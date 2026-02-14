"""
Uninstaller Module
Removes all Window Restore components
"""

import sys
import os
import logging
from pathlib import Path

# Setup logging
DATA_DIR = Path.home() / 'AppData' / 'Roaming' / 'WindowRestore'
LOG_FILE = DATA_DIR / 'uninstall.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def unregister_context_menu() -> bool:
    """Remove context menu from registry"""
    try:
        import winreg
        key_path = r"Software\Classes\Directory\Background\shell\WindowRestore"
        
        # Delete subkeys first
        try:
            subkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
            try:
                while True:
                    subkey_name = winreg.EnumKey(subkey, 0)
                    winreg.DeleteKey(subkey, subkey_name)
            except OSError:
                pass
            winreg.CloseKey(subkey)
        except FileNotFoundError:
            pass
        
        # Delete main key
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except FileNotFoundError:
            pass
        
        logger.info("Context menu removed")
        return True
    except Exception as e:
        logger.error(f"Error removing context menu: {e}")
        return False


def delete_shortcuts() -> bool:
    """Delete all desktop shortcuts"""
    try:
        desktop = Path.home() / 'Desktop'
        deleted = []
        
        for f in desktop.glob("WindowRestore - *.lnk"):
            f.unlink()
            deleted.append(str(f))
        
        for f in desktop.glob("Window Restore - *.lnk"):
            f.unlink()
            deleted.append(str(f))
        
        logger.info(f"Deleted {len(deleted)} shortcuts")
        return True
    except Exception as e:
        logger.error(f"Error deleting shortcuts: {e}")
        return False


def delete_presets() -> bool:
    """Delete all saved presets"""
    try:
        if DATA_DIR.exists():
            presets_file = DATA_DIR / 'presets.json'
            if presets_file.exists():
                presets_file.unlink()
            settings_file = DATA_DIR / 'settings.json'
            if settings_file.exists():
                settings_file.unlink()
        logger.info("Presets deleted")
        return True
    except Exception as e:
        logger.error(f"Error deleting presets: {e}")
        return False


def main():
    """Main uninstaller entry point"""
    print("Window Restore Uninstaller")
    print("=" * 40)
    print()
    
    # Unregister context menu
    print("[1/3] Removing context menu...")
    if unregister_context_menu():
        print("  [OK] Context menu removed")
    else:
        print("  [FAIL] Failed to remove context menu (may need admin)")
    
    # Delete shortcuts
    print("[2/3] Deleting desktop shortcuts...")
    if delete_shortcuts():
        print("  [OK] Shortcuts deleted")
    else:
        print("  [FAIL] Failed to delete shortcuts")
    
    # Delete presets (optional)
    print("[3/3] Deleting saved presets...")
    if delete_presets():
        print("  [OK] Presets deleted")
    else:
        print("  [FAIL] Failed to delete presets")
    
    print()
    print("Uninstallation complete!")
    print(f"Log file: {LOG_FILE}")
    print()
    print("Press Enter to exit...")
    input()


if __name__ == '__main__':
    main()
