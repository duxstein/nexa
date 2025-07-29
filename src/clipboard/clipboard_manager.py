#!/usr/bin/env python3
"""
Clipboard Manager for NEXA
Tracks clipboard history and provides search functionality
"""

import threading
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import win32clipboard
import win32con
import json
from pathlib import Path
import hashlib
import re

class ClipboardManager:
    """Manages clipboard history and operations for NEXA"""
    
    def __init__(self, max_history: int = 50, save_file: str = None):
        self.max_history = max_history
        self.history: List[Dict] = []
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.monitor_thread = None
        self.last_clipboard_hash = None
        
        # Save file for persistence
        if save_file:
            self.save_file = Path(save_file)
        else:
            self.save_file = Path.home() / '.nexa' / 'clipboard_history.json'
        
        # Ensure directory exists
        self.save_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history
        self._load_history()
        
        self.logger.info(f"Clipboard manager initialized with max history: {max_history}")
    
    def start_monitoring(self):
        """Start monitoring clipboard changes"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Clipboard monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring clipboard changes"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=1)
            self.logger.info("Clipboard monitoring stopped")
    
    def _monitor_clipboard(self):
        """Monitor clipboard changes in background thread"""
        while self.monitoring:
            try:
                current_content = self._get_clipboard_content()
                if current_content:
                    content_hash = self._hash_content(current_content['content'])
                    
                    # Only add if content has changed
                    if content_hash != self.last_clipboard_hash:
                        self._add_to_history(current_content)
                        self.last_clipboard_hash = content_hash
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                self.logger.error(f"Error monitoring clipboard: {e}")
                time.sleep(1)  # Wait longer on error
    
    def _get_clipboard_content(self) -> Optional[Dict]:
        """Get current clipboard content"""
        try:
            win32clipboard.OpenClipboard()
            
            content = {
                'timestamp': datetime.now().isoformat(),
                'content': '',
                'type': 'text',
                'size': 0,
                'source': 'unknown'
            }
            
            # Try to get text content
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                if text and text.strip():
                    content['content'] = text.strip()
                    content['type'] = 'text'
                    content['size'] = len(text)
                    
                    # Try to determine source application
                    content['source'] = self._guess_source_app(text)
                    
                    return content
            
            # Try to get file list
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                if files:
                    content['content'] = '\n'.join(files)
                    content['type'] = 'files'
                    content['size'] = len(files)
                    content['source'] = 'file_explorer'
                    return content
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting clipboard content: {e}")
            return None
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
    
    def _guess_source_app(self, text: str) -> str:
        """Try to guess the source application based on content patterns"""
        try:
            # URL patterns
            if re.match(r'https?://', text):
                if 'youtube.com' in text or 'youtu.be' in text:
                    return 'youtube'
                elif 'github.com' in text:
                    return 'github'
                elif 'google.com' in text:
                    return 'google'
                else:
                    return 'browser'
            
            # Email pattern
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text.strip()):
                return 'email'
            
            # Code patterns
            if any(keyword in text for keyword in ['def ', 'function ', 'class ', 'import ', '#include']):
                return 'code_editor'
            
            # File path pattern
            if re.match(r'^[A-Za-z]:\\', text) or text.startswith('/'):
                return 'file_explorer'
            
            # Phone number pattern
            if re.match(r'^[\+]?[1-9]?[0-9]{7,15}$', re.sub(r'[\s\-\(\)]', '', text)):
                return 'phone'
            
            # Long text (likely from document)
            if len(text) > 100 and ' ' in text:
                return 'document'
            
            return 'unknown'
            
        except Exception:
            return 'unknown'
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content to detect duplicates"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _add_to_history(self, content: Dict):
        """Add content to history"""
        try:
            # Don't add empty content or very short content
            if not content['content'] or len(content['content'].strip()) < 2:
                return
            
            # Don't add if it's the same as the last entry
            if self.history and self.history[0]['content'] == content['content']:
                return
            
            # Add to beginning of history
            self.history.insert(0, content)
            
            # Trim history to max size
            if len(self.history) > self.max_history:
                self.history = self.history[:self.max_history]
            
            # Save to file
            self._save_history()
            
            self.logger.debug(f"Added to clipboard history: {content['type']} ({content['size']} chars)")
            
        except Exception as e:
            self.logger.error(f"Error adding to history: {e}")
    
    def get_history(self, limit: int = None) -> List[Dict]:
        """Get clipboard history"""
        if limit:
            return self.history[:limit]
        return self.history.copy()
    
    def search_history(self, query: str, limit: int = 10) -> List[Dict]:
        """Search clipboard history"""
        query = query.lower().strip()
        if not query:
            return self.get_history(limit)
        
        results = []
        for item in self.history:
            if query in item['content'].lower():
                results.append(item)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_by_type(self, content_type: str, limit: int = 10) -> List[Dict]:
        """Get clipboard history by type"""
        results = []
        for item in self.history:
            if item['type'] == content_type:
                results.append(item)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_by_source(self, source: str, limit: int = 10) -> List[Dict]:
        """Get clipboard history by source application"""
        results = []
        for item in self.history:
            if item['source'] == source:
                results.append(item)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_recent(self, hours: int = 24, limit: int = 20) -> List[Dict]:
        """Get recent clipboard history within specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        results = []
        
        for item in self.history:
            try:
                item_time = datetime.fromisoformat(item['timestamp'])
                if item_time >= cutoff_time:
                    results.append(item)
                    if len(results) >= limit:
                        break
                else:
                    break  # History is ordered by time, so we can stop here
            except ValueError:
                continue
        
        return results
    
    def copy_to_clipboard(self, content: str) -> bool:
        """Copy content to clipboard"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(content)
            win32clipboard.CloseClipboard()
            
            self.logger.info(f"Copied to clipboard: {len(content)} characters")
            return True
            
        except Exception as e:
            self.logger.error(f"Error copying to clipboard: {e}")
            return False
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
    
    def paste_from_history(self, index: int) -> bool:
        """Paste content from history by index"""
        try:
            if 0 <= index < len(self.history):
                content = self.history[index]['content']
                return self.copy_to_clipboard(content)
            else:
                self.logger.warning(f"Invalid history index: {index}")
                return False
        except Exception as e:
            self.logger.error(f"Error pasting from history: {e}")
            return False
    
    def clear_history(self) -> bool:
        """Clear clipboard history"""
        try:
            self.history.clear()
            self._save_history()
            self.logger.info("Clipboard history cleared")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing history: {e}")
            return False
    
    def remove_from_history(self, index: int) -> bool:
        """Remove specific item from history"""
        try:
            if 0 <= index < len(self.history):
                removed_item = self.history.pop(index)
                self._save_history()
                self.logger.info(f"Removed item from history: {removed_item['type']}")
                return True
            else:
                self.logger.warning(f"Invalid history index: {index}")
                return False
        except Exception as e:
            self.logger.error(f"Error removing from history: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get clipboard usage statistics"""
        try:
            stats = {
                'total_items': len(self.history),
                'types': {},
                'sources': {},
                'today_items': 0,
                'this_week_items': 0,
                'average_size': 0
            }
            
            if not self.history:
                return stats
            
            # Count by type and source
            total_size = 0
            today = datetime.now().date()
            week_ago = datetime.now() - timedelta(days=7)
            
            for item in self.history:
                # Type statistics
                item_type = item['type']
                stats['types'][item_type] = stats['types'].get(item_type, 0) + 1
                
                # Source statistics
                source = item['source']
                stats['sources'][source] = stats['sources'].get(source, 0) + 1
                
                # Size statistics
                total_size += item['size']
                
                # Time statistics
                try:
                    item_time = datetime.fromisoformat(item['timestamp'])
                    if item_time.date() == today:
                        stats['today_items'] += 1
                    if item_time >= week_ago:
                        stats['this_week_items'] += 1
                except ValueError:
                    continue
            
            stats['average_size'] = round(total_size / len(self.history), 1)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {'error': str(e)}
    
    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")
    
    def _load_history(self):
        """Load history from file"""
        try:
            if self.save_file.exists():
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                    
                # Ensure history doesn't exceed max size
                if len(self.history) > self.max_history:
                    self.history = self.history[:self.max_history]
                    self._save_history()
                
                self.logger.info(f"Loaded {len(self.history)} items from clipboard history")
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
            self.history = []
    
    def export_history(self, file_path: str, format_type: str = 'json') -> bool:
        """Export clipboard history to file"""
        try:
            file_path = Path(file_path)
            
            if format_type.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, indent=2, ensure_ascii=False)
            
            elif format_type.lower() == 'txt':
                with open(file_path, 'w', encoding='utf-8') as f:
                    for i, item in enumerate(self.history):
                        f.write(f"=== Item {i+1} ({item['timestamp']}) ===\n")
                        f.write(f"Type: {item['type']}\n")
                        f.write(f"Source: {item['source']}\n")
                        f.write(f"Size: {item['size']} characters\n")
                        f.write(f"Content:\n{item['content']}\n\n")
            
            else:
                self.logger.error(f"Unsupported export format: {format_type}")
                return False
            
            self.logger.info(f"Exported clipboard history to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting history: {e}")
            return False
    
    def cleanup_old_entries(self, days: int = 30) -> int:
        """Remove entries older than specified days"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            original_count = len(self.history)
            
            self.history = [
                item for item in self.history
                if datetime.fromisoformat(item['timestamp']) >= cutoff_time
            ]
            
            removed_count = original_count - len(self.history)
            
            if removed_count > 0:
                self._save_history()
                self.logger.info(f"Cleaned up {removed_count} old clipboard entries")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old entries: {e}")
            return 0