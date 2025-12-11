from tkinter import *
from tkinter import messagebox
import random
import os
import threading
import time

#Initialize sound system
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

#Color themes for Light/Dark mode
THEMES = {
    "light": {
        "bg": "#2d3436",
        "card": "#ffffff",
        "text": "#2d3436",
        "instr_bg": "#dfe6e9",
        "btn_tool_bg": "white",
        "btn_tool_text": "#636e72"
    },
    "dark": {
        "bg": "#1e272e",
        "card": "#2f3640",
        "text": "#f5f6fa",
        "instr_bg": "#353b48",
        "btn_tool_bg": "#353b48",
        "btn_tool_text": "#dcdde1"
    }
}

#App color palette
COLOR_HEADER = "#0984e3"
COLOR_ACCENT = "#e17055"
BTN_PRIMARY = "#0984e3"    
BTN_SUCCESS = "#00b894"    
BTN_WARNING = "#6c5ce7"    

class JokeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alexa Joke App")
        self.root.geometry("500x750") 
        
        self.jokes_list = []
        self.current_setup = ""
        self.current_punchline = ""
        self.using_backup = False
        self.is_dark_mode = True 
        
        #Animation state
        self.emoji_frames = [] 
        self.anim_id = None    

        #Determine script directory for asset loading
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        self.load_data()
        self.load_background()
        
        #Apply initial theme
        self.current_theme = THEMES["dark"]
        self.root.configure(bg=self.current_theme["bg"])

        #Main container
        self.card = Frame(root, bg=self.current_theme["card"], bd=0)
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=440, height=680)

        #Header bar
        self.header_frame = Frame(self.card, bg=COLOR_HEADER, height=70)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)

        self.lbl_title = Label(self.header_frame, text="🤖 ALEXA JOKES", font=("Segoe UI", 14, "bold"), bg=COLOR_HEADER, fg="white")
        self.lbl_title.pack(side="left", padx=20)

        #Theme toggle button
        self.btn_theme = Button(self.header_frame, text="☀️", command=self.toggle_theme, bg=COLOR_HEADER, fg="white", bd=0, font=("Segoe UI", 12), activebackground=COLOR_HEADER, activeforeground="white", cursor="hand2")
        self.btn_theme.pack(side="right", padx=20)

        #Instruction text
        status_text = f"Status: {len(self.jokes_list)} Jokes Ready"
        if self.using_backup: status_text += " (Backup Mode)"

        instruction_text = (
            "HOW TO USE:\n"
            "1. Click 'Alexa, tell me a joke'\n"
            "2. Read setup -> 3. Show Punchline\n"
            "4. Copy/Save -> 5. ☀️/🌙 Toggle Theme"
        )
        
        self.lbl_instructions = Label(
            self.card, 
            text=instruction_text, 
            font=("Segoe UI", 8), 
            justify="left", 
            bg=self.current_theme["instr_bg"], 
            fg=self.current_theme["text"], 
            padx=10, 
            pady=5, 
            width=50
        )
        self.lbl_instructions.pack(pady=10, padx=20)

        self.lbl_status = Label(self.card, text=status_text, font=("Segoe UI", 8, "italic"), bg=self.current_theme["card"], fg="#b2bec3")
        self.lbl_status.pack(pady=(0, 5))

        self.divider = Frame(self.card, height=1, bg="#b2bec3")
        self.divider.pack(fill="x", padx=30)

        #Joke display area
        self.content_frame = Frame(self.card, bg=self.current_theme["card"])
        self.content_frame.pack(expand=True, fill="both", padx=20, pady=5)

        self.lbl_setup = Label(self.content_frame, text="Welcome!\nTurn up your volume 🔊", font=("Segoe UI", 13, "bold"), bg=self.current_theme["card"], fg=self.current_theme["text"], wraplength=380, justify="center")
        self.lbl_setup.pack(pady=(10, 5))

        self.lbl_punchline = Label(self.content_frame, text="", font=("Segoe UI", 12, "italic"), bg=self.current_theme["card"], fg=COLOR_ACCENT, wraplength=380, justify="center")
        self.lbl_punchline.pack(pady=5)
        
        #Emoji label (hidden initially)
        self.lbl_emoji = Label(self.content_frame, bg=self.current_theme["card"], text="", fg="red")

        #Action buttons
        self.tools_frame = Frame(self.card, bg=self.current_theme["card"])
        self.tools_frame.pack(fill="x", pady=5)
        
        self.btn_copy = Button(self.tools_frame, text="📋 Copy", command=self.copy_to_clipboard, bg=self.current_theme["btn_tool_bg"], fg=self.current_theme["btn_tool_text"], relief="groove")
        self.btn_copy.pack(side="left", padx=(40, 10))
        
        self.btn_fav = Button(self.tools_frame, text="❤️ Save", command=self.save_favorite, bg=self.current_theme["btn_tool_bg"], fg=COLOR_ACCENT, relief="groove")
        self.btn_fav.pack(side="right", padx=(10, 40))

        #Navigation buttons
        self.controls_frame = Frame(self.card, bg=self.current_theme["card"])
        self.controls_frame.pack(side=BOTTOM, fill="x", pady=15, padx=30)

        btn_font = ("Segoe UI", 10, "bold")

        self.btn_alexa = Button(self.controls_frame, text="🗣️  Alexa, tell me a joke", command=self.get_joke, bg=BTN_PRIMARY, fg="white", font=btn_font, relief="flat", height=2)
        self.btn_alexa.pack(fill="x")

        self.btn_show_punch = Button(self.controls_frame, text="🎭  Show Punchline", command=self.show_punchline, bg=BTN_SUCCESS, fg="white", font=btn_font, relief="flat", height=2)
        
        self.btn_next = Button(self.controls_frame, text="➡️  Next Joke", command=self.get_joke, bg=BTN_WARNING, fg="white", font=btn_font, relief="flat", height=2)

        self.btn_quit = Button(self.card, text="❌ Quit", command=root.destroy, bg=self.current_theme["card"], fg="#b2bec3", relief="flat", bd=0)
        self.btn_quit.place(relx=0.5, rely=0.97, anchor="center")
        
        #Initialize animation
        self.load_gif()

    
    def get_asset_path(self, filename_list):
        possible_folders = [
            self.script_dir,
            os.path.join(self.script_dir, "assets"),
            os.path.join(self.script_dir, "Assessment 1 - Skills Portfolio", "02-RandomJokes", "assets")
        ]
        
        for folder in possible_folders:
            for name in filename_list:
                full_path = os.path.join(folder, name)
                if os.path.exists(full_path):
                    return full_path
        return None 

    def load_gif(self):
        
        gif_names = ["ezgif.com-webp-to-gif-converter.gif", "laugh.gif", "emoji.gif"]
        img_path = self.get_asset_path(gif_names)

        if not img_path:
            messagebox.showerror("Asset Error", "Could not find 'ezgif.com-webp-to-gif-converter.gif'.\nPlease put it in the same folder as this script.")
            return

        #Load frames for animation
        try:
            img_path = img_path.replace("\\", "/")
            i = 0
            while True:
                try:
                    frame = PhotoImage(file=img_path, format=f"gif -index {i}")
                    self.emoji_frames.append(frame)
                    i += 1
                except TclError:
                    break 
                except Exception:
                    break
            
            #Fallback: Load as static image if animation fails
            if len(self.emoji_frames) == 0:
                print("Animation load failed (0 frames). Attempting static load...")
                try:
                    static_frame = PhotoImage(file=img_path)
                    self.emoji_frames.append(static_frame)
                    print("Static image loaded successfully.")
                except Exception as e:
                    messagebox.showerror("Format Error", f"Found file but could not read it.\n\nTech Error: {e}\n\nMake sure it is a valid GIF.")
            else:
                print(f"Success! Loaded {len(self.emoji_frames)} frames.")

        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading GIF:\n{e}")

    def start_animation(self, frame_index=0):
        if not self.emoji_frames: 
            self.lbl_emoji.config(text="(Emoji Missing)", image="")
            return

        #Handle single-frame static images
        if len(self.emoji_frames) == 1:
             self.lbl_emoji.configure(image=self.emoji_frames[0], text="")
             return

        self.lbl_emoji.configure(image=self.emoji_frames[frame_index], text="")
        next_index = (frame_index + 1) % len(self.emoji_frames)
        self.anim_id = self.root.after(50, self.start_animation, next_index)

    def stop_animation(self):
        if self.anim_id:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None
        self.lbl_emoji.pack_forget()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        mode = "dark" if self.is_dark_mode else "light"
        colors = THEMES[mode]
        self.btn_theme.config(text="☀️" if self.is_dark_mode else "🌙")
        self.root.configure(bg=colors["bg"])
        self.card.configure(bg=colors["card"])
        self.lbl_instructions.configure(bg=colors["instr_bg"], fg=colors["text"])
        self.lbl_status.configure(bg=colors["card"])
        self.content_frame.configure(bg=colors["card"])
        self.lbl_setup.configure(bg=colors["card"], fg=colors["text"])
        self.lbl_punchline.configure(bg=colors["card"])
        self.lbl_emoji.configure(bg=colors["card"])
        self.tools_frame.configure(bg=colors["card"])
        self.btn_copy.configure(bg=colors["btn_tool_bg"], fg=colors["btn_tool_text"])
        self.btn_fav.configure(bg=colors["btn_tool_bg"])
        self.controls_frame.configure(bg=colors["card"])
        self.btn_quit.configure(bg=colors["card"])

    def load_background(self):
        bg_path = self.get_asset_path(["background.png", "bg.png"])
        if bg_path:
            try:
                bg_path = bg_path.replace("\\", "/") 
                self.bg_image = PhotoImage(file=bg_path)
                bg_label = Label(self.root, image=self.bg_image)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                bg_label.lower()
            except Exception:
                pass

    def load_data(self):
    
        txt_path = self.get_asset_path(["randomJokes.txt"])
        if not txt_path:
            self.using_backup = True
            self.jokes_list = [("Why did the developer quit? 💻?", "Because he didn't get arrays.")]
            return

        success = False
        try:
            with open(txt_path, "r", encoding="utf-8") as file:
                self.parse_jokes(file)
            if self.jokes_list: success = True
        except UnicodeDecodeError:
            try:
                with open(txt_path, "r", errors="ignore") as file:
                    self.parse_jokes(file)
                if self.jokes_list: success = True
            except: pass
        except: pass

        if not success:
            self.using_backup = True
            self.jokes_list = [("Backup Joke?", "The file failed to load.")]

    def parse_jokes(self, file):
        for line in file.readlines():
            if "?" in line:
                parts = line.strip().split("?", 1)
                if len(parts) == 2:
                    self.jokes_list.append((parts[0] + "?", parts[1]))

    def play_start_sound(self):
        if SOUND_AVAILABLE:
            def run():
                winsound.Beep(440, 100); winsound.Beep(554, 100); winsound.Beep(659, 150)
            threading.Thread(target=run, daemon=True).start()

    def play_laugh_sound(self):
        if SOUND_AVAILABLE:
            def run():
                sound_path = self.get_asset_path(["laugh.wav.wav", "laugh.wav"])
                if sound_path:
                    try:
                        winsound.PlaySound(sound_path, winsound.SND_FILENAME)
                    except Exception as e:
                        print(f"Audio error: {e}")
            threading.Thread(target=run, daemon=True).start()

    def copy_to_clipboard(self):
        if self.current_setup:
            self.root.clipboard_clear()
            self.root.clipboard_append(f"{self.current_setup}\n{self.current_punchline}")
            messagebox.showinfo("Copied", "Copied to clipboard!")

    def save_favorite(self):
        if self.current_setup:
            try:
                with open("favoriteJokes.txt", "a", encoding="utf-8") as f:
                    f.write(f"{self.current_setup} {self.current_punchline}\n")
                messagebox.showinfo("Saved", "Saved to favorites!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def get_joke(self):
        if not self.jokes_list: return
        self.stop_animation() 
        self.current_setup, self.current_punchline = random.choice(self.jokes_list)
        self.lbl_setup.config(text=self.current_setup)
        self.lbl_punchline.config(text="") 
        self.play_start_sound()
        self.btn_alexa.pack_forget()
        self.btn_next.pack_forget()
        self.btn_show_punch.pack(fill="x")

    def show_punchline(self):
        self.lbl_punchline.config(text=self.current_punchline)
        self.play_laugh_sound()
        
        #Display emoji and start animation
        self.lbl_emoji.pack(pady=5) 
        self.start_animation()
        
        self.btn_show_punch.pack_forget()
        self.btn_next.pack(fill="x")

if __name__ == "__main__":
    root = Tk()
    app = JokeApp(root)
    root.mainloop()