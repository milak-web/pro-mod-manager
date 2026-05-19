#!/usr/bin/env python3
"""
PRO Mod Manager - Final Version with Visual Enhancements

Features:
- Moves FILES from mod folder to game directory
- Proper tracking system
- Visual enhancements for better UX
- Professional look and feel
"""

import os
import json
import shutil
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime

APP_STATE_FILE = "mod_manager_state.json"
APP_SETTINGS_FILE = "mod_manager_settings.json"

class TrackingModManager:
    def __init__(self, game_dir, repo_dir, state_file):
        self.game_dir = Path(game_dir)
        self.repo_dir = Path(repo_dir)
        self.state_file = Path(state_file)
        self.state = self._load_state()
        
        if not self.state.get("profiles"):
            self.create_profile("Default")
            self.set_current_profile("Default")
    
    def _load_state(self):
        try:
            if self.state_file.exists():
                return json.loads(self.state_file.read_text())
        except:
            pass
        return {"current_profile": None, "profiles": {}}
    
    def _save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))
    
    # Profile management
    def list_profiles(self):
        return sorted(self.state.get("profiles", {}).keys())
    
    def create_profile(self, name):
        if name in self.state.get("profiles", {}):
            raise ValueError("Profile already exists")
        self.state.setdefault("profiles", {})[name] = {
            "active_mods": [],
            "mod_files": {}
        }
        self._save_state()
    
    def get_current_profile(self):
        return self.state.get("current_profile")
    
    def set_current_profile(self, name):
        if name not in self.state.get("profiles", {}):
            self.create_profile(name)
        self.state["current_profile"] = name
        self._save_state()
    
    def get_profile_data(self):
        current = self.get_current_profile()
        if current:
            return self.state.get("profiles", {}).get(current, {"active_mods": [], "mod_files": {}})
        return {"active_mods": [], "mod_files": {}}
    
    # Helper: Get all files in folder with relative paths
    def _get_all_files(self, folder):
        files = []
        if folder.exists():
            for root, dirs, filenames in os.walk(folder):
                for f in filenames:
                    file_path = Path(root) / f
                    rel_path = file_path.relative_to(folder)
                    files.append(str(rel_path))
        return files
    
    # Mod management
    def list_available_mods(self):
        """List ALL mod folders in repository"""
        all_mods = []
        for item in self.repo_dir.iterdir():
            if item.is_dir():
                all_mods.append(item.name)
        
        profile_data = self.get_profile_data()
        active_mods = set(profile_data.get("active_mods", []))
        
        return sorted([m for m in all_mods if m not in active_mods])
    
    def list_active_mods(self):
        """List mods that ARE active (based on state tracking)"""
        profile_data = self.get_profile_data()
        active_mods = profile_data.get("active_mods", [])
        
        # Verify each active mod actually has its tracked files in game
        verified_active = []
        for mod_name in active_mods:
            mod_files = profile_data.get("mod_files", {}).get(mod_name, [])
            
            has_files = False
            for rel_path in mod_files:
                game_file = self.game_dir / rel_path
                if game_file.exists():
                    has_files = True
                    break
            
            if has_files:
                verified_active.append(mod_name)
            else:
                # Clean up state
                current = self.get_current_profile()
                if current:
                    if mod_name in self.state["profiles"][current]["active_mods"]:
                        self.state["profiles"][current]["active_mods"].remove(mod_name)
                    if "mod_files" in self.state["profiles"][current]:
                        if mod_name in self.state["profiles"][current]["mod_files"]:
                            del self.state["profiles"][current]["mod_files"][mod_name]
        
        self._save_state()
        return sorted(verified_active)
    
    def activate_mod(self, mod_name):
        """MOVE FILES from mod folder to game directory AND TRACK THEM"""
        current_profile = self.get_current_profile()
        if not current_profile:
            self.set_current_profile("Default")
            current_profile = "Default"
        
        if mod_name in self.get_profile_data().get("active_mods", []):
            return True  # Already active
        
        mod_folder = self.repo_dir / mod_name
        
        if not mod_folder.exists():
            raise ValueError(f"Mod folder '{mod_name}' not found")
        
        # Get all files in mod folder
        files_to_move = self._get_all_files(mod_folder)
        if not files_to_move:
            raise ValueError(f"Mod '{mod_name}' has no files")
        
        # Track which files we're moving
        moved_files = []
        
        # Move each file
        for rel_path in files_to_move:
            src_file = mod_folder / rel_path
            dst_file = self.game_dir / rel_path
            
            if src_file.exists():
                # Create destination directory
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Remove destination if exists
                if dst_file.exists():
                    if dst_file.is_dir():
                        shutil.rmtree(dst_file)
                    else:
                        dst_file.unlink()
                
                # MOVE the file
                shutil.move(str(src_file), str(dst_file))
                moved_files.append(rel_path)
        
        if not moved_files:
            return False
        
        # UPDATE STATE
        if mod_name not in self.state["profiles"][current_profile]["active_mods"]:
            self.state["profiles"][current_profile]["active_mods"].append(mod_name)
        
        if "mod_files" not in self.state["profiles"][current_profile]:
            self.state["profiles"][current_profile]["mod_files"] = {}
        
        self.state["profiles"][current_profile]["mod_files"][mod_name] = moved_files
        self._save_state()
        
        return True
    
    def deactivate_mod(self, mod_name):
        """MOVE FILES from game directory back to mod folder using TRACKED list"""
        current_profile = self.get_current_profile()
        if not current_profile:
            self.set_current_profile("Default")
            current_profile = "Default"
        
        # Get tracked files for this mod
        profile_data = self.get_profile_data()
        tracked_files = profile_data.get("mod_files", {}).get(mod_name, [])
        
        mod_folder = self.repo_dir / mod_name
        mod_folder.mkdir(parents=True, exist_ok=True)
        
        moved_back = 0
        
        # Move back tracked files
        for rel_path in tracked_files:
            game_file = self.game_dir / rel_path
            mod_file = mod_folder / rel_path
            
            if game_file.exists():
                # Create directory in mod folder
                mod_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Remove destination if exists
                if mod_file.exists():
                    if mod_file.is_dir():
                        shutil.rmtree(mod_file)
                    else:
                        mod_file.unlink()
                
                # MOVE the file back
                shutil.move(str(game_file), str(mod_file))
                moved_back += 1
        
        # Update state
        if mod_name in self.state["profiles"][current_profile]["active_mods"]:
            self.state["profiles"][current_profile]["active_mods"].remove(mod_name)
        
        if "mod_files" in self.state["profiles"][current_profile]:
            if mod_name in self.state["profiles"][current_profile]["mod_files"]:
                del self.state["profiles"][current_profile]["mod_files"][mod_name]
        
        self._save_state()
        
        return moved_back > 0
    
    def deactivate_all(self):
        """Deactivate all mods"""
        current_profile = self.get_current_profile()
        if not current_profile:
            return
        
        active_mods = self.get_profile_data().get("active_mods", [])[:]
        for mod_name in active_mods:
            self.deactivate_mod(mod_name)


class ProModSelectorUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PRO Mod Manager v1.2")
        self.geometry("1040x760")
        self.minsize(980, 700)
        
        # Color system
        self.bg_color = "#171B22"
        self.panel_color = "#1F2530"
        self.panel_alt_color = "#242C38"
        self.fg_color = "#F2F5FA"
        self.muted_color = "#9AA6B8"
        self.accent_color = "#3B82F6"
        self.success_color = "#20B26B"
        self.warning_color = "#ED9D2B"
        self.error_color = "#E14D4D"
        self.border_color = "#2F3A4C"
        
        # Configure colors
        self.configure(bg=self.bg_color)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()
        
        # Load settings
        self.state_file = Path(APP_STATE_FILE)
        self.settings_file = Path(APP_SETTINGS_FILE)
        self.mod_manager = None
        self.load_settings()
        
        # Create UI
        self.create_widgets()
        
        # Try to initialize if paths are already set
        self.try_initialize()
    
    def load_settings(self):
        if self.settings_file.exists():
            try:
                data = json.loads(self.settings_file.read_text(encoding='utf-8'))
                self.last_game_dir = data.get("last_game_dir", "")
                self.last_repo_dir = data.get("last_repo_dir", "")
            except:
                self.last_game_dir = ""
                self.last_repo_dir = ""
        else:
            self.last_game_dir = ""
            self.last_repo_dir = ""
    
    def save_settings(self):
        data = {
            "last_game_dir": self.game_dir_var.get(),
            "last_repo_dir": self.repo_dir_var.get()
        }
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings_file.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def configure_styles(self):
        self.style.configure("Root.TFrame", background=self.bg_color)
        self.style.configure("Panel.TFrame", background=self.panel_color)
        self.style.configure("PanelAlt.TFrame", background=self.panel_alt_color)
        self.style.configure(
            "Card.TLabelframe",
            background=self.panel_color,
            bordercolor=self.border_color,
            darkcolor=self.border_color,
            lightcolor=self.border_color,
            relief="solid",
            borderwidth=1
        )
        self.style.configure(
            "Card.TLabelframe.Label",
            background=self.panel_color,
            foreground=self.fg_color,
            font=("Segoe UI Semibold", 10)
        )
        self.style.configure("Title.TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 11))
        self.style.configure("Muted.TLabel", background=self.panel_color, foreground=self.muted_color, font=("Segoe UI", 9))
        self.style.configure("SectionHeader.TLabel", background=self.panel_color, foreground=self.fg_color, font=("Segoe UI Semibold", 10))
        self.style.configure("TLabel", background=self.panel_color, foreground=self.fg_color, font=("Segoe UI", 10))
        self.style.configure(
            "TEntry",
            fieldbackground="#121720",
            background="#121720",
            foreground=self.fg_color,
            insertcolor=self.fg_color,
            bordercolor=self.border_color,
            lightcolor=self.border_color,
            darkcolor=self.border_color
        )
        self.style.configure(
            "TCombobox",
            fieldbackground="#121720",
            background="#121720",
            foreground=self.fg_color,
            bordercolor=self.border_color,
            lightcolor=self.border_color,
            darkcolor=self.border_color
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#121720")],
            foreground=[("readonly", self.fg_color)],
            selectbackground=[("readonly", self.accent_color)],
            selectforeground=[("readonly", self.fg_color)]
        )
        self.style.configure(
            "TButton",
            background=self.panel_alt_color,
            foreground=self.fg_color,
            bordercolor=self.border_color,
            padding=(10, 6),
            font=("Segoe UI Semibold", 9)
        )
        self.style.map(
            "TButton",
            background=[("active", "#2D3746"), ("pressed", "#202837")]
        )
        self.style.configure(
            "Accent.TButton",
            background=self.accent_color,
            foreground="#FFFFFF",
            bordercolor=self.accent_color,
            padding=(10, 6),
            font=("Segoe UI Semibold", 9)
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", "#2E6BCC"), ("pressed", "#275BAE")]
        )
        self.style.configure(
            "TProgressbar",
            background=self.accent_color,
            troughcolor="#10151D",
            bordercolor=self.border_color,
            lightcolor=self.accent_color,
            darkcolor=self.accent_color
        )
        self.option_add("*TCombobox*Listbox.background", "#121720")
        self.option_add("*TCombobox*Listbox.foreground", self.fg_color)
        self.option_add("*TCombobox*Listbox.selectBackground", self.accent_color)
        self.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
    
    def create_widgets(self):
        # Main container with padding
        main_container = ttk.Frame(self, style="Root.TFrame")
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Header frame
        header_frame = ttk.Frame(main_container, style="Root.TFrame")
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Title
        title_label = tk.Label(header_frame, text="PRO MOD MANAGER", 
                              font=('Segoe UI Semibold', 22),
                              bg=self.bg_color, fg=self.fg_color)
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="Fast profile-based mod switching for your games",
                                 font=('Segoe UI', 10),
                                 bg=self.bg_color, fg=self.muted_color)
        subtitle_label.pack()
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_container, text="Configuration", padding=12, style="Card.TLabelframe")
        config_frame.pack(fill='x', pady=(0, 15))
        
        # Game directory
        game_frame = ttk.Frame(config_frame, style="Panel.TFrame")
        game_frame.pack(fill='x', pady=5)
        
        ttk.Label(game_frame, text="Game Folder:", width=15).pack(side='left')
        self.game_dir_var = tk.StringVar(value=self.last_game_dir)
        game_entry = ttk.Entry(game_frame, textvariable=self.game_dir_var)
        game_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(game_frame, text="📁", width=3, command=self.browse_game).pack(side='left')
        
        # Mod repository
        repo_frame = ttk.Frame(config_frame, style="Panel.TFrame")
        repo_frame.pack(fill='x', pady=5)
        
        ttk.Label(repo_frame, text="Mod Repository:", width=15).pack(side='left')
        self.repo_dir_var = tk.StringVar(value=self.last_repo_dir)
        repo_entry = ttk.Entry(repo_frame, textvariable=self.repo_dir_var)
        repo_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(repo_frame, text="📁", width=3, command=self.browse_repo).pack(side='left')
        
        # Initialize button
        ttk.Button(config_frame, text="🚀 Initialize System", command=self.set_paths).pack(pady=10)
        
        # Profile and Control frame
        profile_control_frame = ttk.Frame(main_container, style="Root.TFrame")
        profile_control_frame.pack(fill='x', pady=(0, 15))
        
        # Profile section
        profile_frame = ttk.LabelFrame(profile_control_frame, text="Profile Management", padding=10, style="Card.TLabelframe")
        profile_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Label(profile_frame, text="Current Profile:").pack(side='left', padx=(0, 5))
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, 
                                         state='readonly', width=20)
        self.profile_combo.pack(side='left', padx=5)
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_changed)
        
        ttk.Button(profile_frame, text="➕ New", command=self.create_profile, width=8).pack(side='left', padx=5)
        
        # Quick action buttons
        action_frame = ttk.LabelFrame(profile_control_frame, text="Quick Actions", padding=10, style="Card.TLabelframe")
        action_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Button(action_frame, text="🔄 Refresh All", command=self.refresh_ui).pack(side='left', padx=5)
        ttk.Button(action_frame, text="🚫 Deactivate All", command=self.deactivate_all).pack(side='left', padx=5)
        
        # Main content area
        content_frame = ttk.Frame(main_container, style="Root.TFrame")
        content_frame.pack(fill='both', expand=True)
        
        # Available mods frame
        avail_frame = ttk.LabelFrame(content_frame, text="📂 Available Mods (Repository)")
        avail_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Available mods header with count
        self.avail_header = ttk.Label(avail_frame, text="Available (0)", style="Muted.TLabel")
        self.avail_header.pack(fill='x', padx=5, pady=(5, 0))
        
        self.avail_list = self.create_mod_listbox(avail_frame, bg="#11161E", fg="#E3E9F3", select_bg="#2F5EA5")
        self.avail_list.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar for available list
        avail_scroll = ttk.Scrollbar(avail_frame)
        avail_scroll.pack(side='right', fill='y')
        self.avail_list.config(yscrollcommand=avail_scroll.set)
        avail_scroll.config(command=self.avail_list.yview)
        
        # Control buttons frame
        ctrl_frame = ttk.Frame(content_frame, style="Root.TFrame")
        ctrl_frame.pack(side='left', fill='y', padx=10)
        
        # Styled buttons with icons
        self.create_styled_button(ctrl_frame, "→ Activate", self.success_color, 
                                 self.activate_selected, "▶").pack(pady=5, fill='x')
        self.create_styled_button(ctrl_frame, "← Deactivate", self.warning_color,
                                 self.deactivate_selected, "◀").pack(pady=5, fill='x')
        
        ttk.Separator(ctrl_frame, orient='horizontal').pack(fill='x', pady=10)
        
        self.create_styled_button(ctrl_frame, "Select All", self.accent_color,
                                 self.select_all_available, "✓").pack(pady=5, fill='x')
        self.create_styled_button(ctrl_frame, "Clear All", "#888888",
                                 self.clear_selection, "✗").pack(pady=5, fill='x')
        
        # Active mods frame
        active_frame = ttk.LabelFrame(content_frame, text="🎮 Active Mods (Game)")
        active_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        # Active mods header with count
        self.active_header = ttk.Label(active_frame, text="Active (0)", style="Muted.TLabel")
        self.active_header.pack(fill='x', padx=5, pady=(5, 0))
        
        self.active_list = self.create_mod_listbox(active_frame, bg="#102015", fg="#AAE8C4", select_bg="#227B4E")
        self.active_list.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar for active list
        active_scroll = ttk.Scrollbar(active_frame)
        active_scroll.pack(side='right', fill='y')
        self.active_list.config(yscrollcommand=active_scroll.set)
        active_scroll.config(command=self.active_list.yview)
        
        # Log area
        log_frame = ttk.LabelFrame(main_container, text="📋 Activity Log", padding=10)
        log_frame.pack(fill='x', pady=(15, 0))
        
        # Log text with scrollbar
        log_container = ttk.Frame(log_frame, style="Panel.TFrame")
        log_container.pack(fill='both', expand=True)
        
        self.log_text = tk.Text(log_container, height=6, wrap='word',
                               bg="#0F141C", fg=self.fg_color,
                               font=('Consolas', 9),
                               relief='flat',
                               insertbackground=self.fg_color,
                               highlightthickness=1,
                               highlightbackground=self.border_color)
        self.log_text.pack(side='left', fill='both', expand=True)
        
        log_scroll = ttk.Scrollbar(log_container)
        log_scroll.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scroll.set)
        log_scroll.config(command=self.log_text.yview)
        
        # Status bar
        self.status_frame = tk.Frame(
            main_container,
            bg=self.panel_color,
            highlightthickness=1,
            highlightbackground=self.border_color,
            padx=8,
            pady=6
        )
        self.status_frame.pack(fill='x', pady=(15, 0))
        
        self.status_icon = tk.Label(self.status_frame, text="●", fg="gray")
        self.status_icon.pack(side='left', padx=(0, 5))
        self.status_icon.configure(text="●", fg=self.muted_color, bg=self.panel_color, font=("Segoe UI", 11))
        
        self.status_var = tk.StringVar(value="Ready to initialize - Set your paths above")
        self.status_label = tk.Label(
            self.status_frame,
            textvariable=self.status_var,
            bg=self.panel_color,
            fg=self.fg_color,
            font=("Segoe UI", 9)
        )
        self.status_label.pack(side='left', fill='x', expand=True)
        
        # Progress bar (hidden by default)
        self.progress_var = tk.IntVar(value=0)
        self.progressbar = ttk.Progressbar(self.status_frame, variable=self.progress_var, maximum=100)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_container, style="Root.TFrame")
        bottom_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Button(bottom_frame, text="ℹ️ Help", command=self.show_help).pack(side='left', padx=5)
        ttk.Button(bottom_frame, text="⚙️ Settings", command=self.show_settings).pack(side='left', padx=5)
        ttk.Button(bottom_frame, text="💾 Save State", command=self.manual_save).pack(side='left', padx=5)
        ttk.Button(bottom_frame, text="❌ Exit", command=self.on_closing).pack(side='right', padx=5)
        
        # Bind events
        self.avail_list.bind('<Double-Button-1>', lambda e: self.activate_selected())
        self.active_list.bind('<Double-Button-1>', lambda e: self.deactivate_selected())
        self.normalize_ui_labels()

    def normalize_ui_labels(self):
        if hasattr(self, "status_icon"):
            self.status_icon.configure(text="\u25CF", fg=self.muted_color, bg=self.panel_color, font=("Segoe UI", 11))

        def visit(widget):
            for child in widget.winfo_children():
                visit(child)

            try:
                text = widget.cget("text")
            except tk.TclError:
                return

            if not isinstance(text, str) or not text:
                return

            normalized = self.clean_text(text)
            if "Initialize System" in text:
                normalized = "Initialize System"
            elif "Refresh All" in text:
                normalized = "Refresh"
            elif "Deactivate All" in text:
                normalized = "Deactivate All"
            elif "Save State" in text:
                normalized = "Save State"
            elif "Settings" in text:
                normalized = "Settings"
            elif "Help" in text:
                normalized = "Help"
            elif "Exit" in text:
                normalized = "Exit"
            elif "Available Mods" in text:
                normalized = "Available Mods (Repository)"
            elif "Active Mods" in text:
                normalized = "Active Mods (Game)"
            elif "Activity Log" in text:
                normalized = "Activity Log"
            elif "Activate" in text and "Deactivate" not in text:
                normalized = "Activate >>"
            elif "Deactivate" in text and "All" not in text:
                normalized = "<< Deactivate"
            elif "New" in text and "Profile" not in text:
                normalized = "New Profile"
            elif "Clear All" in text:
                normalized = "Clear Selection"
            elif text in ("ðŸ“",):
                normalized = "Browse"

            if normalized != text:
                widget.configure(text=normalized)

        visit(self)
    
    def create_mod_listbox(self, parent, bg, fg, select_bg):
        return tk.Listbox(
            parent,
            selectmode='extended',
            bg=bg,
            fg=fg,
            selectbackground=select_bg,
            selectforeground="#FFFFFF",
            activestyle='none',
            font=('Consolas', 10),
            relief='flat',
            highlightthickness=1,
            highlightbackground=self.border_color,
            borderwidth=0
        )

    def create_styled_button(self, parent, text, color, command, icon=None):
        """Create a styled button with custom colors"""
        frame = ttk.Frame(parent, style="Root.TFrame")

        btn_text = f"{icon} {text}" if icon else text

        btn = tk.Button(
            frame,
            text=btn_text,
            command=command,
            bg=color,
            fg="white",
            activeforeground="white",
            activebackground=self.darken_color(color),
            font=('Segoe UI Semibold', 10),
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2',
            bd=0
        )
        btn.pack(fill='x')
        
        # Hover effect
        btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.darken_color(color)))
        btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=color))
        
        return frame
    
    def darken_color(self, color):
        """Darken a hex color for hover effect"""
        if color.startswith("#") and len(color) == 7:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            r = max(0, r - 30)
            g = max(0, g - 30)
            b = max(0, b - 30)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color
    
    def update_status(self, message, type="info"):
        """Update status with color coding"""
        colors = {
            "info": self.accent_color,
            "success": self.success_color,
            "warning": self.warning_color,
            "error": self.error_color
        }
        self.status_icon.config(fg=colors.get(type, self.muted_color))
        self.status_var.set(self.clean_text(message))
    
    def log(self, message, level="info"):
        """Enhanced logging with color coding"""
        now = datetime.now().strftime("%H:%M:%S")
        message = self.clean_text(message)
        
        colors = {
            "info": self.fg_color,
            "success": self.success_color,
            "warning": self.warning_color,
            "error": self.error_color
        }
        
        color = colors.get(level, self.fg_color)
        
        self.log_text.insert('end', f"[{now}] ", "timestamp")
        self.log_text.insert('end', message + "\n", level)
        self.log_text.see('end')
        
        # Configure tags for colors
        self.log_text.tag_config("timestamp", foreground=self.muted_color)
        self.log_text.tag_config(level, foreground=color)
        
        self.update_status(message, level)

    def clean_text(self, text):
        if not isinstance(text, str):
            return text

        replacements = {
            "âœ“": "[OK]",
            "âœ—": "[X]",
            "â†’": "->",
            "â†": "<-",
            "â–¶": ">",
            "â—€": "<",
            "ðŸ“": "Browse",
            "ðŸš€": "",
            "ðŸ”„": "",
            "ðŸš«": "",
            "ðŸ“‚": "",
            "ðŸŽ®": "",
            "ðŸ“‹": "",
            "â„¹ï¸": "",
            "âš™ï¸": "",
            "ðŸ’¾": "",
            "âŒ": ""
        }
        normalized = "".join(ch for ch in text if ch == "\u25CF" or ord(ch) < 128)
        for bad, good in replacements.items():
            normalized = normalized.replace(bad, good)
        return normalized.strip()
    
    def browse_game(self):
        dir_path = filedialog.askdirectory(title="Select Game Folder")
        if dir_path:
            self.game_dir_var.set(dir_path)
            self.save_settings()
            self.log(f"Game folder set: {dir_path}", "info")
    
    def browse_repo(self):
        dir_path = filedialog.askdirectory(title="Select Mod Repository")
        if dir_path:
            self.repo_dir_var.set(dir_path)
            self.save_settings()
            self.log(f"Mod repository set: {dir_path}", "info")
    
    def try_initialize(self):
        game_dir = self.game_dir_var.get().strip()
        repo_dir = self.repo_dir_var.get().strip()
        
        if game_dir and repo_dir and Path(game_dir).exists() and Path(repo_dir).exists():
            self.set_paths()
    
    def set_paths(self):
        game_dir = self.game_dir_var.get().strip()
        repo_dir = self.repo_dir_var.get().strip()
        
        if not game_dir or not repo_dir:
            self.log("Error: Please set both Game Folder and Mod Repository paths", "error")
            messagebox.showerror("Error", "Please set both Game Folder and Mod Repository paths")
            return
        
        if not Path(game_dir).exists():
            self.log(f"Error: Game folder does not exist: {game_dir}", "error")
            messagebox.showerror("Error", f"Game folder does not exist:\n{game_dir}")
            return
        
        if not Path(repo_dir).exists():
            self.log(f"Error: Mod repository does not exist: {repo_dir}", "error")
            messagebox.showerror("Error", f"Mod repository does not exist:\n{repo_dir}")
            return
        
        try:
            self.mod_manager = TrackingModManager(game_dir, repo_dir, self.state_file)
            self.log(f"✓ System initialized: Game={game_dir}, Repo={repo_dir}", "success")
            self.refresh_ui()
        except Exception as e:
            self.log(f"✗ Failed to initialize: {str(e)}", "error")
            messagebox.showerror("Error", f"Failed to initialize: {str(e)}")
    
    def create_profile(self):
        if not self.mod_manager:
            self.log("Error: Please initialize system first", "error")
            messagebox.showerror("Error", "Please initialize system first")
            return
        
        profile_name = simpledialog.askstring("New Profile", "Enter profile name:")
        if not profile_name:
            return
        
        try:
            self.mod_manager.create_profile(profile_name)
            self.mod_manager.set_current_profile(profile_name)
            self.log(f"✓ Created profile: {profile_name}", "success")
            self.refresh_ui()
        except Exception as e:
            self.log(f"✗ Failed to create profile: {str(e)}", "error")
            messagebox.showerror("Error", f"Failed to create profile: {str(e)}")
    
    def on_profile_changed(self, event=None):
        if not self.mod_manager:
            return
        
        selected = self.profile_var.get()
        if selected:
            self.mod_manager.set_current_profile(selected)
            self.log(f"Switched to profile: {selected}", "info")
            self.refresh_lists()
    
    def refresh_ui(self):
        if not self.mod_manager:
            return
        
        # Show progress
        self.progressbar.pack(side='right', padx=(10, 0))
        self.progress_var.set(30)
        self.update()
        
        # Refresh profiles
        profiles = self.mod_manager.list_profiles()
        self.profile_combo['values'] = profiles
        
        current = self.mod_manager.get_current_profile()
        if current:
            self.profile_var.set(current)
        elif profiles:
            self.mod_manager.set_current_profile(profiles[0])
            self.profile_var.set(profiles[0])
        
        self.progress_var.set(60)
        self.update()
        
        # Refresh mod lists
        self.refresh_lists()
        
        self.progress_var.set(100)
        self.after(300, lambda: self.progressbar.pack_forget())  # Hide after delay
    
    def refresh_lists(self):
        if not self.mod_manager:
            return
        
        # Clear lists
        self.avail_list.delete(0, 'end')
        self.active_list.delete(0, 'end')
        
        # Populate available mods
        available = self.mod_manager.list_available_mods()
        for mod in available:
            self.avail_list.insert('end', mod)
        
        # Populate active mods
        active = self.mod_manager.list_active_mods()
        for mod in active:
            self.active_list.insert('end', mod)
        
        # Update headers with counts
        self.avail_header.config(text=f"Available ({len(available)})")
        self.active_header.config(text=f"Active ({len(active)})")
        
        current_profile = self.mod_manager.get_current_profile()
        self.log(f"✓ Refreshed - Profile: {current_profile} | Available: {len(available)} | Active: {len(active)}", "success")
    
    def select_all_available(self):
        self.avail_list.selection_set(0, tk.END)
    
    def clear_selection(self):
        self.avail_list.selection_clear(0, tk.END)
        self.active_list.selection_clear(0, tk.END)
    
    def activate_selected(self):
        if not self.mod_manager:
            self.log("Error: Please initialize system first", "error")
            return
        
        selections = self.avail_list.curselection()
        if not selections:
            self.log("Info: No mods selected to activate", "warning")
            messagebox.showinfo("No Selection", "Select mods from Available list to activate.")
            return
        
        mods_to_activate = [self.avail_list.get(i) for i in selections]
        
        # Show progress
        self.progressbar.pack(side='right', padx=(10, 0))
        
        def do_activation():
            total = len(mods_to_activate)
            for i, mod in enumerate(mods_to_activate):
                try:
                    success = self.mod_manager.activate_mod(mod)
                    self.progress_var.set(int((i + 1) / total * 100))
                    
                    if success:
                        self.after(0, lambda m=mod: self.log(f"✓ Activated: {m}", "success"))
                    else:
                        self.after(0, lambda m=mod: self.log(f"✗ Failed to activate: {m}", "warning"))
                except Exception as e:
                    self.after(0, lambda m=mod, err=str(e): self.log(f"✗ Error activating {m}: {err}", "error"))
            
            self.after(0, self.refresh_lists)
            self.after(0, lambda: self.progressbar.pack_forget())
        
        threading.Thread(target=do_activation, daemon=True).start()
    
    def deactivate_selected(self):
        if not self.mod_manager:
            self.log("Error: Please initialize system first", "error")
            return
        
        selections = self.active_list.curselection()
        if not selections:
            self.log("Info: No mods selected to deactivate", "warning")
            messagebox.showinfo("No Selection", "Select mods from Active list to deactivate.")
            return
        
        mods_to_deactivate = [self.active_list.get(i) for i in selections]
        
        # Show progress
        self.progressbar.pack(side='right', padx=(10, 0))
        
        def do_deactivation():
            total = len(mods_to_deactivate)
            for i, mod in enumerate(mods_to_deactivate):
                try:
                    success = self.mod_manager.deactivate_mod(mod)
                    self.progress_var.set(int((i + 1) / total * 100))
                    
                    if success:
                        self.after(0, lambda m=mod: self.log(f"✓ Deactivated: {m}", "success"))
                    else:
                        self.after(0, lambda m=mod: self.log(f"✗ Failed to deactivate: {m}", "warning"))
                except Exception as e:
                    self.after(0, lambda m=mod, err=str(e): self.log(f"✗ Error deactivating {m}: {err}", "error"))
            
            self.after(0, self.refresh_lists)
            self.after(0, lambda: self.progressbar.pack_forget())
        
        threading.Thread(target=do_deactivation, daemon=True).start()
    
    def deactivate_all(self):
        if not self.mod_manager:
            self.log("Error: Please initialize system first", "error")
            return
        
        if messagebox.askyesno("Deactivate All", "Deactivate ALL active mods? This will move all mod files back to repository."):
            # Show progress
            self.progressbar.pack(side='right', padx=(10, 0))
            
            def do_deactivate_all():
                try:
                    self.mod_manager.deactivate_all()
                    self.progress_var.set(100)
                    self.after(0, lambda: self.log("✓ Deactivated all mods", "success"))
                except Exception as e:
                    self.after(0, lambda err=str(e): self.log(f"✗ Error deactivating all: {err}", "error"))
                
                self.after(0, self.refresh_lists)
                self.after(0, lambda: self.progressbar.pack_forget())
            
            threading.Thread(target=do_deactivate_all, daemon=True).start()
    
    def manual_save(self):
        if self.mod_manager:
            try:
                self.mod_manager._save_state()
                self.log("✓ State saved successfully", "success")
            except Exception as e:
                self.log(f"✗ Error saving state: {str(e)}", "error")
        else:
            self.log("Warning: No manager to save", "warning")
    
    def show_help(self):
        help_text = """PRO MOD MANAGER - Quick Guide

1. SETUP:
   - Set Game Folder (where mod files go when active)
   - Set Mod Repository (where mod folders are stored)
   - Click 'Initialize System'

2. PROFILES:
   - Create profiles for different mod configurations
   - Switch between profiles to load different mod sets

3. MANAGING MODS:
   - Select mods from Available list (left)
   - Click '→ Activate' to move files to Game Folder
   - Active mods appear in right list
   - Click '← Deactivate' to move files back

4. FEATURES:
   - Double-click mods to activate/deactivate
   - Use 'Select All' for batch operations
   - 'Deactivate All' removes all mods at once
   - Activity log shows all operations

Note: This manager MOVES files, not copies them!
Active mods = Files in Game Folder
Available mods = Empty folders in Repository"""
        
        help_window = tk.Toplevel(self)
        help_window.title("Help Guide")
        help_window.geometry("600x500")
        help_window.configure(bg=self.panel_color)
        
        text_widget = tk.Text(help_window, wrap='word', padx=10, pady=10,
                             bg="#0F141C", fg=self.fg_color, insertbackground=self.fg_color, font=('Consolas', 10))
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')
        text_widget.pack(fill='both', expand=True)
        
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)
    
    def show_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.panel_color)
        
        ttk.Label(settings_window, text="Settings", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Auto-refresh setting
        auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_window, text="Auto-refresh after operations",
                       variable=auto_refresh_var).pack(anchor='w', padx=20, pady=5)
        
        # Log level setting
        ttk.Label(settings_window, text="Log Level:").pack(anchor='w', padx=20, pady=(10, 5))
        log_level_var = tk.StringVar(value="All")
        ttk.Combobox(settings_window, textvariable=log_level_var,
                    values=["All", "Errors Only", "Success Only"],
                    state='readonly').pack(fill='x', padx=20, pady=5)
        
        ttk.Separator(settings_window, orient='horizontal').pack(fill='x', pady=20)
        
        ttk.Button(settings_window, text="Save Settings",
                  command=lambda: self.log("Settings saved (demo)", "info")).pack(pady=10)
        ttk.Button(settings_window, text="Cancel",
                  command=settings_window.destroy).pack(pady=5)

    def on_closing(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?\nAll unsaved changes will be saved."):
            self.save_settings()
            if self.mod_manager:
                self.mod_manager._save_state()
            self.destroy()


def main():
    app = ProModSelectorUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
