from tkinter import *
from tkinter import messagebox
import random
import os
import threading

#Sound setup
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

#Themes
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

#Constant colors
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
        self.is_dark_mode = True  #Start in dark mode

        self.load_data()
        self.load_background()

        #UI Setup
        self.current_theme = THEMES["dark"]
        self.root.configure(bg=self.current_theme["bg"])

        #Main Card
        self.card = Frame(root, bg=self.current_theme["card"], bd=0)
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=440, height=680)

        #Header
        self.header_frame = Frame(self.card, bg=COLOR_HEADER, height=80)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)

        self.lbl_title = Label(self.header_frame, text="🤖 ALEXA JOKES", font=("Segoe UI", 16, "bold"), bg=COLOR_HEADER, fg="white")
        self.lbl_title.pack(side="left", padx=20)

        #Dark Mode Toggle
        self.btn_theme = Button(self.header_frame, text="☀️", command=self.toggle_theme, bg=COLOR_HEADER, fg="white", bd=0, font=("Segoe UI", 12), activebackground=COLOR_HEADER, activeforeground="white", cursor="hand2")
        self.btn_theme.pack(side="right", padx=20)

        #Instructions
        status_text = f"Status: {len(self.jokes_list)} Jokes Ready"
        if self.using_backup: status_text += " (Backup Mode)"

        instruction_text = (
            "HOW TO USE:\n"
            "1. Click 'Alexa, tell me a joke'\n"
            "2. Read the setup question\n"
            "3. Click 'Show Punchline'\n"
            "4. Use icons below to Copy or Save\n"
            "5. Click ☀️/🌙 to toggle Theme"
        )
        
        self.lbl_instructions = Label(
            self.card, 
            text=instruction_text, 
            font=("Segoe UI", 9), 
            justify="left", 
            bg=self.current_theme["instr_bg"], 
            fg=self.current_theme["text"], 
            padx=15, 
            pady=10, 
            width=50
        )
        self.lbl_instructions.pack(pady=15, padx=20)

        self.lbl_status = Label(self.card, text=status_text, font=("Segoe UI", 8, "italic"), bg=self.current_theme["card"], fg="#b2bec3")
        self.lbl_status.pack(pady=(0, 5))

        self.divider = Frame(self.card, height=1, bg="#b2bec3")
        self.divider.pack(fill="x", padx=30)

        #Content 
        self.content_frame = Frame(self.card, bg=self.current_theme["card"])
        self.content_frame.pack(expand=True, fill="both", padx=20, pady=5)

        self.lbl_setup = Label(self.content_frame, text="Welcome!\nTurn up your volume 🔊", font=("Segoe UI", 14, "bold"), bg=self.current_theme["card"], fg=self.current_theme["text"], wraplength=380, justify="center")
        self.lbl_setup.pack(pady=(20, 10))

        self.lbl_punchline = Label(self.content_frame, text="", font=("Segoe UI", 13, "italic"), bg=self.current_theme["card"], fg=COLOR_ACCENT, wraplength=380, justify="center")
        self.lbl_punchline.pack(pady=5)

        #Tools
        self.tools_frame = Frame(self.card, bg=self.current_theme["card"])
        self.tools_frame.pack(fill="x", pady=5)
        
        self.btn_copy = Button(self.tools_frame, text="📋 Copy", command=self.copy_to_clipboard, bg=self.current_theme["btn_tool_bg"], fg=self.current_theme["btn_tool_text"], relief="groove")
        self.btn_copy.pack(side="left", padx=(40, 10))
        
        self.btn_fav = Button(self.tools_frame, text="❤️ Save", command=self.save_favorite, bg=self.current_theme["btn_tool_bg"], fg=COLOR_ACCENT, relief="groove")
        self.btn_fav.pack(side="right", padx=(10, 40))

        #Controls
        self.controls_frame = Frame(self.card, bg=self.current_theme["card"])
        self.controls_frame.pack(side=BOTTOM, fill="x", pady=20, padx=30)

        btn_font = ("Segoe UI", 11, "bold")

        self.btn_alexa = Button(self.controls_frame, text="🗣️  Alexa, tell me a joke", command=self.get_joke, bg=BTN_PRIMARY, fg="white", font=btn_font, relief="flat", height=2)
        self.btn_alexa.pack(fill="x")

        self.btn_show_punch = Button(self.controls_frame, text="🎭  Show Punchline", command=self.show_punchline, bg=BTN_SUCCESS, fg="white", font=btn_font, relief="flat", height=2)
        
        self.btn_next = Button(self.controls_frame, text="➡️  Next Joke", command=self.get_joke, bg=BTN_WARNING, fg="white", font=btn_font, relief="flat", height=2)

        self.btn_quit = Button(self.card, text="❌ Quit", command=root.destroy, bg=self.current_theme["card"], fg="#b2bec3", relief="flat", bd=0)
        self.btn_quit.place(relx=0.5, rely=0.98, anchor="center")

    def toggle_theme(self):
        #Switch mode
        self.is_dark_mode = not self.is_dark_mode
        mode = "dark" if self.is_dark_mode else "light"
        colors = THEMES[mode]
        
        #Update Button Icon
        self.btn_theme.config(text="☀️" if self.is_dark_mode else "🌙")

        #Apply colors
        self.root.configure(bg=colors["bg"])
        self.card.configure(bg=colors["card"])
        self.lbl_instructions.configure(bg=colors["instr_bg"], fg=colors["text"])
        self.lbl_status.configure(bg=colors["card"])
        
        self.content_frame.configure(bg=colors["card"])
        self.lbl_setup.configure(bg=colors["card"], fg=colors["text"])
        self.lbl_punchline.configure(bg=colors["card"])
        
        self.tools_frame.configure(bg=colors["card"])
        self.btn_copy.configure(bg=colors["btn_tool_bg"], fg=colors["btn_tool_text"])
        self.btn_fav.configure(bg=colors["btn_tool_bg"])
        
        self.controls_frame.configure(bg=colors["card"])
        self.btn_quit.configure(bg=colors["card"])

    def load_background(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            img_path = os.path.join(script_dir, "c:\\Users\\Le\\OneDrive\\Documents\\background.png")
            self.bg_image = PhotoImage(file=img_path)
            bg_label = Label(self.root, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()
        except Exception:
            pass 

    def load_data(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, "randomJokes.txt")
        success = False

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                self.parse_jokes(file)
            if self.jokes_list: success = True
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", errors="ignore") as file:
                    self.parse_jokes(file)
                if self.jokes_list: success = True
            except: pass
        except: pass

        if not success:
            self.using_backup = True
            self.jokes_list = [
                ("Why did the developer quit? 💻?", "Because he didn't get arrays."),
                ("What is a ghost's favorite data type? 👻?", "Boolean."),
                ("Why do Java developers wear glasses? 👓?", "Because they don't C#."),
                ("Hardware: The part you kick. 🖥️?", "Software: The part you curse at."),
                ("Warning: File not working. ⚠️?", "Check file name and content.")
            ]
            messagebox.showwarning("Backup Mode", "Could not read randomJokes.txt. Using backup.")

    def parse_jokes(self, file):
        for line in file.readlines():
            if "?" in line:
                parts = line.strip().split("?", 1)
                if len(parts) == 2:
                    self.jokes_list.append((parts[0] + "?", parts[1]))

    #Sound Logic
    def play_start_sound(self):
        if SOUND_AVAILABLE:
            def run():
                winsound.Beep(440, 100); winsound.Beep(554, 100); winsound.Beep(659, 150)
            threading.Thread(target=run, daemon=True).start()

    def play_tada_sound(self):
        if SOUND_AVAILABLE:
            def run():
                winsound.Beep(523, 80); winsound.Beep(659, 80); winsound.Beep(784, 80); winsound.Beep(1046, 200)
            threading.Thread(target=run, daemon=True).start()

    #Features
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

    #Main Flow
    def get_joke(self):
        if not self.jokes_list: return
        self.current_setup, self.current_punchline = random.choice(self.jokes_list)
        self.lbl_setup.config(text=self.current_setup)
        self.lbl_punchline.config(text="") 
        self.play_start_sound()
        self.btn_alexa.pack_forget()
        self.btn_next.pack_forget()
        self.btn_show_punch.pack(fill="x")

    def show_punchline(self):
        self.lbl_punchline.config(text=self.current_punchline)
        self.play_tada_sound()
        self.btn_show_punch.pack_forget()
        self.btn_next.pack(fill="x")

if __name__ == "__main__":
    root = Tk()
    app = JokeApp(root)
    root.mainloop()