# Window Restore

Windows utility to save and restore desktop app layouts as named presets.

## Features

- Save current window layout to a preset
- Restore a preset from tray or desktop context menu
- Save 4-window quadrant layouts quickly
- Manage presets (restore, rename, delete, create shortcut)
- Optional startup restore on sign-in

## Requirements

- Windows 11
- Python 3.10+
- Dependencies from `requirements.txt`

Install:

```powershell
pip install -r requirements.txt
```

## Run

Start tray app:

```powershell
python src/main.py
```

Useful commands:

```powershell
python src/main.py --save "Work"
python src/main.py --save-quadrants "Quad Work"
python src/main.py --restore "Work"
python src/main.py --manage
python src/main.py --list
```

Startup restore:

```powershell
python src/main.py --startup-preset "Work"
python src/main.py --enable-startup --startup-preset "Work"
```

## Notes

- Browser tab restore automation is disabled by default for safety.
- Some apps manage their own session state and may behave differently on restore.

## License

MIT (see `LICENSE`).
