# Window Restore - Windows 11 Window & Program Position Preset Manager

## 1. Project Overview

**Project Name:** Window Restore (WinRestore)

**Type:** Windows Desktop Utility Application

**Core Feature Summary:** A Windows 11 utility that saves and restores window positions, sizes, and browser tabs to named presets, accessible via desktop shortcuts or right-click context menu.

**Target Users:** Power users who work with multiple windows and monitors and want to quickly restore their ideal desktop layout after a restart.

---

## 2. UI/UX Specification

### 2.1 Layout Structure

**System Tray Application:**
- Primary interface is system tray icon (no main window by default)
- Tray icon context menu for all operations
- Single main window for preset management (modal dialog)

**Main Window (Preset Manager):**
- **Size:** 600x450 pixels, centered on screen
- **Style:** Native Windows 11 dialog with standard title bar
- **Resizable:** No

**Dialogs:**
- Save Preset Dialog (modal)
- Restore Confirmation Dialog (modal)
- Settings Dialog (modal)

### 2.2 Visual Design

**Color Palette:**
- Primary: `#0078D4` (Windows Blue)
- Secondary: `#F3F3F3` (Light Gray Background)
- Accent: `#005A9E` (Dark Blue for hover states)
- Text Primary: `#1A1A1A`
- Text Secondary: `#666666`
- Success: `#107C10` (Green)
- Error: `#D83B01` (Red)
- Border: `#E1E1E1`

**Typography:**
- Font Family: Segoe UI (Windows default)
- Title: 14pt, SemiBold
- Body: 10pt, Regular
- Button Text: 10pt, SemiBold

**Spacing System:**
- Base unit: 8px
- Margins: 16px (outer), 8px (inner)
- Button padding: 8px 16px
- List item height: 40px

### 2.3 Components

**System Tray Menu:**
- "Save Current Layout" → Opens Save Dialog
- "Restore Layout" → Submenu with preset list
- "Manage Presets..." → Opens Preset Manager
- Separator
- "Settings" → Opens Settings Dialog
- "Exit"

**Preset Manager Window:**
- Title: "Window Restore - Manage Presets"
- Content:
  - List of saved presets (left panel, 250px width)
  - Preview/Detail panel (right panel)
- Actions:
  - "Save Current" button (top toolbar)
  - "Restore" button (bottom)
  - "Delete" button
  - "Create Shortcut" button
  - "Close" button

**Save Preset Dialog:**
- Text input: "Preset Name"
- Checkbox: "Include browser tabs"
- Buttons: "Save", "Cancel"

---

## 3. Functional Specification

### 3.1 Core Features

#### 3.1.1 Window State Capture
- Enumerate all visible top-level windows
- Capture for each window:
  - Executable path (process executable)
  - Window title (for matching)
  - Position (x, y coordinates)
  - Size (width, height)
  - Window state (normal, maximized, minimized)
  - Monitor index (0, 1, 2, etc.)
  - Is visible flag
- Filter out: System windows, hidden windows, certain system processes

#### 3.1.2 Window Restoration
- Launch programs from saved executable paths
- Wait for window to appear (with timeout)
- Apply saved position and size using SetWindowPos
- Restore window state (maximize/minimize)
- Handle multi-monitor configurations

#### 3.1.3 Browser Tab Detection
- **Chrome/Edge (Chromium-based):**
  - Use Chrome DevTools Protocol (CDP) via websocket
  - Connect to debug port (launch with --remote-debugging-port=9222)
  - Query tabs API for URL and title
- **Firefox:**
  - Use Firefox's remote debugging protocol
  - Connect to port (launch with --remote-debugging-port=9222)
  - Query tab URLs

#### 3.1.4 Preset Management
- Save preset: Capture current windows + optional browser tabs
- Load preset: Restore windows from saved state
- Delete preset: Remove preset file
- Rename preset: Change preset name

#### 3.1.5 Desktop Shortcuts
- Create .lnk files in user-defined folder (default: Desktop)
- Shortcut name includes preset name
- Shortcut launches app with --restore="PresetName" argument

#### 3.1.6 Context Menu Integration
- Add "Window Restore" to desktop right-click menu
- Submenu lists all saved presets
- Clicking preset name restores that layout

### 3.2 Data Flow & Processing

**Data Storage:**
- Location: `%APPDATA%\WindowRestore\`
- Files:
  - `presets.json` - All preset data
  - `settings.json` - Application settings
  - `window_restore.log` - Log file

**Preset JSON Structure:**
```json
{
  "presets": [
    {
      "id": "uuid",
      "name": "Work Setup",
      "created": "2024-01-15T10:30:00Z",
      "windows": [
        {
          "executable": "C:\\Program Files\\...",
          "args": "",
          "title": "Visual Studio Code",
          "x": 0,
          "y": 0,
          "width": 1920,
          "height": 1040,
          "state": "maximized",
          "monitor": 0,
          "tabs": [
            {"url": "https://github.com", "title": "GitHub"}
          ]
        }
      ]
    }
  ]
}
```

### 3.3 Key Modules/Classes

| Module | Responsibility | Public API |
|--------|---------------|------------|
| `window_capture.py` | Enumerate and capture window states | `capture_windows()`, `get_window_info(hwnd)` |
| `window_restore.py` | Restore windows to saved positions | `restore_windows(preset)`, `launch_and_position(window_info)` |
| `browser_tabs.py` | Get browser tabs from Chrome/Firefox/Edge | `get_chrome_tabs()`, `get_firefox_tabs()`, `get_edge_tabs()` |
| `preset_manager.py` | CRUD operations for presets | `save_preset(name, data)`, `load_preset(name)`, `delete_preset(id)`, `list_presets()` |
| `shortcut_manager.py` | Create/manage Windows shortcuts | `create_shortcut(preset_name, target)`, `delete_shortcut(name)` |
| `context_menu.py` | Manage desktop context menu | `register_context_menu()`, `unregister_context_menu()` |
| `tray_app.py` | System tray application | Main application entry point |

### 3.4 Edge Cases

1. **Program not installed:** Skip missing programs during restore, log warning
2. **Monitor disconnected:** Map to available monitor, prefer primary
3. **Browser not running with debug port:** Launch with debug flag or skip tabs
4. **Window fails to appear:** Retry 3 times with 2-second timeout
5. **Permission denied:** Request elevation or log error
6. **Preset file corrupted:** Backup and create new, notify user
7. **Duplicate preset name:** Append number (e.g., "Work Setup (2)")

---

## 4. Acceptance Criteria

### 4.1 Success Conditions

| Feature | Criteria |
|---------|----------|
| Window Capture | Captures position, size, state for all visible windows |
| Window Restore | Restores windows to correct position, size, and state |
| Browser Tabs | Detects and restores tabs for Chrome, Firefox, Edge |
| Preset Save | Saves preset with user-provided name to JSON |
| Preset Load | Loads and restores preset correctly |
| Desktop Shortcut | Creates working shortcut that restores preset |
| Context Menu | Right-click shows preset list, clicking restores preset |
| System Tray | Icon appears, menu works correctly |

### 4.2 Visual Checkpoints

1. System tray icon visible and responds to clicks
2. Tray menu displays all options correctly
3. Preset Manager shows list of saved presets
4. Save dialog captures preset name
5. Desktop shortcuts have correct icon and name
6. Context menu appears on desktop right-click
7. Windows restore to exact saved positions

---

## 5. Technical Stack

- **Language:** Python 3.10+
- **Key Libraries:**
  - `pywin32` - Windows API access
  - `win32gui` - Window enumeration and positioning
  - `psutil` - Process information
  - `websocket-client` - Chrome/Firefox CDP connection
  - `pystray` - System tray icon
  - `PyQt6` or `tkinter` - UI components
- **Build:** PyInstaller for standalone .exe
- **Storage:** JSON files in AppData

---

## 6. File Structure

```
WindowRestore/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── window_capture.py      # Window enumeration
│   ├── window_restore.py      # Window positioning
│   ├── browser_tabs.py        # Browser tab detection
│   ├── preset_manager.py      # Preset CRUD
│   ├── shortcut_manager.py    # .lnk creation
│   ├── context_menu.py        # Registry operations
│   ├── tray_app.py            # System tray
│   └── ui/
│       ├── __init__.py
│       ├── preset_manager.py  # Preset manager window
│       └── dialogs.py         # Various dialogs
├── assets/
│   └── icon.ico               # App icon
├── requirements.txt
├── SPEC.md
└── README.md
```
