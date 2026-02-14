"""
Dialogs Module
Simple dialogs for preset management using tkinter
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import Optional, List, Callable


class SavePresetDialog:
    """Dialog for saving a new preset"""
    
    def __init__(self, parent: tk.Tk = None, include_tabs: bool = True):
        self.result = None
        self.include_tabs = include_tabs
        
        self.dialog = tk.Toplevel(parent) if parent else tk.Tk()
        self.dialog.title("Save Window Layout")
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"400x150+{x}+{y}")
        
        self._build_ui()
        
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        if not parent:
            self.dialog.mainloop()
    
    def _build_ui(self):
        """Build the dialog UI"""
        # Name input
        frame = ttk.Frame(self.dialog, padding="16")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Preset Name:").pack(anchor=tk.W)
        
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(frame, textvariable=self.name_var, width=40)
        name_entry.pack(fill=tk.X, pady=(4, 16))
        name_entry.focus()
        
        # Include tabs checkbox
        self.include_tabs_var = tk.BooleanVar(value=self.include_tabs)
        tabs_check = ttk.Checkbutton(
            frame, 
            text="Include browser tabs (requires browsers to have debugging enabled)",
            variable=self.include_tabs_var
        )
        tabs_check.pack(anchor=tk.W, pady=(0, 16))
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Save", command=self._on_save).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT)
    
    def _on_save(self):
        """Handle save button"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a preset name")
            return
        
        self.result = {
            'name': name,
            'include_tabs': self.include_tabs_var.get()
        }
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel button"""
        self.result = None
        self.dialog.destroy()


class PresetListDialog:
    """Dialog for listing and selecting presets"""
    
    def __init__(
        self, 
        parent: tk.Tk = None, 
        presets: List[dict] = None,
        on_restore: Callable = None,
        on_delete: Callable = None,
        on_shortcut: Callable = None,
        on_save: Callable = None,
        on_rename: Callable = None,
        auto_mainloop: bool = True
    ):
        self.result = None
        self.presets = presets or []
        self.on_restore = on_restore
        self.on_delete = on_delete
        self.on_shortcut = on_shortcut
        self.on_save = on_save
        self.on_rename = on_rename
        
        self.dialog = tk.Toplevel(parent) if parent else tk.Tk()
        self.dialog.title("Window Restore - Manage Presets")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"600x400+{x}+{y}")
        
        self._build_ui()
        
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        if not parent and auto_mainloop:
            self.dialog.mainloop()
    
    def _build_ui(self):
        """Build the dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Button(toolbar, text="Save Current Layout", command=self._on_save).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(toolbar, text="Save 4-Quadrant Layout", command=self._on_save_quadrants).pack(side=tk.LEFT, padx=(0, 8))
        
        # List frame with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10)
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        self.listbox.bind('<<ListboxSelect>>', self._on_select)
        self.listbox.bind('<Double-Button-1>', self._on_double_click)
        
        # Populate list
        for preset in self.presets:
            self.listbox.insert(tk.END, f"{preset['name']} ({preset['window_count']} windows)")
        
        # Detail frame
        self.detail_frame = ttk.LabelFrame(main_frame, text="Details", padding="8")
        self.detail_frame.pack(fill=tk.X, pady=(8, 0))
        
        self.detail_label = ttk.Label(self.detail_frame, text="Select a preset")
        self.detail_label.pack(anchor=tk.W)
        
        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(8, 0))
        
        self.restore_btn = ttk.Button(btn_frame, text="Restore", command=self._on_restore_click)
        self.restore_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.restore_btn.config(state=tk.DISABLED)
        
        self.shortcut_btn = ttk.Button(btn_frame, text="Create Shortcut", command=self._on_shortcut_click)
        self.shortcut_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.shortcut_btn.config(state=tk.DISABLED)
        
        self.delete_btn = ttk.Button(btn_frame, text="Delete", command=self._on_delete_click)
        self.delete_btn.pack(side=tk.LEFT)
        self.delete_btn.config(state=tk.DISABLED)

        self.rename_btn = ttk.Button(btn_frame, text="Rename", command=self._on_rename_click)
        self.rename_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.rename_btn.config(state=tk.DISABLED)
        
        ttk.Button(btn_frame, text="Close", command=self._on_close).pack(side=tk.RIGHT)
        
        self.selected_index = None

    def refresh_presets(self, presets: List[dict]):
        """Refresh list contents and clear selection state."""
        self.presets = presets or []
        self.listbox.delete(0, tk.END)
        for preset in self.presets:
            self.listbox.insert(tk.END, f"{preset['name']} ({preset['window_count']} windows)")
        self.selected_index = None
        self.detail_label.config(text="Select a preset")
        self.restore_btn.config(state=tk.DISABLED)
        self.shortcut_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        self.rename_btn.config(state=tk.DISABLED)
        self.dialog.update_idletasks()
    
    def _on_select(self, event):
        """Handle list selection"""
        selection = self.listbox.curselection()
        if selection:
            self.selected_index = selection[0]
            preset = self.presets[self.selected_index]
            
            # Update detail
            self.detail_label.config(
                text=f"Name: {preset['name']}\n"
                     f"Windows: {preset['window_count']}\n"
                     f"Created: {preset.get('created', 'Unknown')}"
            )
            
            # Enable buttons
            self.restore_btn.config(state=tk.NORMAL)
            self.shortcut_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.NORMAL)
            self.rename_btn.config(state=tk.NORMAL)
        else:
            self.selected_index = None
            self.detail_label.config(text="Select a preset")
            self.restore_btn.config(state=tk.DISABLED)
            self.shortcut_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            self.rename_btn.config(state=tk.DISABLED)
    
    def _on_double_click(self, event):
        """Handle double click - restore preset"""
        if self.selected_index is not None and self.on_restore:
            preset = self.presets[self.selected_index]
            self.on_restore(preset['name'])
    
    def _on_save(self):
        """Handle save button"""
        if self.on_save:
            self.on_save()

    def _on_save_quadrants(self):
        """Handle save quadrants button"""
        if self.on_save:
            self.on_save(quadrants_only=True)
    
    def _on_restore_click(self):
        """Handle restore button"""
        if self.selected_index is not None and self.on_restore:
            preset = self.presets[self.selected_index]
            self.on_restore(preset['name'])
    
    def _on_shortcut_click(self):
        """Handle shortcut button"""
        if self.selected_index is not None and self.on_shortcut:
            preset = self.presets[self.selected_index]
            self.on_shortcut(preset['name'])
    
    def _on_delete_click(self):
        """Handle delete button"""
        if self.selected_index is not None and self.on_delete:
            preset = self.presets[self.selected_index]
            if messagebox.askyesno("Confirm Delete", f"Delete preset '{preset['name']}'?"):
                try:
                    deleted = self.on_delete(preset['id'], preset['name'])
                except Exception as e:
                    messagebox.showerror("Delete Failed", f"Error deleting preset: {e}")
                    return
                if not deleted:
                    return
                # Immediate local UI update so user sees deletion instantly.
                idx = self.selected_index
                if 0 <= idx < len(self.presets):
                    self.presets.pop(idx)
                self.listbox.delete(idx)
                self.selected_index = None
                self.detail_label.config(text="Select a preset")
                self.restore_btn.config(state=tk.DISABLED)
                self.shortcut_btn.config(state=tk.DISABLED)
                self.delete_btn.config(state=tk.DISABLED)
                self.rename_btn.config(state=tk.DISABLED)

    def _on_rename_click(self):
        """Handle rename button"""
        if self.selected_index is not None and self.on_rename:
            preset = self.presets[self.selected_index]
            new_name = simpledialog.askstring(
                "Rename Preset",
                "New preset name:",
                initialvalue=preset['name'],
                parent=self.dialog
            )
            if new_name and new_name.strip():
                self.on_rename(preset['name'], new_name.strip())
    
    def _on_close(self):
        """Handle close"""
        self.dialog.destroy()


def ask_preset_name(parent: tk.Tk = None, title: str = "Enter Preset Name", prompt: str = "Preset Name:") -> Optional[str]:
    """Simple dialog to get a preset name"""
    return simpledialog.askstring(title, prompt, parent=parent)


def show_message(title: str, message: str, parent: tk.Tk = None):
    """Show an information message"""
    messagebox.showinfo(title, message, parent=parent)


def show_error(title: str, message: str, parent: tk.Tk = None):
    """Show an error message"""
    messagebox.showerror(title, message, parent=parent)


def ask_yes_no(title: str, message: str, parent: tk.Tk = None) -> bool:
    """Ask a yes/no question"""
    return messagebox.askyesno(title, message, parent=parent)
