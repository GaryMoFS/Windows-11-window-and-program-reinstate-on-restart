"""
System Tray Application Module
Provides system tray icon and menu for Window Restore
"""

import logging
import os
import sys
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image
    PYTRAY_AVAILABLE = True
except ImportError:
    PYTRAY_AVAILABLE = False
    logger.warning("pystray not available, system tray will not work")


class TrayApp:
    """System tray application for Window Restore"""
    
    def __init__(self):
        self.icon = None
        self.running = False
        
        if not PYTRAY_AVAILABLE:
            logger.error("pystray not available, cannot create system tray")
            return
        
        self._setup_icon()
    
    def _setup_icon(self):
        """Set up the system tray icon and menu"""
        try:
            # Create a simple icon (blue square)
            # In production, you'd load an actual icon file
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color='#0078D4')
            
            # Create menu
            menu = Menu(
                MenuItem('Save Current Layout', self._on_save),
                MenuItem('Save 4-Quadrant Layout...', self._on_save_quadrants),
                Menu.SEPARATOR,
                MenuItem('Restore Layout', self._build_restore_menu()),
                MenuItem('Refresh Presets', self._on_refresh_presets),
                Menu.SEPARATOR,
                MenuItem('Manage Presets...', self._on_manage),
                MenuItem('Settings', self._on_settings),
                Menu.SEPARATOR,
                MenuItem('Register Context Menu', self._on_register_menu),
                MenuItem('Unregister Context Menu', self._on_unregister_menu),
                Menu.SEPARATOR,
                MenuItem('Exit', self._on_exit),
            )
            
            self.icon = Icon('WindowRestore', image, 'Window Restore', menu)
            logger.info("System tray icon created")
            
        except Exception as e:
            logger.error(f"Error setting up tray icon: {e}")

    def _main_runner(self):
        """Return runner executable and main.py path."""
        main_path = Path(__file__).resolve().parent / 'main.py'
        pythonw_path = Path(sys.executable).with_name('pythonw.exe')
        runner = pythonw_path if pythonw_path.exists() else Path(sys.executable)
        return str(runner), str(main_path)

    def _run_main(self, args, wait=False):
        """Run main.py with args in a separate process."""
        runner, main_path = self._main_runner()
        cmd = [runner, main_path] + list(args)
        if wait:
            return subprocess.run(cmd, capture_output=True, text=True)
        return subprocess.Popen(cmd)
    
    def _build_restore_menu(self):
        """Build the restore submenu with available presets"""
        from preset_manager import PresetManager
        
        pm = PresetManager()
        presets = pm.list_presets()
        
        if not presets:
            return MenuItem('No Presets', None, enabled=False)
        
        items = []
        for preset in presets:
            # Create menu item for each preset
            name = preset['name']
            items.append(MenuItem(name, self._on_restore_item))
        
        return Menu(*items)
    
    def _restore_preset(self, name: str):
        """Restore a preset"""
        logger.info(f"Restoring preset: {name}")
        self._run_main(['--restore', name], wait=False)

    def _on_restore_item(self, icon=None, item=None):
        """Restore callback from tray menu item."""
        preset_name = str(getattr(item, 'text', '')).strip()
        if not preset_name:
            logger.error("Tray restore item missing preset name")
            return
        self._restore_preset(preset_name)
    
    def _on_save(self, icon=None, item=None):
        """Handle save menu item"""
        self._run_main(['--save-dialog'], wait=True)
        self._refresh_menu()
    
    def _on_manage(self, icon=None, item=None):
        """Handle manage presets menu item"""
        logger.info("Opening preset manager")
        self._run_main(['--manage'], wait=False)

    def _on_save_quadrants(self, icon=None, item=None):
        """Save only the current visible 4-window quadrant layout."""
        self._run_main(['--save-quadrants-dialog'], wait=True)
        self._refresh_menu()

    def _on_refresh_presets(self, icon=None, item=None):
        """Manual refresh for tray restore submenu."""
        self._refresh_menu()
    
    def _on_settings(self, icon=None, item=None):
        """Handle settings menu item"""
        logger.info("Opening settings")
        # Would open settings dialog
    
    def _on_register_menu(self, icon=None, item=None):
        """Register context menu"""
        from context_menu import register_context_menu
        
        register_context_menu()
    
    def _on_unregister_menu(self, icon=None, item=None):
        """Unregister context menu"""
        from context_menu import unregister_context_menu
        unregister_context_menu()
    
    def _on_exit(self, icon=None, item=None):
        """Handle exit menu item"""
        logger.info("Exiting application")
        self.running = False
        if self.icon:
            self.icon.stop()
    
    def _refresh_menu(self):
        """Refresh the tray menu with current presets"""
        if self.icon:
            self.icon.menu = Menu(
                MenuItem('Save Current Layout', self._on_save),
                MenuItem('Save 4-Quadrant Layout...', self._on_save_quadrants),
                Menu.SEPARATOR,
                MenuItem('Restore Layout', self._build_restore_menu()),
                MenuItem('Refresh Presets', self._on_refresh_presets),
                Menu.SEPARATOR,
                MenuItem('Manage Presets...', self._on_manage),
                MenuItem('Settings', self._on_settings),
                Menu.SEPARATOR,
                MenuItem('Register Context Menu', self._on_register_menu),
                MenuItem('Unregister Context Menu', self._on_unregister_menu),
                Menu.SEPARATOR,
                MenuItem('Exit', self._on_exit),
            )
    
    def run(self):
        """Start the system tray application"""
        if not PYTRAY_AVAILABLE:
            logger.error("Cannot run - pystray not available")
            return
        
        logger.info("Starting system tray...")
        self.running = True
        
        try:
            self.icon.run()
        except Exception as e:
            logger.error(f"Error running tray icon: {e}")
    
    def stop(self):
        """Stop the system tray application"""
        self.running = False
        if self.icon:
            self.icon.stop()
