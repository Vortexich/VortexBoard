import os
import pygame
import keyboard
import random
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont
from threading import Thread
from PIL import Image, ImageTk, ImageDraw
import time

class ModernSoundKeyboardApp:
    def __init__(self, root):
        self.root = root
        
        try:
            self.root.iconbitmap('VortexBoard.ico')
        except Exception as e:
            print(f"Ошибка загрузки иконки: {e}")
        
        self.setup_app()
        self.init_audio()
        self.load_settings()
        self.create_widgets()
        self.start_keyboard_listener()
        self.apply_theme()
        self.setup_animations()

    def setup_app(self):
        """Настройка основного окна"""
        self.root.title("VortexBoard")
        self.root.geometry("500x400")
        self.root.minsize(400, 300)

        
        
        
        self.languages = {
            'en': {
                'title': "VortexBoard",
                'settings': "Settings",
                'theme': "Sound Theme:",
                'volume': "Volume:",
                'enable': "Enable sounds",
                'prevent_repeat': "Prevent key repeats",
                'appearance': "Appearance:",
                'light': "Light",
                'dark': "Dark",
                'open_folder': "Open themes folder",
                'add_theme': "Add theme",
                'status_ready': "Ready",
                'language': "Language:"
            },
            'ru': {
                'title': "VortexBoard",
                'settings': "Настройки",
                'theme': "Звуковая тема:",
                'volume': "Громкость:",
                'enable': "Включить звуки",
                'prevent_repeat': "Предотвращать повторения",
                'appearance': "Внешний вид:",
                'light': "Светлая",
                'dark': "Тёмная",
                'open_folder': "Открыть папку тем",
                'add_theme': "Добавить тему",
                'status_ready': "Готов",
                'language': "Язык:"
            }
        }
        
        self.settings = {
            'volume': 0.7,
            'enabled': True,
            'prevent_repeats': True,
            'current_theme': 'CherryMX Black - ABS keycaps',
            'language': 'en',
            'dark_mode': False
        }

    def setup_animations(self):
        self.animations = {
            'checkbutton': {
                'frames': [],
                'current_frame': 0,
                'playing': False
            }
        }
        
        for i in range(1, 11):
            color = "#4CAF50" if not self.settings['dark_mode'] else "#81C784"
            alpha = int(255 * (i / 10))
            img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, 15, 15], outline=color, width=1)
            if i > 1:
                fill_color = (*hex_to_rgb(color), alpha)
                draw.rectangle([3, 3, 12, 12], fill=fill_color)
            self.animations['checkbutton']['frames'].append(ImageTk.PhotoImage(img))

    def animate_checkbutton(self, widget, state):
        if state:
            frames = self.animations['checkbutton']['frames']
        else:
            frames = self.animations['checkbutton']['frames'][::-1]
            
        def update_frame(index=0):
            if index < len(frames):
                widget.configure(image=frames[index])
                self.root.after(20, update_frame, index+1)
            else:
                widget.configure(image='' if not state else frames[-1])
                
        update_frame()

    def load_themes(self):
        themes = {}
        base_dir = 'sound_packs'
        
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        # Стандартная тема
        default_path = os.path.join(base_dir, 'default')
        if not os.path.exists(default_path):
            os.makedirs(default_path)
            for sound in ['space.wav', 'delete.wav', 'key1.wav', 'key2.wav']:
                open(os.path.join(default_path, sound), 'a').close()
        
        themes['default'] = {'name': 'Default', 'path': default_path}
        
        for theme_name in os.listdir(base_dir):
            theme_path = os.path.join(base_dir, theme_name)
            if theme_name != 'default' and os.path.isdir(theme_path):
                themes[theme_name] = {'name': theme_name, 'path': theme_path}
        
        return themes

    def init_audio(self):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        self.active_keys = set()
        self.running = True
        self.themes = self.load_themes()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        lang_frame = ttk.Frame(main_frame)
        lang_frame.pack(anchor=tk.NE, padx=5, pady=5)
        
        ttk.Label(lang_frame, text=self.languages[self.settings['language']]['language']).pack(side=tk.LEFT)
        self.lang_combo = ttk.Combobox(lang_frame, values=['en', 'ru'], width=5)
        self.lang_combo.set(self.settings['language'])
        self.lang_combo.pack(side=tk.LEFT)
        self.lang_combo.bind('<<ComboboxSelected>>', self.change_language)
        
        self.settings_frame = ttk.LabelFrame(
            main_frame,
            text=self.languages[self.settings['language']]['settings'],
            padding=10
        )
        self.settings_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(self.settings_frame, 
                 text=self.languages[self.settings['language']]['theme']).grid(
                     row=0, column=0, sticky=tk.W, pady=5)
        
        self.theme_combo = ttk.Combobox(
            self.settings_frame, 
            values=list(self.themes.keys())
        )
        self.theme_combo.current(0)
        self.theme_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        ttk.Label(self.settings_frame, 
                 text=self.languages[self.settings['language']]['volume']).grid(
                     row=1, column=0, sticky=tk.W, pady=5)
        
        self.volume_scale = ttk.Scale(
            self.settings_frame, 
            from_=0, 
            to=100, 
            command=lambda v: self.update_volume(float(v)/100)
        )
        self.volume_scale.set(self.settings['volume'] * 100)
        self.volume_scale.grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        self.enable_var = tk.BooleanVar(value=self.settings['enabled'])
        self.enable_check = ttk.Checkbutton(
            self.settings_frame,
            text=self.languages[self.settings['language']]['enable'],
            variable=self.enable_var,
            command=lambda: [self.toggle_sounds(), self.animate_checkbutton(self.enable_check, self.enable_var.get())]
        )
        self.enable_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        self.repeat_var = tk.BooleanVar(value=self.settings['prevent_repeats'])
        self.repeat_check = ttk.Checkbutton(
            self.settings_frame,
            text=self.languages[self.settings['language']]['prevent_repeat'],
            variable=self.repeat_var,
            command=lambda: [self.toggle_repeat(), self.animate_checkbutton(self.repeat_check, self.repeat_var.get())]
        )
        self.repeat_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
          
        ttk.Label(self.settings_frame,
                 text=self.languages[self.settings['language']]['appearance']).grid(
                     row=4, column=0, sticky=tk.W, pady=5)
        
        self.appearance_combo = ttk.Combobox(
            self.settings_frame,
            values=[
                self.languages[self.settings['language']]['light'],
                self.languages[self.settings['language']]['dark']
            ]
        )
        self.appearance_combo.current(0 if not self.settings['dark_mode'] else 1)
        self.appearance_combo.grid(row=4, column=1, sticky=tk.EW, padx=5)
        self.appearance_combo.bind('<<ComboboxSelected>>', self.change_appearance)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.open_folder_btn = ttk.Button(
            btn_frame,
            text=self.languages[self.settings['language']]['open_folder'],
            command=self.open_themes_folder
        )
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        self.add_theme_btn = ttk.Button(
            btn_frame,
            text=self.languages[self.settings['language']]['add_theme'],
            command=self.add_theme
        )
        self.add_theme_btn.pack(side=tk.LEFT, padx=5)
        
        # Статус
        self.status_var = tk.StringVar(
            value=self.languages[self.settings['language']]['status_ready'])
        ttk.Label(main_frame, textvariable=self.status_var).pack(side=tk.BOTTOM)

    def update_ui_language(self):
        self.root.title(self.languages[self.settings['language']]['title'])
        
        self.settings_frame.config(text=self.languages[self.settings['language']]['settings'])
        
        for child in self.settings_frame.winfo_children():
            if isinstance(child, ttk.Label):
                text = child.cget('text')
                for key, value in self.languages[self.settings['language']].items():
                    if value == text:
                        child.config(text=self.languages[self.settings['language']][key])
                        break
        
        self.appearance_combo['values'] = [
            self.languages[self.settings['language']]['light'],
            self.languages[self.settings['language']]['dark']
        ]
        
        self.open_folder_btn.config(text=self.languages[self.settings['language']]['open_folder'])
        self.add_theme_btn.config(text=self.languages[self.settings['language']]['add_theme'])
        
        self.status_var.set(self.languages[self.settings['language']]['status_ready'])
        
        self.lang_combo.set(self.settings['language'])

    def change_language(self, event):
        self.settings['language'] = self.lang_combo.get()
        self.save_settings()
        self.update_ui_language()

    def apply_theme(self):
        style = ttk.Style()
        
        if self.settings['dark_mode']:
            bg = '#2d2d2d'
            fg = '#ffffff'
            accent = '#4CAF50'
            
            style.theme_use('clam')
            
            style.configure('.', 
                          background=bg, 
                          foreground=fg,
                          fieldbackground='#3d3d3d',
                          selectbackground=accent,
                          selectforeground=fg,
                          insertcolor=fg)
            
            style.configure('TFrame', background=bg)
            style.configure('TLabel', background=bg, foreground=fg)
            style.configure('TLabelframe', background=bg, foreground=fg)
            style.configure('TLabelframe.Label', background=bg, foreground=accent)
            
            style.configure('TButton', 
                          background='#3d3d3d',
                          foreground=fg,
                          bordercolor='#4d4d4d',
                          lightcolor='#3d3d3d',
                          darkcolor='#3d3d3d')
            style.map('TButton',
                    background=[('active', '#4d4d4d'), ('pressed', '#5d5d5d')])
            
            style.configure('TCheckbutton', 
                           background=bg,
                           foreground=fg,
                           indicatorbackground=bg,
                           indicatordiameter=15)
            style.map('TCheckbutton',
                     background=[('active', bg)],
                     foreground=[('active', fg)])
            
            style.configure('TCombobox',
                          fieldbackground='#3d3d3d',
                          background='#3d3d3d',
                          foreground=fg,
                          selectbackground=accent,
                          selectforeground=fg)
            
            style.configure('Horizontal.TScale',
                          background=bg,
                          troughcolor='#3d3d3d',
                          bordercolor=bg,
                          lightcolor=accent,
                          darkcolor=accent)
            
            self.root.config(bg=bg)
        else:
            bg = '#f5f5f5'
            fg = '#333333'
            accent = '#2196F3'
            
            style.theme_use('clam')
            
            style.configure('.', 
                          background=bg, 
                          foreground=fg,
                          fieldbackground='#ffffff',
                          selectbackground=accent,
                          selectforeground='#ffffff',
                          insertcolor=fg)
            
            style.configure('TFrame', background=bg)
            style.configure('TLabel', background=bg, foreground=fg)
            style.configure('TLabelframe', background=bg, foreground=fg)
            style.configure('TLabelframe.Label', background=bg, foreground=accent)
            
            style.configure('TButton', 
                          background='#e0e0e0',
                          foreground=fg,
                          bordercolor='#d0d0d0',
                          lightcolor='#e0e0e0',
                          darkcolor='#e0e0e0')
            style.map('TButton',
                    background=[('active', '#d0d0d0'), ('pressed', '#c0c0c0')])
            
            style.configure('TCheckbutton', 
                           background=bg,
                           foreground=fg,
                           indicatorbackground=bg,
                           indicatordiameter=15)
            style.map('TCheckbutton',
                     background=[('active', bg)],
                     foreground=[('active', fg)])
            
            style.configure('TCombobox',
                          fieldbackground='#ffffff',
                          background='#ffffff',
                          foreground=fg,
                          selectbackground=accent,
                          selectforeground='#ffffff')
            
            style.configure('Horizontal.TScale',
                          background=bg,
                          troughcolor='#e0e0e0',
                          bordercolor=bg,
                          lightcolor=accent,
                          darkcolor=accent)
            
            self.root.config(bg=bg)

    def start_keyboard_listener(self):
        keyboard.hook(self.on_key_event)
        self.thread = Thread(target=self.keyboard_loop, daemon=True)
        self.thread.start()

    def keyboard_loop(self):
        while self.running:
            keyboard.wait()

    def on_key_event(self, event):
        if not self.settings['enabled']:
            return
            
        if event.event_type == keyboard.KEY_DOWN:
            if self.settings['prevent_repeats'] and event.name in self.active_keys:
                return
                
            self.active_keys.add(event.name)
            self.play_sound(event.name)

        elif event.event_type == keyboard.KEY_UP:
            self.active_keys.discard(event.name)

    def play_sound(self, key):
        theme = self.themes.get(self.settings['current_theme'])
        if not theme:
            return
            
        if key == 'space':
            sound_file = 'space.wav'
        elif key == 'delete':
            sound_file = 'delete.wav'
        else:
            available = []
            for i in range(1, 3):
                if os.path.exists(f"{theme['path']}/key{i}.wav"):
                    available.append(f'key{i}.wav')
            
            if not available:
                return
                
            sound_file = random.choice(available)
        
        try:
            sound = pygame.mixer.Sound(f"{theme['path']}/{sound_file}")
            sound.set_volume(self.settings['volume'])
            sound.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
            self.status_var.set("Sound error")

    def change_appearance(self, event):
        lang = self.settings['language']
        is_dark = self.appearance_combo.get() == self.languages[lang]['dark']
        self.settings['dark_mode'] = is_dark
        self.save_settings()
        self.apply_theme()
        self.setup_animations()

    def change_theme(self, event):
        self.settings['current_theme'] = self.theme_combo.get()
        self.save_settings()

    def update_volume(self, volume):
        self.settings['volume'] = volume
        self.save_settings()

    def toggle_sounds(self):
        self.settings['enabled'] = self.enable_var.get()
        self.save_settings()

    def toggle_repeat(self):
        self.settings['prevent_repeats'] = self.repeat_var.get()
        self.save_settings()

    def open_themes_folder(self):
        try:
            os.startfile('sound_packs')
        except:
            messagebox.showerror("Error", "Could not open themes folder")

    def add_theme(self):
        folder = filedialog.askdirectory(title="Select Theme Folder")
        if folder:
            theme_name = os.path.basename(folder)
            dest = f'sound_packs/{theme_name}'
            
            if not os.path.exists(dest):
                os.makedirs(dest)
                # Копируем WAV-файлы
                for file in os.listdir(folder):
                    if file.lower().endswith('.wav'):
                        os.replace(
                            os.path.join(folder, file),
                            os.path.join(dest, file)
                        )
                
                self.themes[theme_name] = {'name': theme_name, 'path': dest}
                self.theme_combo['values'] = list(self.themes.keys())
                self.status_var.set(f"Theme {theme_name} added")
            else:
                messagebox.showerror("Error", "Theme already exists")

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                self.settings.update(json.load(f))
        except:
            pass

    def save_settings(self):
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)

    def on_closing(self):
        self.running = False
        self.save_settings()
        self.root.destroy()

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernSoundKeyboardApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
