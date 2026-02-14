"""
Context Menu Module
Registers a native Windows cascading context menu on desktop background.
"""

import logging
import winreg
import os
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

CONTEXT_MENU_KEY = r"Software\Classes\Directory\Background\shell\WindowRestore"


def get_ps1_path() -> str:
    """Get path to PowerShell menu script"""
    ps1_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'context_menu.ps1')
    return ps1_path


def _get_runner_command() -> tuple[str, str]:
    """Return python runner and main.py path."""
    main_path = str(Path(__file__).resolve().parent / 'main.py')
    pythonw_path = Path(sys.executable).with_name('pythonw.exe')
    runner = str(pythonw_path if pythonw_path.exists() else Path(sys.executable))
    return runner, main_path


def _set_default_command(base_key: str, command: str):
    cmd_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key + r"\command")
    winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
    cmd_key.Close()


def _delete_registry_tree(root, key_path: str):
    """Delete a registry key and all subkeys."""
    try:
        with winreg.OpenKey(root, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            while True:
                try:
                    subkey = winreg.EnumKey(key, 0)
                    _delete_registry_tree(root, f"{key_path}\\{subkey}")
                except OSError:
                    break
        winreg.DeleteKey(root, key_path)
    except (FileNotFoundError, PermissionError):
        return


def register_context_menu(preset_names: List[str] = None, quiet: bool = False) -> bool:
    """Register native cascading context menu."""
    try:
        try:
            _delete_registry_tree(winreg.HKEY_CURRENT_USER, CONTEXT_MENU_KEY)
        except Exception:
            pass

        runner, main_path = _get_runner_command()

        # Main cascading container
        main_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, CONTEXT_MENU_KEY)
        winreg.SetValueEx(main_key, "MUIVerb", 0, winreg.REG_SZ, "Window Restore")
        winreg.SetValueEx(main_key, "SubCommands", 0, winreg.REG_SZ, "")
        main_key.Close()

        shell_root = CONTEXT_MENU_KEY + r"\shell"
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, shell_root).Close()

        # Save Current Layout
        save_key = shell_root + r"\save"
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, save_key)
        winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "Save Current Layout...")
        k.Close()
        _set_default_command(save_key, f'"{runner}" "{main_path}" --save-dialog')

        # Restore submenu
        restore_key = shell_root + r"\restore"
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, restore_key)
        winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "Restore Layout")
        winreg.SetValueEx(k, "SubCommands", 0, winreg.REG_SZ, "")
        k.Close()

        restore_shell_root = restore_key + r"\shell"
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, restore_shell_root).Close()

        names = preset_names or []
        for idx, preset in enumerate(names, start=1):
            key_name = f"preset_{idx:03d}"
            subkey = restore_shell_root + "\\" + key_name
            sk = winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey)
            winreg.SetValueEx(sk, "MUIVerb", 0, winreg.REG_SZ, preset)
            sk.Close()
            _set_default_command(subkey, f'"{runner}" "{main_path}" --restore "{preset}"')

        # Manage Presets
        manage_key = shell_root + r"\manage"
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, manage_key)
        winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "Manage Presets...")
        k.Close()
        _set_default_command(manage_key, f'"{runner}" "{main_path}" --manage')

        logger.info("Context menu registered with native cascading menu")
        return True
        
    except Exception as e:
        if quiet:
            logger.debug(f"Context menu refresh skipped: {e}")
        else:
            logger.error(f"Error: {e}")
        return False


def unregister_context_menu() -> bool:
    """Remove context menu"""
    try:
        _delete_registry_tree(winreg.HKEY_CURRENT_USER, CONTEXT_MENU_KEY)
        logger.info("Context menu unregistered")
        return True
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def refresh_context_menu(quiet: bool = False) -> bool:
    """Refresh with current presets"""
    from preset_manager import PresetManager
    pm = PresetManager()
    return register_context_menu(pm.get_preset_names(), quiet=quiet)
