"""
Window Capture Module
Enumerates all visible windows and captures their state
"""

import logging
import win32gui
import win32con
import win32process
import win32api
import psutil
from typing import List, Dict, Any, Optional
import time
from pathlib import Path

from browser_tabs import get_browser_tabs

logger = logging.getLogger(__name__)

# Windows to exclude from capture
EXCLUDED_TITLES = [
    'Program Manager',
    'Windows Input Experience',
    'Microsoft Text Input Application',
    'Windows Defender',
    'Security Health',
]

# Process names to exclude
EXCLUDED_PROCESSES = [
    'explorer.exe',
    'systemsettings.exe',
    'searchhost.exe',
    'startmenuexperiencehost.exe',
    'textinputhost.exe',
    'applicationframehost.exe',
]

EXCLUDED_TITLE_PARTS = [
    'Save Window Layout',
    'Window Restore - Manage Presets',
]

THIS_PROJECT_ROOT = Path(__file__).resolve().parent


def get_process_name(hwnd: int) -> Optional[str]:
    """Get process name from window handle"""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name().lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def get_process_path(hwnd: int) -> Optional[str]:
    """Get full executable path from window handle"""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def get_window_title(hwnd: int) -> str:
    """Get window title"""
    try:
        return win32gui.GetWindowText(hwnd)
    except:
        return ""


def is_visible_window(hwnd: int) -> bool:
    """Check if window is visible and should be captured"""
    try:
        if not win32gui.IsWindowVisible(hwnd):
            return False
        
        title = get_window_title(hwnd)
        if not title:
            return False
        
        # Check excluded titles
        for excluded in EXCLUDED_TITLES:
            if excluded.lower() in title.lower():
                return False
        
        # Check excluded processes
        proc_name = get_process_name(hwnd)
        if proc_name and proc_name in EXCLUDED_PROCESSES:
            return False
        
        # Check window style - exclude tool windows, etc.
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if exstyle & win32con.WS_EX_TOOLWINDOW:
            return False
        
        # Must have a title bar
        if not (style & win32con.WS_CAPTION):
            return False
            
        return True
    except:
        return False


def get_window_rect(hwnd: int) -> Optional[tuple]:
    """Get window rectangle (left, top, right, bottom)"""
    try:
        rect = win32gui.GetWindowRect(hwnd)
        return rect
    except:
        return None


def get_window_state(hwnd: int) -> str:
    """Get window state: normal, maximized, minimized"""
    try:
        placement = win32gui.GetWindowPlacement(hwnd)
        show_cmd = placement[1]
        
        if show_cmd == win32con.SW_SHOWMAXIMIZED:
            return "maximized"
        elif show_cmd == win32con.SW_SHOWMINIMIZED:
            return "minimized"
        else:
            return "normal"
    except:
        return "normal"


def get_monitor_info(hwnd: int) -> int:
    """Get monitor index for window"""
    try:
        rect = win32gui.GetWindowRect(hwnd)
        # Center point of window
        cx = (rect[0] + rect[2]) // 2
        cy = (rect[1] + rect[3]) // 2
        
        # Use win32api to enumerate monitors
        monitors = win32api.EnumDisplayMonitors()
        
        # Find which monitor contains the center point
        for i, (hMonitor, hdc, lprc) in enumerate(monitors):
            info = win32api.GetMonitorInfo(hMonitor)
            rect_data = info['Monitor']
            if rect_data[0] <= cx <= rect_data[2] and rect_data[1] <= cy <= rect_data[3]:
                return i
        
        return 0
    except:
        return 0


def detect_snap_type(hwnd: int, rect: tuple, state: str) -> Optional[str]:
    """Detect common Windows snap zones for a window."""
    if state != 'normal':
        return None
    try:
        monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        work = win32api.GetMonitorInfo(monitor)['Work']
        wx1, wy1, wx2, wy2 = work
        mx1, my1, mx2, my2 = rect
        work_w = wx2 - wx1
        work_h = wy2 - wy1
        win_w = mx2 - mx1
        win_h = my2 - my1
        tol = 24

        left = abs(mx1 - wx1) <= tol
        right = abs(mx2 - wx2) <= tol
        top = abs(my1 - wy1) <= tol
        bottom = abs(my2 - wy2) <= tol
        half_w = abs(win_w - (work_w // 2)) <= tol
        half_h = abs(win_h - (work_h // 2)) <= tol
        full_h = abs(win_h - work_h) <= tol
        full_w = abs(win_w - work_w) <= tol

        if left and full_h and half_w:
            return 'left'
        if right and full_h and half_w:
            return 'right'
        if top and full_w and half_h:
            return 'top'
        if bottom and full_w and half_h:
            return 'bottom'
        if left and top and half_w and half_h:
            return 'top_left'
        if right and top and half_w and half_h:
            return 'top_right'
        if left and bottom and half_w and half_h:
            return 'bottom_left'
        if right and bottom and half_w and half_h:
            return 'bottom_right'
    except Exception:
        return None
    return None


def _is_own_utility_window(executable: str, title: str) -> bool:
    """Exclude this utility's own dialogs from capture."""
    exe_name = executable.split('\\')[-1].lower()
    if exe_name in ('python.exe', 'pythonw.exe'):
        for t in EXCLUDED_TITLE_PARTS:
            if t.lower() in title.lower():
                return True
    return False


def get_window_info(hwnd: int, include_tabs: bool = True, include_minimized: bool = False) -> Optional[Dict[str, Any]]:
    """Get detailed information about a single window"""
    if not is_visible_window(hwnd):
        return None
    
    try:
        rect = get_window_rect(hwnd)
        if not rect:
            return None
        
        executable = get_process_path(hwnd)
        if not executable:
            return None
        
        title = get_window_title(hwnd)
        state = get_window_state(hwnd)
        if state == "minimized" and not include_minimized:
            return None
        monitor = get_monitor_info(hwnd)
        snap_type = detect_snap_type(hwnd, rect, state)

        if _is_own_utility_window(executable, title):
            return None
        
        window_info = {
            'executable': executable,
            'title': title,
            'x': rect[0],
            'y': rect[1],
            'width': rect[2] - rect[0],
            'height': rect[3] - rect[1],
            'state': state,
            'monitor': monitor,
        }
        if snap_type:
            window_info['snap_type'] = snap_type
        
        # Try to get browser tabs if it's a browser
        if include_tabs:
            tabs = get_browser_tabs(title, executable)
            if tabs:
                window_info['tabs'] = tabs
        
        return window_info
        
    except Exception as e:
        logger.debug(f"Error getting window info: {e}")
        return None


def capture_windows(include_tabs: bool = True, include_minimized: bool = False) -> List[Dict[str, Any]]:
    """
    Capture all visible windows and their current state
    
    Args:
        include_tabs: Whether to capture browser tabs
    
    Returns:
        List of window information dictionaries
    """
    logger.info("Capturing current window states...")
    windows = []
    
    try:
        def callback(hwnd, _):
            info = get_window_info(hwnd, include_tabs=include_tabs, include_minimized=include_minimized)
            if info:
                windows.append(info)
            return True

        win32gui.EnumWindows(callback, None)
        logger.info(f"Captured {len(windows)} windows")
        
        # Log the captured windows for debugging
        for w in windows:
            logger.debug(f"  {w.get('title', 'Unknown')}: {w.get('executable', '')}")
        
    except Exception as e:
        logger.error(f"Error capturing windows: {e}")
    
    return windows


def get_running_programs() -> List[str]:
    """Get list of running program executable paths"""
    programs = set()
    
    def callback(hwnd, windows):
        try:
            if is_visible_window(hwnd):
                path = get_process_path(hwnd)
                if path:
                    programs.add(path)
        except:
            pass
    
    try:
        win32gui.EnumWindows(callback, None)
    except:
        pass
    
    return list(programs)
