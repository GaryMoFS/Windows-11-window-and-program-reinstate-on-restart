"""
Shortcut Manager Module
Creates Windows .lnk shortcut files
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_app_path() -> str:
    """Get the path to the application entry point."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return str(Path(__file__).resolve().parent / 'main.py')


def get_python_runner() -> str:
    """Prefer pythonw to avoid console windows when running shortcuts."""
    pythonw_path = Path(sys.executable).with_name('pythonw.exe')
    if pythonw_path.exists():
        return str(pythonw_path)
    return sys.executable


def _shortcut_target_and_args(preset_name: str) -> tuple[str, str, str]:
    """Return target path, arguments, and working directory for a shortcut."""
    app_path = get_app_path()
    if getattr(sys, 'frozen', False):
        return app_path, f'--restore "{preset_name}"', os.path.dirname(app_path)
    runner = get_python_runner()
    return runner, f'"{app_path}" --restore "{preset_name}"', str(Path(app_path).parent)


def create_shortcut(preset_name: str, output_path: Path = None) -> bool:
    """Create a desktop shortcut for a preset."""
    try:
        import comtypes.client

        if output_path is None:
            output_path = Path.home() / 'Desktop'

        shortcut_name = f"WindowRestore - {preset_name}.lnk"
        shortcut_path = output_path / shortcut_name

        target_path, arguments, working_dir = _shortcut_target_and_args(preset_name)

        shell = comtypes.client.CreateObject('WScript.Shell')
        shortcut = shell.CreateShortcut(str(shortcut_path))
        shortcut.TargetPath = target_path
        shortcut.Arguments = arguments
        shortcut.WorkingDirectory = working_dir
        shortcut.Description = f"Restore window layout: {preset_name}"
        shortcut.Save()

        logger.info(f"Created shortcut: {shortcut_path}")
        return True

    except ImportError:
        logger.warning("comtypes not available, trying alternative method")
        return create_shortcut_fallback(preset_name, output_path)
    except Exception as e:
        logger.error(f"Error creating shortcut: {e}")
        return create_shortcut_fallback(preset_name, output_path)


def create_shortcut_fallback(preset_name: str, output_path: Path = None) -> bool:
    """Fallback method to create shortcut using PowerShell."""
    try:
        import subprocess

        if output_path is None:
            output_path = Path.home() / 'Desktop'

        shortcut_name = f"WindowRestore - {preset_name}.lnk"
        shortcut_path = output_path / shortcut_name
        target_path, arguments, _ = _shortcut_target_and_args(preset_name)

        ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_path}"
$Shortcut.Arguments = '{arguments}'
$Shortcut.Description = "Restore window layout: {preset_name}"
$Shortcut.Save()
'''

        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"Created shortcut (fallback): {shortcut_path}")
            return True

        logger.error(f"PowerShell error: {result.stderr}")
        return False

    except Exception as e:
        logger.error(f"Error creating shortcut (fallback): {e}")
        return False


def delete_shortcut(preset_name: str, output_path: Path = None) -> bool:
    """Delete a desktop shortcut for a preset."""
    try:
        if output_path is None:
            output_path = Path.home() / 'Desktop'

        shortcut_name = f"WindowRestore - {preset_name}.lnk"
        shortcut_path = output_path / shortcut_name

        if shortcut_path.exists():
            shortcut_path.unlink()
            logger.info(f"Deleted shortcut: {shortcut_path}")
            return True

        return False

    except Exception as e:
        logger.error(f"Error deleting shortcut: {e}")
        return False


def list_shortcuts(output_path: Path = None) -> list:
    """List all Window Restore shortcuts in a directory."""
    if output_path is None:
        output_path = Path.home() / 'Desktop'

    if not output_path.exists():
        return []

    shortcuts = []
    for f in output_path.glob("WindowRestore - *.lnk"):
        name = f.stem.replace("WindowRestore - ", "")
        shortcuts.append(name)

    return shortcuts
