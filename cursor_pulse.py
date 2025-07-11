import tkinter as tk
from tkinter import ttk, messagebox, Menu
import webbrowser
import pyautogui
import threading
import time
import ctypes
import keyboard
import win32con
import win32gui
import pystray
from PIL import Image, ImageDraw
from pynput import mouse
import json
import os
from pathlib import Path
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MouseHighlighter:
    def __init__(self):
        # Default values
        self.config = self.load_settings()  # Load saved settings or defaults

        self.setup_main_window()
        self.setup_tray_icon()
        self.setup_config_gui()
        self.setup_mouse_highlight()
        self.setup_menu()
        self.show_config_gui()
        # self.minimize_to_tray()

    def setup_main_window(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.protocol('WM_DELETE_WINDOW', self.hide_to_tray)
        # Set the application icon for the main window (influences taskbar)
        icon_path = resource_path("assets/CursorPulse.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        if os.name == 'nt':  # Only for Windows
            try:
                # Set AppUserModelID for consistent taskbar grouping and icon
                # You should use a unique ID for your application
                myappid = 'Njaka.CursorPulse.1.0' # Example: 'Njaka.CursorPulse.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except AttributeError:
                pass # Not available on older Windows versions or Wine

    def setup_menu(self):
        menubar = Menu(self.config_window)

        # File menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Settings", command=self.save_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_application)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="Website", command=lambda: webbrowser.open("http://www.example.com"))
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config_window.config(menu=menubar)

    def show_about(self):
        messagebox.showinfo("About", "Developer: Njaka ANDRIAMAHENINA\nVersion: 1.0.0")

    def setup_tray_icon(self):
        # Use a PNG for the tray icon, pystray handles resizing
        image_path = resource_path("assets/64.png") # Or "assets/128.png"
        image = Image.open(image_path)

        menu = (
            pystray.MenuItem('Show Config', self.show_config_gui),
            pystray.MenuItem('Exit', self.quit_application)
        )

        self.tray_icon = pystray.Icon(
            "mouse_highlighter",
            image,
            "Cursor Pulse",
            menu
        )

        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        """Hide the config window to system tray"""
        self.config_window.withdraw()

    def setup_config_gui(self):
        self.config_window = tk.Toplevel()
        self.config_window.title("Cursor Pulse v1.0.0")
        # Set the icon for the config window (top left of the window)
        icon_path = resource_path("assets/CursorPulse.ico")
        if os.path.exists(icon_path):
            self.config_window.iconbitmap(icon_path)

        # Set fixed window size
        window_width = 400
        window_height = 400
        self.config_window.geometry(f"{window_width}x{window_height}")
        self.config_window.resizable(False, False)

        # Center the window on screen
        screen_width = self.config_window.winfo_screenwidth()
        screen_height = self.config_window.winfo_screenheight()

        # Calculate position
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Set geometry with position
        self.config_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.config_window.protocol('WM_DELETE_WINDOW', self.hide_to_tray)
        self.config_window.withdraw()

        # Configure grid layout
        self.config_window.grid_columnconfigure(0, weight=1)
        self.config_window.grid_columnconfigure(1, weight=1)
        self.config_window.grid_columnconfigure(2, weight=1)

        # Base Radius
        ttk.Label(self.config_window, text="Base Radius:", anchor='w').grid(
            row=0, column=0, padx=5, pady=5, sticky='w')
        self.base_radius_var = tk.IntVar(value=self.config['BASE_RADIUS'])
        ttk.Scale(self.config_window, from_=10, to=50, variable=self.base_radius_var,
                  command=lambda v: self.update_radius_display('base'), orient='horizontal').grid(
            row=0, column=1, padx=5, pady=5, sticky='ew')
        self.base_radius_display = ttk.Label(self.config_window, text=str(self.config['BASE_RADIUS']))
        self.base_radius_display.grid(row=0, column=2, padx=5, pady=5, sticky='w')

        # Min Radius
        ttk.Label(self.config_window, text="Min Radius:", anchor='w').grid(
            row=1, column=0, padx=5, pady=5, sticky='w')
        self.min_radius_var = tk.IntVar(value=self.config['MIN_RADIUS'])
        ttk.Scale(self.config_window, from_=10, to=50, variable=self.min_radius_var,
                  command=lambda v: self.update_radius_display('min'), orient='horizontal').grid(
            row=1, column=1, padx=5, pady=5, sticky='ew')
        self.min_radius_display = ttk.Label(self.config_window, text=str(self.config['MIN_RADIUS']))
        self.min_radius_display.grid(row=1, column=2, padx=5, pady=5, sticky='w')

        # Animation Duration
        ttk.Label(self.config_window, text="Animation Duration (s):", anchor='w').grid(
            row=2, column=0, padx=5, pady=5, sticky='w')
        self.anim_dur_var = tk.DoubleVar(value=self.config['ANIMATION_DURATION'])
        ttk.Scale(self.config_window, from_=0, to=1, variable=self.anim_dur_var,
                  command=lambda v: self.update_radius_display('anim'), orient='horizontal').grid(
            row=2, column=1, padx=5, pady=5, sticky='ew')
        self.anim_dur_display = ttk.Label(self.config_window, text=f"{self.config['ANIMATION_DURATION']:.1f}")
        self.anim_dur_display.grid(row=2, column=2, padx=5, pady=5, sticky='w')

        # Drag Detect Delay
        ttk.Label(self.config_window, text="Drag Detect Delay (s):", anchor='w').grid(
            row=3, column=0, padx=5, pady=5, sticky='w')
        self.drag_delay_var = tk.DoubleVar(value=self.config['DRAG_DETECT_DELAY'])
        ttk.Scale(self.config_window, from_=0, to=1, variable=self.drag_delay_var,
                  command=lambda v: self.update_radius_display('drag'), orient='horizontal').grid(
            row=3, column=1, padx=5, pady=5, sticky='ew')
        self.drag_delay_display = ttk.Label(self.config_window, text=f"{self.config['DRAG_DETECT_DELAY']:.1f}")
        self.drag_delay_display.grid(row=3, column=2, padx=5, pady=5, sticky='w')

        # Hotkey
        ttk.Label(self.config_window, text="Toggle Hotkey:", anchor='w').grid(
            row=4, column=0, padx=5, pady=5, sticky='w')
        self.hotkey_var = tk.StringVar(value=self.config['TOGGLE_HOTKEY'])
        ttk.Entry(self.config_window, textvariable=self.hotkey_var).grid(
            row=4, column=1, columnspan=2, padx=5, pady=5, sticky='ew')

        # Color selection
        colors = ['green', 'red', 'yellow', 'blue', 'purple', 'orange']

        # Default Color
        ttk.Label(self.config_window, text="Default Color:", anchor='w').grid(
            row=5, column=0, padx=5, pady=5, sticky='w')
        self.default_color_var = tk.StringVar(value=self.config['DEFAULT_COLOR'])
        ttk.Combobox(self.config_window, textvariable=self.default_color_var,
                     values=colors).grid(row=5, column=1, columnspan=2, padx=5, pady=5, sticky='ew')

        # Left Click Color
        ttk.Label(self.config_window, text="Left Click Color:", anchor='w').grid(
            row=6, column=0, padx=5, pady=5, sticky='w')
        self.left_color_var = tk.StringVar(value=self.config['LEFT_CLICK_COLOR'])
        ttk.Combobox(self.config_window, textvariable=self.left_color_var,
                     values=colors).grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky='ew')

        # Right Click Color
        ttk.Label(self.config_window, text="Right Click Color:", anchor='w').grid(
            row=7, column=0, padx=5, pady=5, sticky='w')
        self.right_color_var = tk.StringVar(value=self.config['RIGHT_CLICK_COLOR'])
        ttk.Combobox(self.config_window, textvariable=self.right_color_var,
                     values=colors).grid(row=7, column=1, columnspan=2, padx=5, pady=5, sticky='ew')

        # Drag Color
        ttk.Label(self.config_window, text="Drag Color:", anchor='w').grid(
            row=8, column=0, padx=5, pady=5, sticky='w')
        self.drag_color_var = tk.StringVar(value=self.config['DRAG_COLOR'])
        ttk.Combobox(self.config_window, textvariable=self.drag_color_var,
                     values=colors).grid(row=8, column=1, columnspan=2, padx=5, pady=5, sticky='ew')

        # Save button
        ttk.Button(self.config_window, text="Save Settings", command=self.save_settings).grid(
            row=9, column=0, columnspan=3, padx=100, pady=10, sticky='ew')

        # Status Bar
        self.status_bar = ttk.Label(self.config_window, text="Developer: Njaka ANDRIAMAHENINA", relief=tk.GROOVE, anchor=tk.W)
        self.status_bar.grid(row=10, column=0, columnspan=3, sticky='ew', padx=0, pady=18)
        # ttk.Label(self.config_window, text="Developer: Njaka ANDRIAMAHENINA", anchor='w').grid(row=10, column=0, padx=5, pady=15, sticky='w')


    def update_radius_display(self, which):
        if which == 'base':
            value = int(self.base_radius_var.get())
            self.base_radius_display.config(text=str(value))
        elif which == 'min':
            value = int(self.min_radius_var.get())
            self.min_radius_display.config(text=str(value))
        elif which == 'anim':
            value = round(self.anim_dur_var.get(), 1)
            self.anim_dur_display.config(text=f"{value:.1f}")
        elif which == 'drag':
            value = round(self.drag_delay_var.get(), 1)
            self.drag_delay_display.config(text=f"{value:.1f}")

    def save_settings(self):
        self.config = {
            'BASE_RADIUS': int(self.base_radius_var.get()),
            'MIN_RADIUS': int(self.min_radius_var.get()),
            'DRAG_RADIUS': int(self.base_radius_var.get()) - 10,
            'DEFAULT_COLOR': self.default_color_var.get(),
            'LEFT_CLICK_COLOR': self.left_color_var.get(),
            'RIGHT_CLICK_COLOR': self.right_color_var.get(),
            'DRAG_COLOR': self.drag_color_var.get(),
            'ANIMATION_DURATION': round(self.anim_dur_var.get(), 1),
            'DRAG_DETECT_DELAY': round(self.drag_delay_var.get(), 1),
            'TOGGLE_HOTKEY': self.hotkey_var.get()
        }
        self.save_json_settings(self.config)
        messagebox.showinfo("Settings Saved", "Settings have been updated successfully!")
        # self.minimize_to_tray()

    def setup_mouse_highlight(self):
        self.highlight_window = tk.Toplevel()
        self.highlight_window.overrideredirect(True)
        self.highlight_window.attributes('-topmost', True)
        self.highlight_window.attributes('-disabled', True)
        self.highlight_window.configure(bg='black')
        self.highlight_window.wm_attributes('-transparentcolor', 'black')

        size = self.config['BASE_RADIUS'] * 2 + 30
        self.canvas = tk.Canvas(self.highlight_window, width=size, height=size, bg='black', highlightthickness=0)
        self.canvas.pack()

        self.current_color = self.config['DEFAULT_COLOR']
        self.is_dragging = False
        self.drag_timer = None
        self.enabled = True

        self.draw_circle(self.config['BASE_RADIUS'])

        # Window setup
        hwnd = self.highlight_window.winfo_id()
        self.make_window_transparent(hwnd)
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
        )

        # Start threads
        self.running = True
        threading.Thread(target=self.track_mouse, daemon=True).start()
        threading.Thread(target=self.listen_mouse_clicks, daemon=True).start()
        threading.Thread(target=self.listen_hotkey, daemon=True).start()

        self.highlight_window.after(100, self.reinforce_topmost)

    def make_window_transparent(self, hwnd):
        try:
            extended_style = (win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT |
                              win32con.WS_EX_TOPMOST | win32con.WS_EX_NOACTIVATE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style)
            win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 255, win32con.LWA_COLORKEY | win32con.LWA_ALPHA)
        except Exception as e:
            print(f"Window transparency error: {e}")

    def reinforce_topmost(self):
        if self.enabled:
            hwnd = self.highlight_window.winfo_id()
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )
        self.highlight_window.after(100, self.reinforce_topmost)

    def draw_circle(self, radius):
        self.canvas.delete('all')
        if not self.enabled:
            return
        size = self.config['BASE_RADIUS'] * 2 + 30
        center = size // 2
        self.canvas.create_oval(
            center - radius, center - radius,
            center + radius, center + radius,
            outline=self.current_color,
            width=4
        )

    def grow_animation(self, color='green'):
        # color = self.current_color
        if not self.enabled:
            return
        self.current_color = color
        steps = 10
        radius_list = [
            int(self.config['MIN_RADIUS'] + (self.config['BASE_RADIUS'] - self.config['MIN_RADIUS']) * i / steps)
            for i in range(0, steps + 1)
        ]
        for r in radius_list:
            self.draw_circle(r)
            time.sleep(self.config['ANIMATION_DURATION'] / steps)

        self.current_color = self.config['DEFAULT_COLOR'] if not self.is_dragging else self.config['DRAG_COLOR']
        self.draw_circle(self.config['BASE_RADIUS'] if not self.is_dragging else self.config['DRAG_RADIUS'])

    def start_drag_effect(self):
        if not self.enabled:
            return
        self.is_dragging = True
        self.current_color = self.config['DRAG_COLOR']
        self.draw_circle(self.config['DRAG_RADIUS'])

    def on_click(self, x, y, button, pressed):
        if not self.enabled:
            return
        if button.name == 'left':
            if pressed:
                self.drag_timer = threading.Timer(self.config['DRAG_DETECT_DELAY'], self.start_drag_effect)
                self.drag_timer.start()
            else:
                if self.drag_timer and self.drag_timer.is_alive():
                    self.drag_timer.cancel()
                    threading.Thread(target=self.grow_animation, args=(self.config['LEFT_CLICK_COLOR'],), daemon=True).start()
                else:
                    self.is_dragging = False
                    self.current_color = self.config['DEFAULT_COLOR']
                    threading.Thread(target=self.grow_animation, args=(self.config['DEFAULT_COLOR'],), daemon=True).start()
        elif button.name == 'right' and pressed:
            threading.Thread(target=self.grow_animation, args=(self.config['RIGHT_CLICK_COLOR'],), daemon=True).start()

    def listen_mouse_clicks(self):
        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()

    def listen_hotkey(self):
        while self.running:
            keyboard.wait(self.config['TOGGLE_HOTKEY'])
            self.enabled = not self.enabled
            self.canvas.delete('all')
            if not self.enabled:
                self.highlight_window.withdraw()
            else:
                self.highlight_window.deiconify()
                self.draw_circle(self.config['BASE_RADIUS'])

    def track_mouse(self):
        while self.running:
            if self.enabled:
                x, y = pyautogui.position()
                size = self.config['BASE_RADIUS'] * 2 + 30
                self.highlight_window.geometry(f'+{x - size // 2}+{y - size // 2}')
                self.highlight_window.lift()
            time.sleep(0.01)

    def show_config_gui(self, icon=None, item=None):
        self.config_window.deiconify()
        self.config_window.lift()

    def minimize_to_tray(self):
        self.config_window.withdraw()

    def quit_application(self, icon=None, item=None):
        self.running = False
        self.tray_icon.stop()
        self.root.quit()
        self.highlight_window.destroy()
        self.config_window.destroy()

    def get_settings_path(self):
        """Return platform-appropriate settings file path"""
        if os.name == 'nt':  # Windows
            config_dir = os.path.join(os.getenv('APPDATA'), 'MouseHighlighter')
        else:  # Linux/Mac
            config_dir = os.path.join(os.path.expanduser('~'), '.config', 'mouse_highlighter')

        Path(config_dir).mkdir(parents=True, exist_ok=True)
        return os.path.join(config_dir, 'settings.json')

    def save_json_settings(self, settings):
        """Save settings to JSON file"""
        settings_path = self.get_settings_path()
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)

    def load_settings(self):
        """Load settings from JSON file or return defaults"""
        settings_path = self.get_settings_path()
        print(settings_path)
        defaults = {
            'BASE_RADIUS': 50,
            'MIN_RADIUS': 10,
            'DEFAULT_COLOR': 'green',
            'LEFT_CLICK_COLOR': 'green',
            'RIGHT_CLICK_COLOR': 'red',
            'DRAG_COLOR': 'yellow',
            'ANIMATION_DURATION': 0.1,
            'DRAG_DETECT_DELAY': 0.25,
            'TOGGLE_HOTKEY': 'ctrl+shift+m'
        }

        try:
            with open(settings_path, 'r') as f:
                loaded = json.load(f)
                # Merge with defaults in case new settings were added later
                return {**defaults, **loaded}
        except (FileNotFoundError, json.JSONDecodeError):
            return defaults


if __name__ == "__main__":
    app = MouseHighlighter()
    app.root.mainloop()