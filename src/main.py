"""
Window Restore - Main Entry Point
Windows 11 Window and Program Position Preset Manager

Usage:
    python main.py                    - Start application (system tray)
    python main.py --save NAME        - Save current layout as preset NAME
    python main.py --restore NAME    - Restore preset NAME
    python main.py --manage          - Open preset manager
    python main.py --register        - Register context menu
    python main.py --unregister      - Unregister context menu
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
APP_DATA_DIR = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')) / 'WindowRestore'
SETTINGS_FILE = APP_DATA_DIR / 'settings.json'

from preset_manager import PresetManager
from window_capture import capture_windows
from window_restore import restore_windows
from context_menu import register_context_menu, unregister_context_menu
from shortcut_manager import create_shortcut
from tray_app import TrayApp


def setup_logging():
    """Set up logging to file and console"""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    log_file = APP_DATA_DIR / 'window_restore.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def load_settings() -> dict:
    """Load application settings."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        return {}
    try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = f.read().strip()
            return {} if not data else json.loads(data)
    except Exception:
        return {}


def save_settings(settings: dict) -> bool:
    """Persist application settings."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False


def try_refresh_context_menu():
    """Best-effort context menu refresh."""
    try:
        from context_menu import refresh_context_menu
        refresh_context_menu(quiet=True)
    except Exception:
        pass


def handle_save_preset(name: str, include_tabs: bool = False):
    """Save current window layout as a preset"""
    logger = logging.getLogger(__name__)
    logger.info(f"Saving preset: {name}")
    
    # Capture current windows
    windows = capture_windows(include_tabs=include_tabs, include_minimized=False)
    
    if not windows:
        logger.warning("No windows captured")
        return False
    
    # Save to preset
    pm = PresetManager()
    success = pm.save_preset(name, windows)
    
    if success:
        logger.info(f"Preset '{name}' saved successfully with {len(windows)} windows")
    else:
        logger.error(f"Failed to save preset '{name}'")
    
    return success


def handle_save_quadrant_preset(name: str, include_tabs: bool = False):
    """Save a preset intended for 4-window quadrant layouts."""
    logger = logging.getLogger(__name__)
    logger.info(f"Saving quadrant preset: {name}")
    windows = capture_windows(include_tabs=include_tabs, include_minimized=False)
    if not windows:
        logger.warning("No windows captured")
        return False

    def sort_key(w):
        return (w.get('y', 0), w.get('x', 0))

    selected = sorted(windows, key=sort_key)[:4]
    pm = PresetManager()
    success = pm.save_preset(name, selected)
    if success:
        logger.info(f"Quadrant preset '{name}' saved with {len(selected)} windows")
    else:
        logger.error(f"Failed to save quadrant preset '{name}'")
    return success


def handle_save_quadrants_dialog():
    """Prompt for a name, then save a 4-window quadrant preset."""
    import tkinter as tk
    from tkinter import simpledialog

    root = tk.Tk()
    root.withdraw()
    name = simpledialog.askstring("Save 4-Quadrant Layout", "Enter a name for this preset:")
    root.destroy()

    if name and name.strip():
        return handle_save_quadrant_preset(name.strip())
    return False


def handle_restore_preset(name: str):
    """Restore a preset by name"""
    logger = logging.getLogger(__name__)
    logger.info(f"Restoring preset: {name}")
    
    pm = PresetManager()
    preset = pm.load_preset(name)
    
    if not preset:
        logger.error(f"Preset '{name}' not found")
        return False
    
    success = restore_windows(preset['windows'])
    
    if success:
        logger.info(f"Preset '{name}' restored successfully")
    else:
        logger.error(f"Failed to restore preset '{name}'")
    
    return success


def handle_list_presets():
    """List all saved presets"""
    pm = PresetManager()
    presets = pm.list_presets()
    
    if not presets:
        print("No presets found")
        return
    
    print("Saved presets:")
    for p in presets:
        print(f"  - {p['name']} ({p.get('window_count', 0)} windows)")


def handle_save_dialog():
    """Open a dialog to save current layout with a name"""
    import tkinter as tk
    from ui.dialogs import SavePresetDialog

    root = tk.Tk()
    root.withdraw()

    dialog = SavePresetDialog(parent=root, include_tabs=False)
    root.wait_window(dialog.dialog)
    root.destroy()

    if dialog.result:
        return handle_save_preset(
            dialog.result['name'].strip(),
            include_tabs=bool(dialog.result.get('include_tabs', False))
        )
    return False


def handle_settings():
    """Open settings dialog"""
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()
    
    messagebox.showinfo("Settings", "Settings panel coming soon!")
    root.destroy()
    return True


def main():
    """Main entry point"""
    logger = setup_logging()
    
    parser = argparse.ArgumentParser(
        description='Window Restore - Save and restore window layouts'
    )
    parser.add_argument('--save', metavar='NAME', help='Save current layout as preset')
    parser.add_argument('--save-quadrants', metavar='NAME', help='Save visible layout as a 4-window quadrant preset')
    parser.add_argument('--save-dialog', action='store_true', help='Open dialog to save current layout')
    parser.add_argument('--save-quadrants-dialog', action='store_true', help='Open dialog to save a 4-window quadrant preset')
    parser.add_argument('--restore', metavar='NAME', help='Restore preset by name')
    parser.add_argument('--list', action='store_true', help='List all presets')
    parser.add_argument('--manage', action='store_true', help='Open preset manager')
    parser.add_argument('--settings', action='store_true', help='Open settings')
    parser.add_argument('--register', action='store_true', help='Register context menu')
    parser.add_argument('--unregister', action='store_true', help='Unregister context menu')
    parser.add_argument('--shortcut', metavar='NAME', help='Create desktop shortcut for preset')
    parser.add_argument('--no-tray', action='store_true', help='Run without system tray')
    parser.add_argument('--exit', action='store_true', help='Exit (for context menu)')
    parser.add_argument('--enable-startup', action='store_true', help='Start with Windows')
    parser.add_argument('--disable-startup', action='store_true', help='Do not start with Windows')
    parser.add_argument('--startup', action='store_true', help='Internal startup launch mode')
    parser.add_argument('--startup-preset', metavar='NAME', help='Preset to restore automatically on startup')
    parser.add_argument('--clear-startup-preset', action='store_true', help='Disable preset restore on startup')
    
    args = parser.parse_args()
    
    try:
        # Handle command-line operations
        if args.save_dialog:
            success = handle_save_dialog()
            # Refresh context menu after saving
            if success:
                try_refresh_context_menu()
            sys.exit(0 if success else 1)

        if args.save_quadrants_dialog:
            success = handle_save_quadrants_dialog()
            if success:
                try_refresh_context_menu()
            sys.exit(0 if success else 1)
        
        if args.save:
            success = handle_save_preset(args.save)
            # Refresh context menu after saving
            if success:
                try_refresh_context_menu()
            sys.exit(0 if success else 1)

        if args.save_quadrants:
            success = handle_save_quadrant_preset(args.save_quadrants)
            if success:
                try_refresh_context_menu()
            sys.exit(0 if success else 1)
        
        if args.restore:
            success = handle_restore_preset(args.restore)
            sys.exit(0 if success else 1)
        
        if args.list:
            handle_list_presets()
            sys.exit(0)
        
        if args.manage:
            # Import and show preset manager
            from tkinter import messagebox, simpledialog
            from ui.dialogs import PresetListDialog
            from ui.dialogs import SavePresetDialog
            from shortcut_manager import create_shortcut

            pm = PresetManager()
            state = {'dialog': None}

            def refresh_dialog():
                dlg = state.get('dialog')
                if dlg:
                    dlg.refresh_presets(pm.list_presets())
            
            def on_restore(name):
                handle_restore_preset(name)
            
            def on_delete(preset_id, preset_name=None):
                deleted = pm.delete_preset_by_id(preset_id)
                if not deleted and preset_name:
                    deleted = pm.delete_preset(preset_name)
                if not deleted:
                    messagebox.showerror("Delete Failed", f"Could not delete preset: {preset_name or preset_id}")
                    return False
                # Refresh context menu
                try_refresh_context_menu()
                refresh_dialog()
                return True
            
            def on_shortcut(name):
                create_shortcut(name)
            
            def on_save(quadrants_only=False):
                dlg = state.get('dialog')
                parent = dlg.dialog if dlg else None
                if quadrants_only:
                    name = simpledialog.askstring(
                        "Save 4-Quadrant Layout",
                        "Enter a name for this preset:",
                        parent=parent
                    )
                    result = bool(name and name.strip() and handle_save_quadrant_preset(name.strip()))
                else:
                    save_dlg = SavePresetDialog(parent=parent, include_tabs=False)
                    if parent:
                        parent.wait_window(save_dlg.dialog)
                    result = False
                    if save_dlg.result:
                        result = handle_save_preset(
                            save_dlg.result['name'].strip(),
                            include_tabs=bool(save_dlg.result.get('include_tabs', False))
                        )
                if result:
                    # Refresh the list
                    refresh_dialog()
                    try_refresh_context_menu()

            def on_rename(old_name, new_name):
                if pm.rename_preset(old_name, new_name):
                    refresh_dialog()
                    try_refresh_context_menu()
            
            # Create custom dialog
            dialog = PresetListDialog(
                parent=None,
                presets=pm.list_presets(),
                on_restore=on_restore,
                on_delete=on_delete,
                on_shortcut=on_shortcut,
                on_save=on_save,
                on_rename=on_rename,
                auto_mainloop=False
            )
            state['dialog'] = dialog

            dialog.dialog.mainloop()
            sys.exit(0)
        
        if args.settings:
            success = handle_settings()
            sys.exit(0 if success else 1)
        
        if args.register:
            pm = PresetManager()
            presets = pm.get_preset_names()
            success = register_context_menu(presets)
            logger.info("Context menu registered" if success else "Failed to register context menu")
            sys.exit(0 if success else 1)
        
        if args.unregister:
            success = unregister_context_menu()
            logger.info("Context menu unregistered" if success else "Failed to unregister context menu")
            sys.exit(0 if success else 1)
        
        if args.shortcut:
            success = create_shortcut(args.shortcut)
            logger.info(f"Shortcut created for '{args.shortcut}'" if success else "Failed to create shortcut")
            sys.exit(0 if success else 1)
        
        if args.enable_startup:
            import winreg
            app_path = str(Path(__file__).resolve())
            pythonw_path = str(Path(sys.executable).with_name('pythonw.exe'))
            if not Path(pythonw_path).exists():
                pythonw_path = sys.executable
            key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                run_command = f'"{pythonw_path}" "{app_path}" --startup'
                winreg.SetValueEx(key, 'WindowRestore', 0, winreg.REG_SZ, run_command)
                winreg.CloseKey(key)
                if args.startup_preset:
                    pm = PresetManager()
                    if not pm.load_preset(args.startup_preset):
                        print(f"Preset not found: {args.startup_preset}")
                        sys.exit(1)
                    settings = load_settings()
                    settings['startup_preset'] = args.startup_preset
                    save_settings(settings)
                print("Added to Windows startup")
                logger.info("Added to Windows startup")
                sys.exit(0)
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)
        
        if args.disable_startup:
            import winreg
            key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, 'WindowRestore')
                winreg.CloseKey(key)
                print("Removed from Windows startup")
                logger.info("Removed from Windows startup")
                sys.exit(0)
            except FileNotFoundError:
                print("Not in startup")
                sys.exit(0)
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)

        if args.startup_preset:
            pm = PresetManager()
            preset = pm.load_preset(args.startup_preset)
            if not preset:
                print(f"Preset not found: {args.startup_preset}")
                sys.exit(1)
            settings = load_settings()
            settings['startup_preset'] = args.startup_preset
            if save_settings(settings):
                print(f"Startup preset set to: {args.startup_preset}")
                sys.exit(0)
            print("Failed to save startup preset")
            sys.exit(1)

        if args.clear_startup_preset:
            settings = load_settings()
            settings.pop('startup_preset', None)
            if save_settings(settings):
                print("Startup preset cleared")
                sys.exit(0)
            print("Failed to update startup settings")
            sys.exit(1)
        
        if args.exit:
            # Just exit cleanly
            sys.exit(0)
        
        # Start as system tray application
        if args.startup:
            settings = load_settings()
            startup_preset = settings.get('startup_preset')
            if startup_preset:
                logger.info(f"Startup mode: restoring preset '{startup_preset}'")
                handle_restore_preset(startup_preset)

        if not args.no_tray:
            app = TrayApp()
            app.run()
        else:
            logger.info("Window Restore started in console mode")
            
    except KeyboardInterrupt:
        logger.info("Application interrupted")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
