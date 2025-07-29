#!/usr/bin/env python3
"""
File Organizer for NEXA
Auto-organizes Downloads/Desktop into categorized folders
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import mimetypes
from datetime import datetime
import send2trash

class FileOrganizer:
    """File organization system for NEXA AI Butler"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # File type categories
        self.file_categories = {
            'Documents': {
                'extensions': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages', '.tex', '.wpd'],
                'mimetypes': ['application/pdf', 'application/msword', 'text/plain']
            },
            'Spreadsheets': {
                'extensions': ['.xls', '.xlsx', '.csv', '.ods', '.numbers'],
                'mimetypes': ['application/vnd.ms-excel', 'text/csv']
            },
            'Presentations': {
                'extensions': ['.ppt', '.pptx', '.odp', '.key'],
                'mimetypes': ['application/vnd.ms-powerpoint']
            },
            'Images': {
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico', '.raw'],
                'mimetypes': ['image/jpeg', 'image/png', 'image/gif', 'image/bmp']
            },
            'Videos': {
                'extensions': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
                'mimetypes': ['video/mp4', 'video/avi', 'video/quicktime']
            },
            'Audio': {
                'extensions': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
                'mimetypes': ['audio/mpeg', 'audio/wav', 'audio/flac']
            },
            'Archives': {
                'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
                'mimetypes': ['application/zip', 'application/x-rar-compressed']
            },
            'Software': {
                'extensions': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.appx'],
                'mimetypes': ['application/x-msdownload']
            },
            'Code': {
                'extensions': ['.py', '.js', '.html', '.css', '.cpp', '.c', '.java', '.php', '.rb', '.go', '.rs'],
                'mimetypes': ['text/x-python', 'text/javascript', 'text/html']
            },
            'Fonts': {
                'extensions': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
                'mimetypes': ['font/ttf', 'font/otf']
            },
            'eBooks': {
                'extensions': ['.epub', '.mobi', '.azw', '.azw3', '.fb2'],
                'mimetypes': ['application/epub+zip']
            }
        }
        
        # Common directories
        self.user_home = Path.home()
        self.downloads_dir = self.user_home / 'Downloads'
        self.desktop_dir = self.user_home / 'Desktop'
        self.documents_dir = self.user_home / 'Documents'
        
        # Organization base directory
        self.organized_base = self.documents_dir / 'NEXA_Organized'
    
    def organize_downloads(self) -> Dict[str, int]:
        """Organize files in Downloads folder"""
        return self._organize_directory(self.downloads_dir)
    
    def organize_desktop(self) -> Dict[str, int]:
        """Organize files in Desktop folder"""
        return self._organize_directory(self.desktop_dir)
    
    def organize_directory(self, directory_path: str) -> Dict[str, int]:
        """Organize files in specified directory"""
        return self._organize_directory(Path(directory_path))
    
    def _organize_directory(self, source_dir: Path) -> Dict[str, int]:
        """Organize files in a directory"""
        if not source_dir.exists():
            self.logger.error(f"Directory does not exist: {source_dir}")
            return {}
        
        self.logger.info(f"Starting organization of: {source_dir}")
        
        # Create organized directory structure
        self._create_organized_structure()
        
        # Statistics
        stats = {
            'total_files': 0,
            'organized_files': 0,
            'skipped_files': 0,
            'errors': 0
        }
        
        # Get all files in directory (non-recursive for safety)
        files = [f for f in source_dir.iterdir() if f.is_file()]
        stats['total_files'] = len(files)
        
        for file_path in files:
            try:
                if self._should_skip_file(file_path):
                    stats['skipped_files'] += 1
                    continue
                
                category = self._categorize_file(file_path)
                if category:
                    success = self._move_file_to_category(file_path, category)
                    if success:
                        stats['organized_files'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    # Move to 'Other' category
                    success = self._move_file_to_category(file_path, 'Other')
                    if success:
                        stats['organized_files'] += 1
                    else:
                        stats['errors'] += 1
                        
            except Exception as e:
                self.logger.error(f"Error organizing file {file_path}: {e}")
                stats['errors'] += 1
        
        self.logger.info(f"Organization complete. Stats: {stats}")
        return stats
    
    def _create_organized_structure(self):
        """Create organized directory structure"""
        try:
            # Create base organized directory
            self.organized_base.mkdir(exist_ok=True)
            
            # Create category directories
            for category in self.file_categories.keys():
                category_dir = self.organized_base / category
                category_dir.mkdir(exist_ok=True)
            
            # Create 'Other' directory for uncategorized files
            other_dir = self.organized_base / 'Other'
            other_dir.mkdir(exist_ok=True)
            
            self.logger.info(f"Created organized structure at: {self.organized_base}")
            
        except Exception as e:
            self.logger.error(f"Error creating organized structure: {e}")
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during organization"""
        # Skip hidden files
        if file_path.name.startswith('.'):
            return True
        
        # Skip system files
        system_files = ['desktop.ini', 'thumbs.db', '.ds_store']
        if file_path.name.lower() in system_files:
            return True
        
        # Skip very large files (>1GB) for safety
        try:
            if file_path.stat().st_size > 1024 * 1024 * 1024:  # 1GB
                self.logger.warning(f"Skipping large file: {file_path.name}")
                return True
        except:
            pass
        
        # Skip files currently in use
        if self._is_file_in_use(file_path):
            return True
        
        return False
    
    def _is_file_in_use(self, file_path: Path) -> bool:
        """Check if file is currently in use"""
        try:
            # Try to open file in exclusive mode
            with open(file_path, 'r+b') as f:
                pass
            return False
        except (IOError, OSError):
            return True
    
    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file based on extension and mimetype"""
        file_ext = file_path.suffix.lower()
        
        # Try to get mimetype
        mimetype, _ = mimetypes.guess_type(str(file_path))
        
        # Check each category
        for category, criteria in self.file_categories.items():
            # Check extension
            if file_ext in criteria['extensions']:
                return category
            
            # Check mimetype
            if mimetype and mimetype in criteria['mimetypes']:
                return category
        
        return None  # Uncategorized
    
    def _move_file_to_category(self, file_path: Path, category: str) -> bool:
        """Move file to appropriate category directory"""
        try:
            # Determine destination directory
            dest_dir = self.organized_base / category
            dest_dir.mkdir(exist_ok=True)
            
            # Handle filename conflicts
            dest_path = self._get_unique_destination(dest_dir, file_path.name)
            
            # Move file
            shutil.move(str(file_path), str(dest_path))
            
            self.logger.info(f"Moved {file_path.name} to {category}/{dest_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error moving file {file_path}: {e}")
            return False
    
    def _get_unique_destination(self, dest_dir: Path, filename: str) -> Path:
        """Get unique destination path to avoid conflicts"""
        dest_path = dest_dir / filename
        
        if not dest_path.exists():
            return dest_path
        
        # File exists, create unique name
        name_stem = Path(filename).stem
        name_suffix = Path(filename).suffix
        counter = 1
        
        while dest_path.exists():
            new_name = f"{name_stem}_{counter}{name_suffix}"
            dest_path = dest_dir / new_name
            counter += 1
        
        return dest_path
    
    def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move file from source to destination"""
        try:
            source = Path(source_path)
            dest = Path(dest_path)
            
            if not source.exists():
                self.logger.error(f"Source file does not exist: {source}")
                return False
            
            # Create destination directory if needed
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle conflicts
            if dest.exists():
                dest = self._get_unique_destination(dest.parent, dest.name)
            
            shutil.move(str(source), str(dest))
            self.logger.info(f"Moved {source} to {dest}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error moving file: {e}")
            return False
    
    def delete_file(self, file_path: str, use_trash: bool = True) -> bool:
        """Delete file (send to trash by default)"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.error(f"File does not exist: {file_path}")
                return False
            
            if use_trash:
                send2trash.send2trash(str(file_path))
                self.logger.info(f"Sent to trash: {file_path}")
            else:
                file_path.unlink()
                self.logger.info(f"Permanently deleted: {file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting file: {e}")
            return False
    
    def rename_file(self, old_path: str, new_name: str) -> bool:
        """Rename file"""
        try:
            old_path = Path(old_path)
            new_path = old_path.parent / new_name
            
            if not old_path.exists():
                self.logger.error(f"File does not exist: {old_path}")
                return False
            
            if new_path.exists():
                self.logger.error(f"Destination already exists: {new_path}")
                return False
            
            old_path.rename(new_path)
            self.logger.info(f"Renamed {old_path.name} to {new_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error renaming file: {e}")
            return False
    
    def create_folder(self, folder_path: str) -> bool:
        """Create new folder"""
        try:
            folder_path = Path(folder_path)
            folder_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created folder: {folder_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating folder: {e}")
            return False
    
    def zip_files(self, file_paths: List[str], zip_path: str) -> bool:
        """Create zip archive from files"""
        try:
            import zipfile
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:
                    file_path = Path(file_path)
                    if file_path.exists():
                        zipf.write(file_path, file_path.name)
            
            self.logger.info(f"Created zip archive: {zip_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating zip: {e}")
            return False
    
    def get_organization_stats(self) -> Dict[str, int]:
        """Get statistics about organized files"""
        stats = {}
        
        if not self.organized_base.exists():
            return stats
        
        try:
            for category_dir in self.organized_base.iterdir():
                if category_dir.is_dir():
                    file_count = len([f for f in category_dir.iterdir() if f.is_file()])
                    stats[category_dir.name] = file_count
        except Exception as e:
            self.logger.error(f"Error getting organization stats: {e}")
        
        return stats
    
    def clean_empty_folders(self, directory: str) -> int:
        """Remove empty folders in directory"""
        removed_count = 0
        directory = Path(directory)
        
        try:
            for folder in directory.rglob('*'):
                if folder.is_dir() and not any(folder.iterdir()):
                    folder.rmdir()
                    removed_count += 1
                    self.logger.info(f"Removed empty folder: {folder}")
        except Exception as e:
            self.logger.error(f"Error cleaning empty folders: {e}")
        
        return removed_count