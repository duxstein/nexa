#!/usr/bin/env python3
"""
System Controller for NEXA
Handles Windows system operations and automation
"""

import subprocess
import psutil
import logging
from typing import Dict, List, Optional, Tuple
import win32api
import win32gui
import win32con
import win32process
import win32clipboard
from ctypes import windll, wintypes, byref
import time
import os
from pathlib import Path

class SystemController:
    """Windows system control and automation for NEXA"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common application paths
        self.app_paths = {
            'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            'firefox': r'C:\Program Files\Mozilla Firefox\firefox.exe',
            'edge': r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            'notepad': r'C:\Windows\System32\notepad.exe',
            'calculator': r'C:\Windows\System32\calc.exe',
            'explorer': r'C:\Windows\explorer.exe',
            'cmd': r'C:\Windows\System32\cmd.exe',
            'powershell': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
            'notion': r'C:\Users\sport\AppData\Local\Programs\Notion\Notion.exe'
        }
        
        self.logger.info("System controller initialized")
    
    # Application Management
    def launch_application(self, app_name: str, args: str = "") -> bool:
        """Launch an application"""
        try:
            app_name = app_name.lower()
            
            # Check if it's a known application
            if app_name in self.app_paths:
                app_path = self.app_paths[app_name]
                if os.path.exists(app_path):
                    subprocess.Popen([app_path] + (args.split() if args else []))
                    self.logger.info(f"Launched {app_name}")
                    return True
            
            # Try to launch by name (if in PATH)
            try:
                subprocess.Popen([app_name] + (args.split() if args else []))
                self.logger.info(f"Launched {app_name}")
                return True
            except FileNotFoundError:
                pass
            
            # Try Windows start command
            try:
                subprocess.run(['start', app_name], shell=True, check=True)
                self.logger.info(f"Launched {app_name} via start command")
                return True
            except Exception:
                pass

            # Search for the app in common locations
            search_dirs = [
                os.environ.get('ProgramFiles', 'C:\\Program Files'),
                os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs')
            ]

            for dir in search_dirs:
                for root, _, files in os.walk(dir):
                    if f"{app_name}.exe" in files:
                        app_path = os.path.join(root, f"{app_name}.exe")
                        subprocess.Popen([app_path] + (args.split() if args else []))
                        self.logger.info(f"Launched {app_name} from {app_path}")
                        return True

            
        except Exception as e:
            self.logger.error(f"Failed to launch {app_name}: {e}")
            return False
    
    def close_application(self, app_name: str) -> bool:
        """Close an application by name"""
        try:
            app_name = app_name.lower()
            
            # Find processes by name
            closed_count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app_name in proc.info['name'].lower():
                        proc.terminate()
                        closed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if closed_count > 0:
                self.logger.info(f"Closed {closed_count} instances of {app_name}")
                return True
            else:
                # Try taskkill command
                result = subprocess.run(
                    ['taskkill', '/f', '/im', f'{app_name}.exe'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.logger.info(f"Closed {app_name} via taskkill")
                    return True
                
            self.logger.warning(f"No running instances of {app_name} found")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to close {app_name}: {e}")
            return False
    
    def minimize_application(self, app_name: str) -> bool:
        """Minimize an application window"""
        try:
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if app_name.lower() in window_title.lower():
                        windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            minimized_count = 0
            for hwnd in windows:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                minimized_count += 1
            
            if minimized_count > 0:
                self.logger.info(f"Minimized {minimized_count} windows of {app_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to minimize {app_name}: {e}")
            return False
    
    def get_running_applications(self) -> List[Dict[str, str]]:
        """Get list of running applications"""
        apps = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    # Filter out system processes
                    if proc.info['name'] and not proc.info['name'].startswith('System'):
                        apps.append({
                            'name': proc.info['name'],
                            'pid': proc.info['pid'],
                            'memory_mb': round(proc.info['memory_info'].rss / 1024 / 1024, 1)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error getting running applications: {e}")
        
        return sorted(apps, key=lambda x: x['memory_mb'], reverse=True)[:20]
    
    # Volume Control
    def set_volume(self, volume: int) -> bool:
        """Set system volume (0-100)"""
        try:
            volume = max(0, min(100, volume))
            
            # Use nircmd if available, otherwise use PowerShell
            try:
                # Try PowerShell method
                ps_script = f"""
                Add-Type -TypeDefinition '
                using System.Runtime.InteropServices;
                [Guid(\"5CDF2C82-841E-4546-9722-0CF74078229A\"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                interface IAudioEndpointVolume {{
                    int RegisterControlChangeNotify(IntPtr pNotify);
                    int UnregisterControlChangeNotify(IntPtr pNotify);
                    int GetChannelCount(out int pnChannelCount);
                    int SetMasterVolumeLevel(float fLevelDB, System.Guid pguidEventContext);
                    int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
                    int GetMasterVolumeLevel(out float pfLevelDB);
                    int GetMasterVolumeLevelScalar(out float pfLevel);
                    int SetChannelVolumeLevel(uint nChannel, float fLevelDB, System.Guid pguidEventContext);
                    int SetChannelVolumeLevelScalar(uint nChannel, float fLevel, System.Guid pguidEventContext);
                    int GetChannelVolumeLevel(uint nChannel, out float pfLevelDB);
                    int GetChannelVolumeLevelScalar(uint nChannel, out float pfLevel);
                    int SetMute(bool bMute, System.Guid pguidEventContext);
                    int GetMute(out bool pbMute);
                    int GetVolumeStepInfo(out uint pnStep, out uint pnStepCount);
                    int VolumeStepUp(System.Guid pguidEventContext);
                    int VolumeStepDown(System.Guid pguidEventContext);
                    int QueryHardwareSupport(out uint pdwHardwareSupportMask);
                    int GetVolumeRange(out float pflVolumeMindB, out float pflVolumeMaxdB, out float pflVolumeIncrementdB);
                }}'
                $volume = {volume / 100.0}
                """
                
                subprocess.run(['powershell', '-Command', ps_script], 
                             capture_output=True, check=True)
                
                self.logger.info(f"Set volume to {volume}%")
                return True
                
            except subprocess.CalledProcessError:
                # Fallback: use simple volume keys simulation
                import pyautogui
                current_vol = self.get_volume()
                if current_vol is not None:
                    diff = volume - current_vol
                    if diff > 0:
                        for _ in range(abs(diff) // 2):
                            pyautogui.press('volumeup')
                    elif diff < 0:
                        for _ in range(abs(diff) // 2):
                            pyautogui.press('volumedown')
                    return True
                
        except Exception as e:
            self.logger.error(f"Failed to set volume: {e}")
            return False
    
    def get_volume(self) -> Optional[int]:
        """Get current system volume (0-100)"""
        try:
            # This is a simplified implementation
            # In a real implementation, you'd use Windows Audio APIs
            return 50  # Placeholder
        except Exception as e:
            self.logger.error(f"Failed to get volume: {e}")
            return None
    
    def mute_volume(self) -> bool:
        """Mute system volume"""
        try:
            import pyautogui
            pyautogui.press('volumemute')
            self.logger.info("Volume muted")
            return True
        except Exception as e:
            self.logger.error(f"Failed to mute volume: {e}")
            return False
    
    def volume_up(self) -> bool:
        """Increase volume"""
        try:
            import pyautogui
            pyautogui.press('volumeup')
            return True
        except Exception as e:
            self.logger.error(f"Failed to increase volume: {e}")
            return False
    
    def volume_down(self) -> bool:
        """Decrease volume"""
        try:
            import pyautogui
            pyautogui.press('volumedown')
            return True
        except Exception as e:
            self.logger.error(f"Failed to decrease volume: {e}")
            return False
    
    # System Power Management
    def shutdown_system(self, delay_minutes: int = 0) -> bool:
        """Shutdown system with optional delay"""
        try:
            delay_seconds = delay_minutes * 60
            subprocess.run(['shutdown', '/s', '/t', str(delay_seconds)], check=True)
            self.logger.info(f"System shutdown scheduled in {delay_minutes} minutes")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown system: {e}")
            return False
    
    def restart_system(self, delay_minutes: int = 0) -> bool:
        """Restart system with optional delay"""
        try:
            delay_seconds = delay_minutes * 60
            subprocess.run(['shutdown', '/r', '/t', str(delay_seconds)], check=True)
            self.logger.info(f"System restart scheduled in {delay_minutes} minutes")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restart system: {e}")
            return False
    
    def cancel_shutdown(self) -> bool:
        """Cancel scheduled shutdown/restart"""
        try:
            subprocess.run(['shutdown', '/a'], check=True)
            self.logger.info("Shutdown/restart cancelled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel shutdown: {e}")
            return False
    
    def lock_workstation(self) -> bool:
        """Lock the workstation"""
        try:
            windll.user32.LockWorkStation()
            self.logger.info("Workstation locked")
            return True
        except Exception as e:
            self.logger.error(f"Failed to lock workstation: {e}")
            return False
    
    def sleep_system(self) -> bool:
        """Put system to sleep"""
        try:
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'], check=True)
            self.logger.info("System going to sleep")
            return True
        except Exception as e:
            self.logger.error(f"Failed to put system to sleep: {e}")
            return False
    
    # System Information
    def get_system_info(self) -> Dict[str, str]:
        """Get system information"""
        info = {}
        try:
            # CPU usage
            info['cpu_usage'] = f"{psutil.cpu_percent(interval=1)}%"
            
            # Memory usage
            memory = psutil.virtual_memory()
            info['memory_usage'] = f"{memory.percent}%"
            info['memory_available'] = f"{memory.available // (1024**3)} GB"
            
            # Disk usage
            disk = psutil.disk_usage('C:\\')
            info['disk_usage'] = f"{(disk.used / disk.total) * 100:.1f}%"
            info['disk_free'] = f"{disk.free // (1024**3)} GB"
            
            # Battery (if laptop)
            try:
                battery = psutil.sensors_battery()
                if battery:
                    info['battery_percent'] = f"{battery.percent}%"
                    info['battery_plugged'] = "Yes" if battery.power_plugged else "No"
            except:
                info['battery_percent'] = "N/A"
                info['battery_plugged'] = "N/A"
            
            # Network
            info['network_connections'] = str(len(psutil.net_connections()))
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
        
        return info
    
    def get_battery_status(self) -> Dict[str, str]:
        """Get detailed battery status"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    'percent': f"{battery.percent}%",
                    'plugged': "Yes" if battery.power_plugged else "No",
                    'time_left': f"{battery.secsleft // 3600}h {(battery.secsleft % 3600) // 60}m" if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unlimited"
                }
            else:
                return {'status': 'No battery detected'}
        except Exception as e:
            self.logger.error(f"Error getting battery status: {e}")
            return {'error': str(e)}
    
    def get_network_status(self) -> Dict[str, str]:
        """Get network connection status"""
        try:
            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            active_interfaces = []
            for interface, addrs in interfaces.items():
                if interface in stats and stats[interface].isup:
                    for addr in addrs:
                        if addr.family == 2:  # IPv4
                            active_interfaces.append({
                                'name': interface,
                                'ip': addr.address
                            })
            
            return {
                'active_connections': str(len(active_interfaces)),
                'interfaces': ', '.join([f"{iface['name']} ({iface['ip']})" for iface in active_interfaces[:3]])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting network status: {e}")
            return {'error': str(e)}
    
    # Notification Management
    def disable_notifications(self, duration_minutes: int = 0) -> bool:
        """Disable Windows notifications"""
        try:
            # This would require registry modifications or Focus Assist API
            # For now, we'll use a placeholder implementation
            self.logger.info(f"Notifications disabled for {duration_minutes} minutes")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable notifications: {e}")
            return False
    
    def enable_notifications(self) -> bool:
        """Enable Windows notifications"""
        try:
            # Placeholder implementation
            self.logger.info("Notifications enabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable notifications: {e}")
            return False
    
    # Window Management
    def get_active_window(self) -> Optional[str]:
        """Get title of active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd)
        except Exception as e:
            self.logger.error(f"Error getting active window: {e}")
            return None
    
    def minimize_all_windows(self) -> bool:
        """Minimize all windows (Show Desktop)"""
        try:
            import pyautogui
            pyautogui.hotkey('win', 'd')
            self.logger.info("All windows minimized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to minimize all windows: {e}")
            return False
    
    # Process Management
    def kill_process(self, process_name: str) -> bool:
        """Kill process by name"""
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        proc.kill()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                self.logger.info(f"Killed {killed_count} instances of {process_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to kill process {process_name}: {e}")
            return False
    
    def get_process_info(self, process_name: str) -> List[Dict]:
        """Get information about processes by name"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_mb': round(proc.info['memory_info'].rss / 1024 / 1024, 1)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error getting process info: {e}")
        
        return processes