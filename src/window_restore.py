"""
Window Restore Module
Restores windows to saved positions
"""

import logging
import subprocess
import time
import win32gui
import win32con
import win32api
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)
RESTORE_BROWSER_TABS = False
RESTORE_SESSION_MANAGED_APPS = True

SESSION_MANAGED_APPS = {
    'chrome.exe',
    'msedge.exe',
    'firefox.exe',
    'brave.exe',
    'opera.exe',
}


def launch_program(executable: str, arguments: str = "") -> Optional[int]:
    """
    Launch a program and return its process ID
    
    Args:
        executable: Path to executable
        arguments: Optional command line arguments
    
    Returns:
        Process ID or None
    """
    try:
        cmd = f'"{executable}"'
        if arguments:
            cmd += f" {arguments}"
        
        # Start the process
        process = subprocess.Popen(cmd, shell=True)
        logger.info(f"Launched: {executable}")
        
        # Wait a bit for the window to appear
        time.sleep(2)
        
        return process.pid
        
    except Exception as e:
        logger.error(f"Failed to launch {executable}: {e}")
        return None


def find_window_by_executable(executable: str, title: str = "") -> Optional[int]:
    """
    Find a window handle by executable path and optionally title
    
    Args:
        executable: Path to executable
        title: Optional window title to match
    
    Returns:
        Window handle or None
    """
    target_exe = executable.split('\\')[-1].lower()
    
    def callback(hwnd, windows):
        try:
            # Check if window is visible
            if not win32gui.IsWindowVisible(hwnd):
                return True
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            if not window_title:
                return True
            
            # Get process info
            import win32process
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                import psutil
                process = psutil.Process(pid)
                proc_name = process.name().lower()
                
                if proc_name == target_exe:
                    # If title specified, match it
                    if title and title.lower() not in window_title.lower():
                        return True
                    windows.append(hwnd)
            except:
                pass
                
        except:
            pass
        
        return True
    
    windows = []
    try:
        win32gui.EnumWindows(callback, windows)
    except Exception as e:
        logger.debug(f"Error enumerating windows: {e}")
    
    # Return the first matching window
    return windows[0] if windows else None


def find_windows_by_executable(executable: str) -> List[int]:
    """Find visible windows by executable name."""
    target_exe = executable.split('\\')[-1].lower()
    matches = []

    def callback(hwnd, windows):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            window_title = win32gui.GetWindowText(hwnd)
            if not window_title:
                return True
            import win32process
            import psutil
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc_name = psutil.Process(pid).name().lower()
            if proc_name == target_exe:
                windows.append(hwnd)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(callback, matches)
    except Exception:
        pass
    return matches


def find_window_by_executable_exact_title(executable: str, title: str) -> Optional[int]:
    """Find a window for executable using exact title match (case-insensitive)."""
    if not title:
        return None
    target_exe = executable.split('\\')[-1].lower()
    target_title = title.strip().lower()
    matches = []

    def callback(hwnd, windows):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            window_title = win32gui.GetWindowText(hwnd)
            if not window_title:
                return True
            import win32process
            import psutil
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc_name = psutil.Process(pid).name().lower()
            if proc_name == target_exe and window_title.strip().lower() == target_title:
                windows.append(hwnd)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(callback, matches)
    except Exception:
        pass
    return matches[0] if matches else None


def _choose_best_window(hwnds: List[int], desired_title: str = "") -> Optional[int]:
    """Choose the best window handle from candidates."""
    if not hwnds:
        return None
    if desired_title:
        desired = desired_title.lower()
        for hwnd in hwnds:
            try:
                if desired in win32gui.GetWindowText(hwnd).lower():
                    return hwnd
            except Exception:
                pass
    # fallback: largest area window is most likely the primary UI window
    def area(hwnd):
        try:
            l, t, r, b = win32gui.GetWindowRect(hwnd)
            return max(0, (r - l) * (b - t))
        except Exception:
            return 0
    return sorted(hwnds, key=area, reverse=True)[0]


def position_window(hwnd: int, x: int, y: int, width: int, height: int, state: str, monitor: int, activate: bool = False):
    """
    Position and size a window
    
    Args:
        hwnd: Window handle
        x, y: Position
        width, height: Size
        state: Window state (normal, maximized, minimized)
        monitor: Monitor index
    """
    try:
        # Keep restored windows within visible monitor work areas.
        monitors = win32api.EnumDisplayMonitors()
        work_areas = []
        for hmonitor, _, _ in monitors:
            try:
                work_areas.append(win32api.GetMonitorInfo(hmonitor).get('Work'))
            except Exception:
                pass

        if work_areas:
            # Normalize invalid sizes first.
            width = max(320, int(width))
            height = max(220, int(height))

            # Check if target rect intersects any work area.
            rect = (x, y, x + width, y + height)

            def intersects(a, b):
                return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])

            if not any(intersects(rect, wa) for wa in work_areas):
                # Fallback to target monitor if available, else primary monitor.
                target_idx = monitor if 0 <= monitor < len(monitors) else 0
                wa = win32api.GetMonitorInfo(monitors[target_idx][0]).get('Work', work_areas[0])
                wx1, wy1, wx2, wy2 = wa
                max_w = max(320, (wx2 - wx1))
                max_h = max(220, (wy2 - wy1))
                width = min(width, max_w)
                height = min(height, max_h)
                x = wx1 + max(0, ((wx2 - wx1) - width) // 2)
                y = wy1 + max(0, ((wy2 - wy1) - height) // 2)
        
        # Restore window first if minimized
        if state == "minimized":
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.5)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        # Set window position and size
        # SWP_NOACTIVATE = 0x0010, SWP_NOZORDER = 0x0004
        flags = win32con.SWP_NOZORDER
        if not activate:
            flags |= win32con.SWP_NOACTIVATE

        win32gui.SetWindowPos(
            hwnd, 
            0, 
            x, y, 
            width, height,
            flags
        )
        
        # Apply state
        if state == "maximized":
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        elif state == "minimized":
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        elif activate:
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass
        
        logger.debug(f"Positioned window: {x}, {y}, {width}x{height}, {state}")
        
    except Exception as e:
        logger.error(f"Error positioning window: {e}")


def apply_snap_layout(hwnd: int, snap_type: str) -> bool:
    """Apply a captured snap layout using monitor work-area geometry."""
    if not snap_type:
        return False
    try:
        monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        wx1, wy1, wx2, wy2 = win32api.GetMonitorInfo(monitor)['Work']
        work_w = wx2 - wx1
        work_h = wy2 - wy1
        half_w = max(1, work_w // 2)
        half_h = max(1, work_h // 2)

        layouts = {
            'left': (wx1, wy1, half_w, work_h),
            'right': (wx1 + half_w, wy1, work_w - half_w, work_h),
            'top': (wx1, wy1, work_w, half_h),
            'bottom': (wx1, wy1 + half_h, work_w, work_h - half_h),
            'top_left': (wx1, wy1, half_w, half_h),
            'top_right': (wx1 + half_w, wy1, work_w - half_w, half_h),
            'bottom_left': (wx1, wy1 + half_h, half_w, work_h - half_h),
            'bottom_right': (wx1 + half_w, wy1 + half_h, work_w - half_w, work_h - half_h),
        }
        rect = layouts.get(snap_type)
        if not rect:
            return False
        x, y, w, h = rect
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(
            hwnd,
            0,
            x, y,
            w, h,
            win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER
        )
        return True
    except Exception as e:
        logger.debug(f"Snap restore failed for '{snap_type}': {e}")
        return False


def restore_tabs(browser_executable: str, tabs: List[Dict[str, str]]):
    """
    Restore browser tabs
    
    Args:
        browser_executable: Path to browser
        tabs: List of dicts with 'url' and 'title'
    """
    if not tabs:
        return
    
    try:
        # Find the browser window
        hwnd = find_window_by_executable(browser_executable)
        if not hwnd:
            logger.warning("Browser window not found for tabs")
            return
        
        # Activate the browser
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        # For Chrome/Edge, we can use keyboard shortcuts to open tabs
        # Ctrl+Shift+T reopens last closed tab
        # We need to open new tabs with Ctrl+T and navigate to URLs
        
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        
        for i, tab in enumerate(tabs):
            if i == 0:
                # First tab - navigate to URL using address bar
                # Focus address bar: Ctrl+L
                shell.SendKeys("^l")
                time.sleep(0.3)
                # Type URL and Enter
                shell.SendKeys(tab.get('url', ''))
                shell.SendKeys("{ENTER}")
            else:
                # New tab: Ctrl+T
                shell.SendKeys("^t")
                time.sleep(0.5)
                # Type URL and Enter
                shell.SendKeys(tab.get('url', ''))
                shell.SendKeys("{ENTER}")
            
            time.sleep(0.5)
        
        logger.info(f"Restored {len(tabs)} tabs")
        
    except Exception as e:
        logger.error(f"Error restoring tabs: {e}")


def restore_window(window_info: Dict[str, Any], launched_session_apps: Optional[set] = None) -> bool:
    """
    Restore a single window
    
    Args:
        window_info: Window information dict
    
    Returns:
        True if successful
    """
    executable = window_info.get('executable', '')
    title = window_info.get('title', '')
    x = window_info.get('x', 0)
    y = window_info.get('y', 0)
    width = window_info.get('width', 800)
    height = window_info.get('height', 600)
    state = window_info.get('state', 'normal')
    monitor = window_info.get('monitor', 0)
    tabs = window_info.get('tabs', [])
    snap_type = window_info.get('snap_type')
    exe_name = executable.split('\\')[-1].lower()
    is_session_managed = exe_name in SESSION_MANAGED_APPS

    # Minimized windows in saved presets often create poor UX on restore.
    if state == 'minimized':
        logger.debug("Skipping minimized window restore: %r", title)
        return True
    
    logger.info("Restoring: %r (%s)", title, executable)

    # Conservative policy for session-managed apps (Chrome/Edge/etc.) to avoid
    # "running but unusable from taskbar/Alt+Tab" states.
    if launched_session_apps is None:
        launched_session_apps = set()

    if is_session_managed and not RESTORE_SESSION_MANAGED_APPS:
        logger.info("Skipping session-managed app restore by policy: %r", title)
        return True

    if is_session_managed:
        # Safe mode for session-managed apps: avoid repositioning to prevent
        # non-interactive/stuck window states. Only surface or launch.
        hwnd = find_window_by_executable(executable, title) or _choose_best_window(find_windows_by_executable(executable), title)
        if hwnd:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass
            return True
        if executable in launched_session_apps:
            return True
        pid = launch_program(executable)
        if not pid:
            logger.warning(f"Could not launch session-managed app: {executable}")
            return False
        launched_session_apps.add(executable)
        return True
    
    # Find existing window first (prefer title match, then fallback to best executable match)
    hwnd = find_window_by_executable(executable, title) or _choose_best_window(find_windows_by_executable(executable), title)

    if not hwnd:
        # Launch the program
        pid = launch_program(executable)
        if not pid:
            logger.warning(f"Could not launch: {executable}")
            return False
        
        # Wait and find window
        for _ in range(10):
            time.sleep(1)
            hwnd = find_window_by_executable(executable, title) or _choose_best_window(find_windows_by_executable(executable), title)
            if hwnd:
                break
        
        if not hwnd:
            logger.warning(f"Window not found after launch: {title}")
            return False
    
    # Position the window or restore snap layout
    if not apply_snap_layout(hwnd, snap_type):
        position_window(hwnd, x, y, width, height, state, monitor, activate=False)
    
    # Restore tabs if browser
    if tabs and RESTORE_BROWSER_TABS:
        restore_tabs(executable, tabs)
    
    return True


def restore_windows(windows: List[Dict[str, Any]]) -> bool:
    """
    Restore all windows from a preset
    
    Args:
        windows: List of window information dicts
    
    Returns:
        True if all windows restored
    """
    logger.info(f"Restoring {len(windows)} windows...")
    
    success_count = 0
    launched_session_apps = set()
    
    for window_info in windows:
        try:
            if restore_window(window_info, launched_session_apps=launched_session_apps):
                success_count += 1
        except Exception as e:
            logger.error(f"Error restoring window: {e}")
    
    logger.info(f"Restored {success_count}/{len(windows)} windows")
    
    return success_count > 0
