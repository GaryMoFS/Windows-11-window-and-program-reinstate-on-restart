"""
Browser Tabs Module
Detects and retrieves open tabs from browsers
"""

import logging
import subprocess
import json
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Browser process names and their data paths
BROWSERS = {
    'chrome.exe': {
        'name': 'Chrome',
        'debug_port': 9222,
    },
    'msedge.exe': {
        'name': 'Edge',
        'debug_port': 9222,
    },
    'firefox.exe': {
        'name': 'Firefox',
        'debug_port': 9222,
    },
    'brave.exe': {
        'name': 'Brave',
        'debug_port': 9222,
    },
    'opera.exe': {
        'name': 'Opera',
        'debug_port': 9222,
    },
}


def is_browser_running(executable: str) -> bool:
    """Check if a browser is running"""
    import psutil
    exe_name = executable.split('\\')[-1].lower()
    return exe_name in BROWSERS


def get_browser_tabs(window_title: str, executable: str) -> List[Dict[str, str]]:
    """
    Get tabs from a browser window
    
    Args:
        window_title: Title of the browser window
        executable: Path to browser executable
    
    Returns:
        List of dicts with 'url' and 'title' keys
    """
    exe_name = executable.split('\\')[-1].lower()
    
    if exe_name not in BROWSERS:
        return []
    
    browser_info = BROWSERS[exe_name]
    browser_name = browser_info['name']
    debug_port = browser_info['debug_port']
    
    logger.debug(f"Getting tabs from {browser_name}")
    
    try:
        if browser_name in ['Chrome', 'Edge', 'Brave', 'Opera']:
            return get_chrome_tabs(debug_port)
        elif browser_name == 'Firefox':
            return get_firefox_tabs(debug_port)
    except Exception as e:
        logger.debug(f"Error getting tabs from {browser_name}: {e}")
    
    return []


def get_chrome_tabs(port: int = 9222) -> List[Dict[str, str]]:
    """Get tabs from Chrome/Chromium-based browsers via CDP"""
    tabs = []
    
    try:
        # Try to connect to Chrome DevTools Protocol
        import websocket
        
        # First, get the list of targets
        ws_url = f"ws://localhost:{port}/json"
        
        # This may fail if browser wasn't launched with debug port
        # We'll try to launch a temporary connection to check
        ws = websocket.WebSocket()
        ws.settimeout(1)
        
        try:
            ws.connect(ws_url)
            response = ws.recv()
            ws.close()
            
            targets = json.loads(response)
            
            for target in targets:
                if target.get('type') == 'page':
                    tabs.append({
                        'url': target.get('url', ''),
                        'title': target.get('title', '')
                    })
                    
        except (websocket.WebSocketTimeoutException, 
                websocket.WebSocketBadStatusException,
                ConnectionRefusedError) as e:
            # Browser not running with debug port
            logger.debug(f"Chrome not running with debug port {port}: {e}")
            pass
            
    except ImportError:
        logger.warning("websocket-client not installed, cannot get browser tabs")
    except Exception as e:
        logger.debug(f"Error connecting to Chrome: {e}")
    
    return tabs


def get_firefox_tabs(port: int = 9222) -> List[Dict[str, str]]:
    """Get tabs from Firefox via remote debugging"""
    tabs = []
    
    try:
        import websocket
        
        ws_url = f"ws://localhost:{port}/json"
        
        ws = websocket.WebSocket()
        ws.settimeout(1)
        
        try:
            ws.connect(ws_url)
            response = ws.recv()
            ws.close()
            
            targets = json.loads(response)
            
            for target in targets:
                if target.get('type') == 'page':
                    tabs.append({
                        'url': target.get('url', ''),
                        'title': target.get('title', '')
                    })
                    
        except (websocket.WebSocketTimeoutException,
                websocket.WebSocketBadStatusException,
                ConnectionRefusedError):
            logger.debug(f"Firefox not running with debug port {port}")
            pass
            
    except ImportError:
        logger.warning("websocket-client not installed, cannot get browser tabs")
    except Exception as e:
        logger.debug(f"Error connecting to Firefox: {e}")
    
    return tabs


def launch_browser_with_debug(executable: str, port: int = 9222) -> bool:
    """
    Launch a browser with remote debugging enabled
    
    Note: This will open a new browser window. Most users won't want this.
    """
    try:
        cmd = [executable, f"--remote-debugging-port={port}"]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)  # Give browser time to start
        return True
    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")
        return False
