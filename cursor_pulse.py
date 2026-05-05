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
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MouseHighlighter:
    def __init__(self):
        self.config = self.load_settings()
        self.setup_main_window()

        self.enabled_var = tk.BooleanVar(value=self.config.get('HIGHLIGHTING_ENABLED', True))
        self.enabled = self.enabled_var.get()

        self.current_color = self.config['NORMAL_COLOR']
        self.current_radius = self.config['BASE_RADIUS']
        self.is_dragging = False
        self.drag_timer = None
        self.running = True

        self.scroll_arrow = None
        self.scroll_arrow_after_id = None

        self.setup_tray_icon()
        self.setup_config_gui()
        self.setup_mouse_highlight()
        self.setup_menu()          # menu now refers to config_window
        self.show_config_gui()

    def setup_main_window(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.protocol('WM_DELETE_WINDOW', self.hide_to_tray)
        icon_path = resource_path("assets/CursorPulse.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        if os.name == 'nt':
            try:
                myappid = 'Njaka.CursorPulse.1.5'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except AttributeError:
                pass

    def setup_menu(self):
        menubar = Menu(self.config_window)

        # File menu with Enable Highlighting checkbutton
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_checkbutton(label="Enable Highlighting", variable=self.enabled_var,
                                  command=lambda: self.toggle_highlighting(force_state=self.enabled_var.get()))
        file_menu.add_separator()
        file_menu.add_command(label="Save Settings", command=self.save_settings)
        file_menu.add_command(label="Restore Default Settings", command=self.restore_default_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_application)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu with How to use
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="Website", command=lambda: webbrowser.open("https://github.com/a6njaka/CursorPulse"))
        help_menu.add_command(label="How to use", command=self.show_howto)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config_window.config(menu=menubar)

    def show_about(self):
        messagebox.showinfo("About Cursor Pulse", "Developer: Njaka ANDRIAMAHENINA\nVersion: 1.5.0")

    def show_howto(self):
        howto_text = (
            "How to Use Cursor Pulse:\n\n"
            "• Right‑click the tray icon and select 'Show Config' to display the settings window.\n"
            "• Set a color to 'None' to disable the highlight effect for that specific action.\n"
            "• Use Ctrl+Shift+F12 to toggle the highlighting on/off (also reflected in File menu).\n"
            "• Adjust the sliders to change the base/min radius, animation duration, and drag delay.\n"
            "• Scroll up/down to see a directional arrow (color configurable).\n"
            "• Click the 'X' button to exit the application completely."
        )
        messagebox.showinfo("How to Use", howto_text)

    def setup_tray_icon(self):
        image_path = resource_path("assets/64.png")
        image = Image.open(image_path)
        menu = (pystray.MenuItem('Show Config', self.show_config_gui),)
        self.tray_icon = pystray.Icon("mouse_highlighter", image, "Cursor Pulse", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        """Used only for the root window (withdrawn) – not for config_window anymore."""
        pass  # root is always withdrawn

    def setup_config_gui(self):
        self.config_window = tk.Toplevel()
        self.config_window.title("Cursor Pulse v1.5.0")
        icon_path = resource_path("assets/CursorPulse.ico")
        if os.path.exists(icon_path):
            self.config_window.iconbitmap(icon_path)

        window_width = 450
        window_height = 450
        screen_width = self.config_window.winfo_screenwidth()
        screen_height = self.config_window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.config_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.config_window.resizable(False, False)
        # X button now quits the application
        self.config_window.protocol('WM_DELETE_WINDOW', self.quit_application)
        self.config_window.withdraw()

        self.config_window.grid_columnconfigure(0, weight=0)
        self.config_window.grid_columnconfigure(1, weight=1)
        self.config_window.grid_columnconfigure(2, weight=0)

        row = 0
        # Base Radius
        ttk.Label(self.config_window, text="Base Radius:", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        self.base_radius_var = tk.IntVar(value=self.config['BASE_RADIUS'])
        ttk.Scale(self.config_window, from_=10, to=50, variable=self.base_radius_var,
                  command=lambda v: self.update_radius_display('base'), orient='horizontal').grid(
            row=row, column=1, padx=5, pady=5, sticky='ew')
        self.base_radius_display = ttk.Label(self.config_window, text=str(self.config['BASE_RADIUS']))
        self.base_radius_display.grid(row=row, column=2, padx=5, pady=5, sticky='w')
        row += 1

        # Min Radius
        ttk.Label(self.config_window, text="Min Radius:", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        self.min_radius_var = tk.IntVar(value=self.config['MIN_RADIUS'])
        ttk.Scale(self.config_window, from_=10, to=50, variable=self.min_radius_var,
                  command=lambda v: self.update_radius_display('min'), orient='horizontal').grid(
            row=row, column=1, padx=5, pady=5, sticky='ew')
        self.min_radius_display = ttk.Label(self.config_window, text=str(self.config['MIN_RADIUS']))
        self.min_radius_display.grid(row=row, column=2, padx=5, pady=5, sticky='w')
        row += 1

        # Animation Duration
        ttk.Label(self.config_window, text="Animation Duration (s):", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        self.anim_dur_var = tk.DoubleVar(value=self.config['ANIMATION_DURATION'])
        ttk.Scale(self.config_window, from_=0, to=1, variable=self.anim_dur_var,
                  command=lambda v: self.update_radius_display('anim'), orient='horizontal').grid(
            row=row, column=1, padx=5, pady=5, sticky='ew')
        self.anim_dur_display = ttk.Label(self.config_window, text=f"{self.config['ANIMATION_DURATION']:.1f}")
        self.anim_dur_display.grid(row=row, column=2, padx=5, pady=5, sticky='w')
        row += 1

        # Drag Detect Delay
        ttk.Label(self.config_window, text="Drag Detect Delay (s):", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        self.drag_delay_var = tk.DoubleVar(value=self.config['DRAG_DETECT_DELAY'])
        ttk.Scale(self.config_window, from_=0, to=1, variable=self.drag_delay_var,
                  command=lambda v: self.update_radius_display('drag'), orient='horizontal').grid(
            row=row, column=1, padx=5, pady=5, sticky='ew')
        self.drag_delay_display = ttk.Label(self.config_window, text=f"{self.config['DRAG_DETECT_DELAY']:.1f}")
        self.drag_delay_display.grid(row=row, column=2, padx=5, pady=5, sticky='w')
        row += 1

        # Hotkey (fixed)
        ttk.Label(self.config_window, text="Toggle Hotkey:", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.config_window, text="Ctrl+Shift+F12", anchor='w').grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky='w')
        row += 1

        # Color lists in alphabetical order
        colors_display = [
            'Black', 'Blue', 'Cyan', 'Gray', 'Green', 'Magenta', 'Orange',
            'Pink', 'Purple', 'Red', 'White', 'Yellow'
        ]
        colors_none_display = ['None'] + colors_display

        # Normal Cursor Color
        ttk.Label(self.config_window, text="Normal Cursor Color:", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        self.normal_color_var = tk.StringVar(value=self.config['NORMAL_COLOR'])
        combo_normal = ttk.Combobox(self.config_window, textvariable=self.normal_color_var,
                                    values=colors_none_display, state='readonly')
        combo_normal.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
        self.normal_color_preview = tk.Canvas(self.config_window, width=20, height=20, highlightthickness=1, relief='solid')
        self.normal_color_preview.grid(row=row, column=2, padx=5, pady=5, sticky='w')
        self.normal_color_var.trace_add('write', lambda *a: self.update_color_preview('normal'))
        row += 1

        # Left Click Color
        ttk.Label(self.config_window, text="Left Click Color:", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        self.left_color_var = tk.StringVar(value=self.config['LEFT_CLICK_COLOR'])
        combo_left = ttk.Combobox(self.config_window, textvariable=self.left_color_var,
                                  values=colors_none_display, state='readonly')
        combo_left.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
        self.left_color_preview = tk.Canvas(self.config_window, width=20, height=20, highlightthickness=1, relief='solid')
        self.left_color_preview.grid(row=row, column=2, padx=5, pady=5, sticky='w')
        self.left_color_var.trace_add('write', lambda *a: self.update_color_preview('left'))
        row += 1

        # Right Click Color
        ttk.Label(self.config_window, text="Right Click Color:", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        self.right_color_var = tk.StringVar(value=self.config['RIGHT_CLICK_COLOR'])
        combo_right = ttk.Combobox(self.config_window, textvariable=self.right_color_var,
                                   values=colors_none_display, state='readonly')
        combo_right.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
        self.right_color_preview = tk.Canvas(self.config_window, width=20, height=20, highlightthickness=1, relief='solid')
        self.right_color_preview.grid(row=row, column=2, padx=5, pady=5, sticky='w')
        self.right_color_var.trace_add('write', lambda *a: self.update_color_preview('right'))
        row += 1

        # Drag Color
        ttk.Label(self.config_window, text="Drag Color:", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        self.drag_color_var = tk.StringVar(value=self.config['DRAG_COLOR'])
        combo_drag = ttk.Combobox(self.config_window, textvariable=self.drag_color_var,
                                  values=colors_none_display, state='readonly')
        combo_drag.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
        self.drag_color_preview = tk.Canvas(self.config_window, width=20, height=20, highlightthickness=1, relief='solid')
        self.drag_color_preview.grid(row=row, column=2, padx=5, pady=5, sticky='w')
        self.drag_color_var.trace_add('write', lambda *a: self.update_color_preview('drag'))
        row += 1

        # Scroll Color
        ttk.Label(self.config_window, text="Scroll Color:", anchor='w').grid(row=row, column=0, padx=5, pady=5, sticky='w')
        self.scroll_color_var = tk.StringVar(value=self.config.get('SCROLL_COLOR', 'Red'))
        combo_scroll = ttk.Combobox(self.config_window, textvariable=self.scroll_color_var,
                                    values=colors_none_display, state='readonly')
        combo_scroll.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
        self.scroll_color_preview = tk.Canvas(self.config_window, width=20, height=20, highlightthickness=1, relief='solid')
        self.scroll_color_preview.grid(row=row, column=2, padx=5, pady=5, sticky='w')
        self.scroll_color_var.trace_add('write', lambda *a: self.update_color_preview('scroll'))
        row += 1

        # Save button
        ttk.Button(self.config_window, text="Save Settings", command=self.save_settings).grid(
            row=row, column=0, columnspan=3, padx=100, pady=10, sticky='ew')
        row += 1

        self.status_bar = ttk.Label(self.config_window, text="Developer: Njaka ANDRIAMAHENINA",
                                    relief=tk.GROOVE, anchor=tk.W)
        self.status_bar.grid(row=row, column=0, columnspan=3, sticky='ew', padx=0, pady=18)

        self.update_color_preview('normal')
        self.update_color_preview('left')
        self.update_color_preview('right')
        self.update_color_preview('drag')
        self.update_color_preview('scroll')

    def update_color_preview(self, which):
        mapping = {
            'normal': (self.normal_color_var, self.normal_color_preview),
            'left':   (self.left_color_var,   self.left_color_preview),
            'right':  (self.right_color_var,  self.right_color_preview),
            'drag':   (self.drag_color_var,   self.drag_color_preview),
            'scroll': (self.scroll_color_var, self.scroll_color_preview)
        }
        var, canvas = mapping[which]
        display_name = var.get()
        fill = 'lightgray' if display_name == 'None' else display_name.lower()
        canvas.delete("all")
        canvas.create_rectangle(2, 2, 18, 18, fill=fill, outline='')

    def update_radius_display(self, which):
        if which == 'base':
            self.base_radius_display.config(text=str(int(self.base_radius_var.get())))
        elif which == 'min':
            self.min_radius_display.config(text=str(int(self.min_radius_var.get())))
        elif which == 'anim':
            self.anim_dur_display.config(text=f"{self.anim_dur_var.get():.1f}")
        elif which == 'drag':
            self.drag_delay_display.config(text=f"{self.drag_delay_var.get():.1f}")

    def restore_default_settings(self):
        if messagebox.askyesno("Restore Defaults", "Reset all settings to default values?"):
            self.config = {
                'BASE_RADIUS': 50,
                'MIN_RADIUS': 10,
                'DRAG_RADIUS': 50,
                'NORMAL_COLOR': 'Cyan',
                'LEFT_CLICK_COLOR': 'Cyan',
                'RIGHT_CLICK_COLOR': 'Red',
                'DRAG_COLOR': 'Yellow',
                'SCROLL_COLOR': 'Red',
                'ANIMATION_DURATION': 0.2,
                'DRAG_DETECT_DELAY': 0.25,
                'TOGGLE_HOTKEY': 'ctrl+shift+f12',
                'HIGHLIGHTING_ENABLED': self.enabled_var.get()
            }
            self.base_radius_var.set(self.config['BASE_RADIUS'])
            self.min_radius_var.set(self.config['MIN_RADIUS'])
            self.anim_dur_var.set(self.config['ANIMATION_DURATION'])
            self.drag_delay_var.set(self.config['DRAG_DETECT_DELAY'])
            self.normal_color_var.set(self.config['NORMAL_COLOR'])
            self.left_color_var.set(self.config['LEFT_CLICK_COLOR'])
            self.right_color_var.set(self.config['RIGHT_CLICK_COLOR'])
            self.drag_color_var.set(self.config['DRAG_COLOR'])
            self.scroll_color_var.set(self.config['SCROLL_COLOR'])
            self.update_radius_display('base')
            self.update_radius_display('min')
            self.update_radius_display('anim')
            self.update_radius_display('drag')
            self.save_json_settings(self.config)
            self.apply_normal_color()
            messagebox.showinfo("Settings", "Default settings restored.")

    def save_settings(self):
        self.config = {
            'BASE_RADIUS': int(self.base_radius_var.get()),
            'MIN_RADIUS': int(self.min_radius_var.get()),
            'DRAG_RADIUS': int(self.base_radius_var.get()),
            'NORMAL_COLOR': self.normal_color_var.get(),
            'LEFT_CLICK_COLOR': self.left_color_var.get(),
            'RIGHT_CLICK_COLOR': self.right_color_var.get(),
            'DRAG_COLOR': self.drag_color_var.get(),
            'SCROLL_COLOR': self.scroll_color_var.get(),
            'ANIMATION_DURATION': round(self.anim_dur_var.get(), 1),
            'DRAG_DETECT_DELAY': round(self.drag_delay_var.get(), 1),
            'TOGGLE_HOTKEY': 'ctrl+shift+f12',
            'HIGHLIGHTING_ENABLED': self.enabled_var.get()
        }
        self.save_json_settings(self.config)
        self.apply_normal_color()
        messagebox.showinfo("Settings Saved", "Settings have been updated successfully!")

    def apply_normal_color(self):
        if self.enabled and not self.is_dragging:
            self.current_color = self.config['NORMAL_COLOR']
            self.draw_circle(self.current_radius)

    def on_checkbox_toggle(self):
        """Not used anymore – left for compatibility."""
        pass

    def toggle_highlighting(self, force_state=None):
        if force_state is None:
            self.enabled = not self.enabled
        else:
            self.enabled = force_state
        self.enabled_var.set(self.enabled)
        if not self.enabled:
            self.canvas.delete('all')
            self.highlight_window.withdraw()
        else:
            self.highlight_window.deiconify()
            self.draw_circle(self.current_radius)

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

        self.draw_circle(self.current_radius)

        self.highlight_window.update_idletasks()
        hwnd = self.highlight_window.winfo_id()
        self.make_window_transparent(hwnd)

        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
        )

        threading.Thread(target=self.track_mouse, daemon=True).start()
        threading.Thread(target=self.listen_mouse_events, daemon=True).start()
        threading.Thread(target=self.listen_hotkey, daemon=True).start()

        self.highlight_window.after(100, self.reinforce_topmost)

    def make_window_transparent(self, hwnd):
        try:
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            new_style = ex_style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)
            win32gui.SetWindowPos(
                hwnd, None,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER |
                win32con.SWP_FRAMECHANGED | win32con.SWP_NOACTIVATE
            )
        except Exception as e:
            print(f"Window transparency error: {e}")

    def reinforce_topmost(self):
        if self.enabled:
            hwnd = self.highlight_window.winfo_id()
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )
        self.highlight_window.after(100, self.reinforce_topmost)

    def draw_circle(self, radius):
        self.canvas.delete('all')
        if not self.enabled:
            return
        self.current_radius = radius
        if self.current_color == 'None':
            return
        size = self.config['BASE_RADIUS'] * 2 + 30
        center = size // 2
        self.canvas.create_oval(
            center - radius, center - radius,
            center + radius, center + radius,
            outline=self.current_color.lower(),
            width=4
        )

    def grow_animation(self, color):
        if not self.enabled or color == 'None':
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

        if self.is_dragging:
            if self.config['DRAG_COLOR'] != 'None':
                self.current_color = self.config['DRAG_COLOR']
                self.draw_circle(self.config['DRAG_RADIUS'])
            else:
                self.current_color = self.config['NORMAL_COLOR']
                self.draw_circle(self.config['BASE_RADIUS'])
        else:
            self.current_color = self.config['NORMAL_COLOR']
            self.draw_circle(self.config['BASE_RADIUS'])

    def start_drag_effect(self):
        if not self.enabled or self.config['DRAG_COLOR'] == 'None':
            return
        self.is_dragging = True
        self.current_color = self.config['DRAG_COLOR']
        drag_radius = self.config.get('DRAG_RADIUS', self.config['BASE_RADIUS'])
        self.draw_circle(drag_radius)

    def on_click(self, x, y, button, pressed):
        if not self.enabled:
            return
        if button.name == 'left':
            if pressed:
                if self.config['DRAG_COLOR'] != 'None':
                    self.drag_timer = threading.Timer(self.config['DRAG_DETECT_DELAY'], self.start_drag_effect)
                    self.drag_timer.start()
            else:
                if self.drag_timer and self.drag_timer.is_alive():
                    self.drag_timer.cancel()
                    threading.Thread(target=self.grow_animation,
                                     args=(self.config['LEFT_CLICK_COLOR'],), daemon=True).start()
                else:
                    if self.is_dragging:
                        self.is_dragging = False
                        if self.config['DRAG_COLOR'] != 'None':
                            threading.Thread(target=self.grow_animation,
                                             args=(self.config['NORMAL_COLOR'],), daemon=True).start()
                        else:
                            self.current_color = self.config['NORMAL_COLOR']
                            self.draw_circle(self.config['BASE_RADIUS'])
                    else:
                        threading.Thread(target=self.grow_animation,
                                         args=(self.config['LEFT_CLICK_COLOR'],), daemon=True).start()
        elif button.name == 'right' and pressed:
            threading.Thread(target=self.grow_animation,
                             args=(self.config['RIGHT_CLICK_COLOR'],), daemon=True).start()

    def on_scroll(self, x, y, dx, dy):
        if not self.enabled:
            return
        if self.scroll_arrow_after_id:
            self.highlight_window.after_cancel(self.scroll_arrow_after_id)
            self.scroll_arrow_after_id = None

        if dy > 0:
            self.scroll_arrow = 'up'
        elif dy < 0:
            self.scroll_arrow = 'down'
        else:
            return

        size = self.config['BASE_RADIUS'] * 2 + 30
        center = size // 2

        self.canvas.delete('all')

        scroll_color = self.config.get('SCROLL_COLOR', 'Red')
        if scroll_color != 'None':
            arrow_color = scroll_color.lower()
            ss = 14
            if self.scroll_arrow == 'up':
                # arrow moved 48 pixels further up
                points = [
                    center, center - 36,              # tip
                    center - 18, center - 12,         # left
                    center + 18, center - 12          # right
                ]
            else:  # down arrow moved 59 pixels further down
                points = [
                    center, center + 36 + ss,              # tip
                    center - 18, center + 12 + ss,         # left
                    center + 18, center + 12 + ss         # right
                ]
            self.canvas.create_polygon(points, fill=arrow_color, outline=arrow_color)

        self.scroll_arrow_after_id = self.highlight_window.after(500, self.clear_scroll_arrow)

    def clear_scroll_arrow(self):
        self.scroll_arrow = None
        self.scroll_arrow_after_id = None
        if self.enabled:
            if self.is_dragging and self.config['DRAG_COLOR'] != 'None':
                self.current_color = self.config['DRAG_COLOR']
                self.draw_circle(self.config.get('DRAG_RADIUS', self.config['BASE_RADIUS']))
            else:
                self.current_color = self.config['NORMAL_COLOR']
                self.draw_circle(self.config['BASE_RADIUS'])

    def listen_mouse_events(self):
        with mouse.Listener(on_click=self.on_click, on_scroll=self.on_scroll) as listener:
            listener.join()

    def listen_hotkey(self):
        while self.running:
            keyboard.wait('ctrl+shift+f12')
            self.toggle_highlighting()

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

    def quit_application(self, icon=None, item=None):
        self.running = False
        self.tray_icon.stop()
        self.root.quit()
        self.highlight_window.destroy()
        self.config_window.destroy()

    def get_settings_path(self):
        if os.name == 'nt':
            config_dir = os.path.join(os.getenv('APPDATA'), 'MouseHighlighter')
        else:
            config_dir = os.path.join(os.path.expanduser('~'), '.config', 'mouse_highlighter')
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        return os.path.join(config_dir, 'settings.json')

    def save_json_settings(self, settings):
        settings_path = self.get_settings_path()
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)

    def load_settings(self):
        settings_path = self.get_settings_path()
        defaults = {
            'BASE_RADIUS': 50,
            'MIN_RADIUS': 10,
            'DRAG_RADIUS': 50,
            'NORMAL_COLOR': 'Cyan',
            'LEFT_CLICK_COLOR': 'Cyan',
            'RIGHT_CLICK_COLOR': 'Red',
            'DRAG_COLOR': 'Yellow',
            'SCROLL_COLOR': 'Red',
            'ANIMATION_DURATION': 0.2,
            'DRAG_DETECT_DELAY': 0.25,
            'TOGGLE_HOTKEY': 'ctrl+shift+f12',
            'HIGHLIGHTING_ENABLED': True
        }
        try:
            with open(settings_path, 'r') as f:
                loaded = json.load(f)
            return {**defaults, **loaded}
        except (FileNotFoundError, json.JSONDecodeError):
            return defaults


if __name__ == "__main__":
    app = MouseHighlighter()
    try:
        app.root.mainloop()
    except KeyboardInterrupt:
        app.quit_application()