import os
import json
import random
from tkinter import *
from tkinter import ttk, messagebox, simpledialog, filedialog
import time
import platform


#--- Configuration ---
DIFFICULTY = {
    "Easy": (1, 9),
    "Moderate": (10, 99),
    "Advanced": (100, 999),
    "Extreme": (100, 9999)
}
QUESTIONS_PER_QUIZ = 10
LEADERBOARD_FILE = "leaderboard.json"
PROFILES_FILE = "profiles.json"
ACHIEVEMENTS_DEF = [
    {"id": "speed_demon", "title": "Speed Demon", "desc": "Answer 10 questions under 30 seconds total"},
    {"id": "brain_master", "title": "Brain Master", "desc": "Score >= 90%"},
    {"id": "perfect_run", "title": "Perfect Run", "desc": "No wrong answers in a quiz"},
    {"id": "comeback", "title": "Comeback", "desc": "Get >=50% after initially falling below 30%"}
]

#--- Utilities for storage ---
def load_json_file(path, default):
    try:
        if not os.path.exists(path):
            return default
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def save_json_file(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed saving {path}: {e}")

#--- Leaderboard and profiles ---
leaderboard = load_json_file(LEADERBOARD_FILE, [])
profiles = load_json_file(PROFILES_FILE, {})  # dict: username -> profile data

#--- Sound helpers (safe) ---
def _bell_if_possible():
    try:
        root = Tk()
        if root:
            root.bell()
            root.destroy()
    except Exception:
        pass

if platform.system() == 'Windows':
    try:
        import winsound
        def play_sound_correct():
            try:
                winsound.MessageBeep(winsound.MB_OK)
            except Exception:
                _bell_if_possible()
        def play_sound_wrong():
            try:
                winsound.MessageBeep(winsound.MB_ICONHAND)
            except Exception:
                _bell_if_possible()
    except Exception:
        def play_sound_correct():
            pass
        def play_sound_wrong():
            pass
else:
    def play_sound_correct():
        pass
    def play_sound_wrong():
        pass

#--- App class ---
class EnhancedMathsQuizApp(Tk):
    def __init__(self):
        super().__init__()
        self.title('Enhanced Maths Quiz Application')
        # INCREASED SIZE
        self.geometry('1024x720')
        self.minsize(900, 600)

        #-------------------------
        #--- Theme / Styling -----
        #-------------------------
        self._THEME = {}
        PRIMARY_BG = "#0b1220"
        MAIN_BG = "#071025"
        SIDEBAR_BG = "#0f1724"
        CARD_BG = "#0f172a"
        TEXT_LIGHT = "#e6eef8"
        ACCENT = "#2b8ef6"
        ACCENT_HOVER = "#60a5fa"
        ENTRY_BG = "#071829"
        MUTED = "#93a4b8"

        self._THEME.update({
            "PRIMARY_BG": PRIMARY_BG,
            "MAIN_BG": MAIN_BG,
            "SIDEBAR_BG": SIDEBAR_BG,
            "CARD_BG": CARD_BG,
            "TEXT_LIGHT": TEXT_LIGHT,
            "ACCENT": ACCENT,
            "ACCENT_HOVER": ACCENT_HOVER,
            "ENTRY_BG": ENTRY_BG,
            "MUTED": MUTED
        })

        # --- STYLE UPDATES FOR BIGGER TEXT ---
        try:
            style = ttk.Style(self)
            style.theme_use("clam")
            
            # Bigger Buttons
            style.configure("TButton",
                            font=("Segoe UI", 12, "bold"),
                            padding=10,
                            foreground=TEXT_LIGHT,
                            background=ACCENT,
                            borderwidth=0)
            style.map("TButton",
                      background=[("active", ACCENT_HOVER), ("!active", ACCENT)])
            
            # Bigger Labels
            style.configure("TLabel",
                            background=MAIN_BG,
                            foreground=TEXT_LIGHT,
                            font=("Segoe UI", 14))
            
            style.configure("TFrame", background=MAIN_BG)
            
            # Bigger Combobox
            style.configure("TCombobox",
                            fieldbackground=ENTRY_BG,
                            background=ENTRY_BG,
                            foreground=TEXT_LIGHT,
                            arrowsize=20,
                            padding=5)
            
            # Bigger Treeview (Leaderboard)
            style.configure("Treeview",
                            background=ENTRY_BG,
                            foreground=TEXT_LIGHT,
                            fieldbackground=ENTRY_BG,
                            font=("Segoe UI", 12),
                            rowheight=35) # Taller rows
            
            style.configure("Treeview.Heading",
                            background=ACCENT,
                            foreground="white",
                            font=("Segoe UI", 13, "bold"),
                            padding=10)
                            
        except Exception:
            pass

        # Root-level defaults for classic widgets
        try:
            self.option_add("*Background", MAIN_BG)
            self.option_add("*Foreground", TEXT_LIGHT)
            # Global bigger font
            self.option_add("*Label.Font", ("Segoe UI", 14))
            self.option_add("*Button.Font", ("Segoe UI", 12, "bold"))
            self.option_add("*Entry.Font", ("Segoe UI", 14))
            self.option_add("*Listbox.Font", ("Segoe UI", 14))
            self.option_add("*Button.Background", ACCENT)
            self.option_add("*Button.Foreground", TEXT_LIGHT)
            self.option_add("*TearOff", False)
        except Exception:
            pass

        # -------------------------
        # state
        # -------------------------
        self.current_profile = None
        self.score = 0
        self.question_index = 0
        self.difficulty = 'Moderate'
        self.first_attempt = True
        self.current_problem = None
        self.timer_seconds = 15
        self.timer_remaining = 0
        self.timer_after_id = None
        self.quiz_start_time = None
        self.questions_attempted = []

        self.dark_mode = True
        self.bg_image = None

        # UI layout
        self.sidebar = Frame(self, width=240, bg=SIDEBAR_BG)
        self.sidebar.pack(side='left', fill='y')
        self.main_area = Frame(self, bg=MAIN_BG)
        self.main_area.pack(side='right', fill='both', expand=True)

        self._build_sidebar()
        self._build_main_frames()

        try:
            self._apply_theme_recursive(self)
        except Exception:
            pass

        self.show_frame('home')

    
    def _apply_theme_recursive(self, w):
        t = self._THEME
        for child in w.winfo_children():
            try:
                if isinstance(child, Frame):
                    if child is self.sidebar:
                        child.config(bg=t["SIDEBAR_BG"])
                    elif child is self.main_area:
                        child.config(bg=t["MAIN_BG"])
                    else:
                        try:
                            child.config(bg=t["CARD_BG"])
                        except Exception:
                            pass
                
                # Style Buttons mostly handled by ttk or option_add, 
                # but explicit config for hover effects on standard Buttons
                if isinstance(child, Button):
                    try:
                        child.config(bg=t["ACCENT"], fg=t["TEXT_LIGHT"], activebackground=t["ACCENT_HOVER"],
                                     relief='flat', bd=0, highlightthickness=0)
                        child.bind("<Enter>", lambda e, c=t["ACCENT_HOVER"]: e.widget.config(bg=c))
                        child.bind("<Leave>", lambda e, c=t["ACCENT"]: e.widget.config(bg=c))
                    except Exception:
                        pass
                
                if isinstance(child, Entry):
                    try:
                        child.config(bg=t["ENTRY_BG"], fg=t["TEXT_LIGHT"], insertbackground=t["TEXT_LIGHT"],
                                     relief='flat', bd=0)
                    except Exception:
                        pass
                
                if isinstance(child, Listbox):
                    try:
                        child.config(bg=t["ENTRY_BG"], fg=t["TEXT_LIGHT"], bd=0, highlightthickness=0)
                    except Exception:
                        pass

                self._apply_theme_recursive(child)
            except Exception:
                pass

    # ---------- UI: Sidebar ----------
    def _build_sidebar(self):
        # Bigger Logo
        logo = Label(self.sidebar, text='MathsQuiz', font=('Segoe UI', 26, 'bold'), bg='#0f1724', fg='#e6eef8')
        logo.pack(fill='x', pady=(20, 20), padx=15)

        buttons = [
            ('Home', 'home'),
            ('Instructions', 'instructions'),
            ('New Quiz', 'quiz_setup'),
            ('Profiles', 'profiles'),
            ('Leaderboard', 'leaderboard'),
            ('Settings', 'settings')
        ]
        
        # Spacer
        Frame(self.sidebar, bg='#0f1724', height=20).pack()

        for text, frame_key in buttons:
            # Bigger sidebar buttons
            b = Button(self.sidebar, text=text, font=('Segoe UI', 13), relief='flat',
                       bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"],
                       command=lambda k=frame_key: self.show_frame(k), height=2)
            b.pack(fill='x', padx=15, pady=8)

        self.profile_label = Label(self.sidebar, text='No profile', font=('Segoe UI', 11), 
                                   bg=self._THEME["SIDEBAR_BG"], fg=self._THEME["MUTED"])
        self.profile_label.pack(side='bottom', pady=20)

    # ---------- UI: Main frames ----------
    def _build_main_frames(self):
        self.frames = {}
        keys = ['home', 'instructions', 'quiz_setup', 'quiz', 'results', 'leaderboard', 'profiles', 'settings']
        for key in keys:
            frame = Frame(self.main_area, bg=self._THEME["MAIN_BG"])
            self.frames[key] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._populate_home()
        self._populate_instructions()
        self._populate_quiz_setup()
        self._populate_quiz()
        self._populate_results()
        self._populate_leaderboard()
        self._populate_profiles()
        self._populate_settings()

    def show_frame(self, key):
        if key not in self.frames:
            return
        
        # --- FIX: Kill timer if navigating away from quiz ---
        if key != 'quiz':
            if self.timer_after_id:
                try:
                    self.after_cancel(self.timer_after_id)
                except Exception:
                    pass
                self.timer_after_id = None
        # ---------------------------------------------------

        self.frames[key].lift()
        self.profile_label.config(text=f'User: {self.current_profile}' if self.current_profile else 'No profile')

    # ---------- Home ----------
    def _populate_home(self):
        f = self.frames['home']
        for w in f.winfo_children():
            w.destroy()
        
        # Centering Container
        container = Frame(f, bg=self._THEME["MAIN_BG"])
        container.pack(expand=True)

        Label(container, text='Welcome to MathsQuiz', font=('Segoe UI', 36, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=30)
        
        btn_width = 25
        Button(container, text='Instructions', width=btn_width, font=('Segoe UI', 14), bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('instructions')).pack(pady=10)
        Button(container, text='Start New Quiz', width=btn_width, font=('Segoe UI', 14), bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('quiz_setup')).pack(pady=10)
        Button(container, text='View Leaderboard', width=btn_width, font=('Segoe UI', 14), bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('leaderboard')).pack(pady=10)

    # ---------- Instructions ----------
    def _populate_instructions(self):
        f = self.frames['instructions']
        for w in f.winfo_children():
            w.destroy()
        
        container = Frame(f, bg=self._THEME["MAIN_BG"])
        container.pack(expand=True, fill='both', padx=40, pady=40)

        Label(container, text='Instructions', font=('Segoe UI', 32, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=(0, 20))
        
        instructions_text = (
            "1. Select a profile (optional) or create new.\n\n"
            "2. Choose a difficulty level (Easy / Moderate / Advanced / Extreme).\n\n"
            "3. Each quiz contains 10 questions.\n\n"
            "4. Only addition and subtraction questions will appear.\n\n"
            "5. You have limited time per question; answer before timer ends.\n\n"
            "6. Correct on first try: +10 points. Correct on second try: +5 points.\n\n"
            "7. View results, achievements, and leaderboard after quiz.\n"
        )
        Label(container, text=instructions_text, justify='left', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"], font=('Segoe UI', 14)).pack(anchor='center')
        
        Button(container, text='Back to Home', width=20, font=('Segoe UI', 12), bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('home')).pack(pady=30)

    # ---------- Quiz Setup ----------
    def _populate_quiz_setup(self):
        f = self.frames['quiz_setup']
        for w in f.winfo_children():
            w.destroy()
        
        container = Frame(f, bg=self._THEME["MAIN_BG"])
        container.pack(expand=True)

        Label(container, text='Quiz Setup', font=('Segoe UI', 32, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=30)

        pf = Frame(container, bg=self._THEME["MAIN_BG"])
        pf.pack(pady=10)
        
        # Profile
        Label(pf, text='Profile:', font=('Segoe UI', 16), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).grid(row=0, column=0, sticky='e', padx=10, pady=10)
        
        profiles_list = list(profiles.keys())
        self.profile_select = ttk.Combobox(pf, values=profiles_list if profiles_list else ['Anonymous'], state='normal', font=('Segoe UI', 14), width=20)
        self.profile_select.grid(row=0, column=1, padx=10, pady=10)
        
        if profiles_list:
            self.profile_select.set(profiles_list[0])
        elif self.current_profile:
             self.profile_select.set(self.current_profile)

        Button(pf, text='Manage', font=('Segoe UI', 10), bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('profiles')).grid(row=0, column=2, padx=10)

        # Difficulty
        Label(pf, text='Difficulty:', font=('Segoe UI', 16), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).grid(row=1, column=0, sticky='e', padx=10, pady=10)
        self.difficulty_combo = ttk.Combobox(pf, values=list(DIFFICULTY.keys()), state='readonly', font=('Segoe UI', 14), width=20)
        self.difficulty_combo.set(self.difficulty)
        self.difficulty_combo.grid(row=1, column=1, padx=10, pady=10)

        # Time
        Label(pf, text='Time per question (s):', font=('Segoe UI', 16), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).grid(row=2, column=0, sticky='e', padx=10, pady=10)
        self.time_spin = Spinbox(pf, from_=5, to=60, width=5, font=('Segoe UI', 14))
        self.time_spin.delete(0, 'end')
        self.time_spin.insert(0, str(self.timer_seconds))
        self.time_spin.grid(row=2, column=1, sticky='w', padx=10, pady=10)

        Button(container, text='Begin Quiz', width=20, font=('Segoe UI', 16, 'bold'), bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=self.begin_quiz).pack(pady=40)

    def begin_quiz(self):
        sel = self.profile_select.get().strip()
        
        if sel and sel in profiles:
            self.current_profile = sel
        else:
            if sel and sel != 'Anonymous':
                if sel not in profiles:
                    profiles[sel] = self._default_profile(sel)
                    save_json_file(PROFILES_FILE, profiles)
                    self._refresh_profile_widgets() 
                self.current_profile = sel
            else:
                self.current_profile = None

        self.difficulty = self.difficulty_combo.get() or self.difficulty
        try:
            self.timer_seconds = int(self.time_spin.get())
        except Exception:
            self.timer_seconds = 15

        self.score = 0
        self.question_index = 0
        self.questions_attempted = []
        self.quiz_start_time = time.time()
        self.show_frame('quiz')
        self._start_question()

    # ---------- Quiz screen ----------
    def _populate_quiz(self):
        f = self.frames['quiz']
        for w in f.winfo_children():
            w.destroy()
            
        # Top info bar
        top = Frame(f, bg=self._THEME["MAIN_BG"])
        top.pack(fill='x', pady=15, padx=20)
        
        self.quiz_info_label = Label(top, text='', font=('Segoe UI', 14), bg=self._THEME["MAIN_BG"], fg=self._THEME["MUTED"])
        self.quiz_info_label.pack(side='right')
        
        self.progress_label = Label(top, text='', font=('Segoe UI', 14, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["ACCENT"])
        self.progress_label.pack(side='left')

        # Center Content
        center = Frame(f, bg=self._THEME["MAIN_BG"])
        center.pack(expand=True)

        # HUGE Question
        self.question_label = Label(center, text='', font=('Segoe UI', 64, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"])
        self.question_label.pack(pady=(20, 40))
        
        # Big Answer Box
        self.answer_entry = Entry(center, font=('Segoe UI', 32), width=10, justify='center', 
                                  bg=self._THEME["ENTRY_BG"], fg=self._THEME["TEXT_LIGHT"], 
                                  insertbackground=self._THEME["TEXT_LIGHT"])
        self.answer_entry.pack(pady=(0, 30), ipady=10)
        
        # Buttons
        btn_frame = Frame(center, bg=self._THEME["MAIN_BG"])
        btn_frame.pack(pady=20)
        Button(btn_frame, text='Submit Answer', width=15, font=('Segoe UI', 14), bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=self.submit_answer).pack(side='left', padx=15)
        Button(btn_frame, text='Skip', width=10, font=('Segoe UI', 14), bg="#475569", fg=self._THEME["TEXT_LIGHT"], command=self.skip_question).pack(side='left', padx=15)

        # Timer at bottom
        bottom = Frame(f, bg=self._THEME["MAIN_BG"])
        bottom.pack(side='bottom', fill='x', pady=30)
        
        self.timer_label = Label(bottom, text='', font=('Segoe UI', 18, 'bold'), bg=self._THEME["MAIN_BG"], fg="#ef4444")
        self.timer_label.pack()

    def _random_numbers(self):
        min_v, max_v = DIFFICULTY.get(self.difficulty, (1, 99))
        return random.randint(min_v, max_v), random.randint(min_v, max_v)

    def _start_question(self):
        if self.timer_after_id:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

        if self.question_index >= QUESTIONS_PER_QUIZ:
            self._end_quiz()
            return

        n1, n2 = self._random_numbers()
        op = random.choice(['+', '-'])
        if op == '-' and n1 < n2:
            n1, n2 = n2, n1

        self.current_problem = (n1, n2, op)
        self.first_attempt = True

        if not hasattr(self, 'answer_entry') or not self.answer_entry.winfo_exists():
            self._populate_quiz()

        self.answer_entry.delete(0, 'end')
        self.question_label.config(text=f"{n1} {op} {n2} = ?")
        self.quiz_info_label.config(text=f"Diff: {self.difficulty}  |  User: {self.current_profile or 'Guest'}")
        self.progress_label.config(text=f"Q: {self.question_index+1}/{QUESTIONS_PER_QUIZ}   Score: {self.score}")
        
        # Focus entry
        self.answer_entry.focus_set()

        self.timer_remaining = self.timer_seconds
        self._tick_timer()

    def _tick_timer(self):
        self.timer_label.config(text=f"Time left: {self.timer_remaining}s")
        if self.timer_remaining <= 0:
            play_sound_wrong()
            messagebox.showinfo('Time up', 'Time is up for this question.')
            self._record_attempt(user_ans=None, time_taken=self.timer_seconds)
            self.question_index += 1
            self._start_question()
            return
        self.timer_remaining -= 1
        self.timer_after_id = self.after(1000, self._tick_timer)

    def _correct_answer(self):
        if not self.current_problem:
            return None
        n1, n2, op = self.current_problem
        return n1 + n2 if op == '+' else n1 - n2

    def submit_answer(self):
        entry = self.answer_entry.get().strip()
        try:
            user_ans = int(entry)
        except Exception:
            messagebox.showinfo('Invalid', 'Please enter an integer answer.')
            return

        correct = self._correct_answer()
        time_taken = int(time.time() - self.quiz_start_time) if self.quiz_start_time else 0 

        if user_ans == correct:
            points = 10 if self.first_attempt else 5
            self.score += points
            play_sound_correct()
            # Removed annoying popup for every correct answer to speed up flow, 
            # or keep it if preferred. Kept it as per original logic but maybe could be improved.
            messagebox.showinfo('Correct', f'Correct! +{points} points')
            self._record_attempt(user_ans, time_taken)
            self.question_index += 1
            self._start_question()
        else:
            if self.first_attempt:
                self.first_attempt = False
                play_sound_wrong()
                messagebox.showinfo('Incorrect', 'Incorrect — try again (fewer points if correct).')
                self.answer_entry.delete(0, 'end')
            else:
                play_sound_wrong()
                messagebox.showinfo('Incorrect', 'Incorrect — moving on.')
                self._record_attempt(user_ans, time_taken)
                self.question_index += 1
                self._start_question()

    def skip_question(self):
        self._record_attempt(user_ans=None, time_taken=None)
        self.question_index += 1
        self._start_question()

    def _record_attempt(self, user_ans, time_taken):
        if not self.current_problem:
            return
        n1, n2, op = self.current_problem
        correct = self._correct_answer()
        correct_bool = (user_ans == correct)
        qstr = f"{n1} {op} {n2}"
        self.questions_attempted.append((qstr, user_ans, correct, correct_bool, time_taken))

    # ---------- End quiz & results ----------
    def _end_quiz(self):
        if self.timer_after_id:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

        total_time = int(time.time() - self.quiz_start_time) if self.quiz_start_time else 0
        pct = (self.score / (QUESTIONS_PER_QUIZ * 10)) * 100 if QUESTIONS_PER_QUIZ > 0 else 0
        
        num_correct_first_try = sum(1 for q, u, c, b, t in self.questions_attempted if b and (u is not None) and (10 if self.first_attempt else 5) == 10)
        perfect = all(attempt[3] for attempt in self.questions_attempted) if self.questions_attempted else False
        
        earned = self._evaluate_achievements(perfect, total_time, pct)

        rec = {'name': self.current_profile or 'Guest', 'score': self.score, 'difficulty': self.difficulty, 'time': time.strftime('%Y-%m-%d %H:%M:%S')}
        leaderboard.append(rec)
        leaderboard.sort(key=lambda r: (-r['score'], r['time']))
        save_json_file(LEADERBOARD_FILE, leaderboard)

        self._populate_leaderboard()

        if self.current_profile:
            p = profiles.get(self.current_profile, self._default_profile(self.current_profile))
            p['last_score'] = self.score
            p['history'].append({'score': self.score, 'time': time.strftime('%Y-%m-%d %H:%M:%S')})
            for a in earned:
                if a not in p['achievements']:
                    p['achievements'].append(a)
            profiles[self.current_profile] = p
            save_json_file(PROFILES_FILE, profiles)

        self._populate_results(earned=earned, total_time=total_time)
        self.show_frame('results')

    def _populate_results(self, earned=None, total_time=0):
        f = self.frames['results']
        for w in f.winfo_children():
            w.destroy()
        
        container = Frame(f, bg=self._THEME["MAIN_BG"])
        container.pack(expand=True)

        Label(container, text='Quiz Complete', font=('Segoe UI', 32, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=20)
        Label(container, text=f'Final Score: {self.score} / {QUESTIONS_PER_QUIZ*10}', font=('Segoe UI', 24, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["ACCENT"]).pack(pady=10)
        Label(container, text=f'Total Time: {total_time} seconds', font=('Segoe UI', 16), bg=self._THEME["MAIN_BG"], fg=self._THEME["MUTED"]).pack(pady=10)

        if earned:
            Label(container, text='Achievements Unlocked!', font=('Segoe UI', 18, 'bold'), bg=self._THEME["MAIN_BG"], fg="#fbbf24").pack(pady=(20, 10))
            for aid in earned:
                a = next((x for x in ACHIEVEMENTS_DEF if x['id'] == aid), None)
                if a:
                    Label(container, text=f"• {a['title']}: {a['desc']}", font=('Segoe UI', 14), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(anchor='center', pady=2)
        
        Button(container, text='Home', width=20, font=('Segoe UI', 14), command=lambda: self.show_frame('home')).pack(pady=40)

    # ---------- Leaderboard ----------
    def _populate_leaderboard(self):
        f = self.frames['leaderboard']
        for w in f.winfo_children():
            w.destroy()
        
        Label(f, text='Leaderboard', font=('Segoe UI', 28, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=20)
        
        cols = ('Rank', 'Name', 'Score', 'Difficulty', 'When')
        # Treeview style already increased in __init__
        tree = ttk.Treeview(f, columns=cols, show='headings')
        
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor='center', width=150)
            
        tree.pack(fill='both', expand=True, padx=40, pady=20)
        
        for i, r in enumerate(leaderboard[:50], start=1):
            tree.insert('', 'end', values=(i, r.get('name'), r.get('score'), r.get('difficulty', '-'), r.get('time', '-')))
            
        Button(f, text='Back', width=15, font=('Segoe UI', 12), command=lambda: self.show_frame('home')).pack(pady=20)

    # ---------- Profiles ----------
    def _populate_profiles(self):
        f = self.frames['profiles']
        for w in f.winfo_children():
            w.destroy()
        
        Label(f, text='Profiles', font=('Segoe UI', 28, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=20)
        
        content = Frame(f, bg=self._THEME["MAIN_BG"])
        content.pack(fill='both', expand=True, padx=40, pady=10)

        left = Frame(content, bg=self._THEME["MAIN_BG"])
        left.pack(side='left', fill='y', padx=(0, 20))
        
        right = Frame(content, bg=self._THEME["MAIN_BG"])
        right.pack(side='right', fill='both', expand=True)

        self.profile_listbox = Listbox(left, height=15, width=25, bg=self._THEME["ENTRY_BG"], fg=self._THEME["TEXT_LIGHT"], bd=0, highlightthickness=0, font=('Segoe UI', 14))
        self.profile_listbox.pack(fill='y', expand=True)
        
        for name in profiles.keys():
            self.profile_listbox.insert('end', name)
            
        btn_grp = Frame(left, bg=self._THEME["MAIN_BG"])
        btn_grp.pack(pady=10)
        Button(btn_grp, text='New', command=self.create_profile).pack(side='left', padx=5)
        Button(btn_grp, text='Delete', command=self.delete_profile).pack(side='left', padx=5)

        self.profile_detail = Frame(right, bg='#0b1220', bd=1, relief='solid')
        self.profile_detail.pack(fill='both', expand=True)
        self.profile_listbox.bind('<<ListboxSelect>>', self._on_profile_select)

    def create_profile(self):
        name = simpledialog.askstring('New Profile', 'Enter a profile name (max 24 chars):')
        if not name:
            return
        name = name.strip()[:24]
        if name in profiles:
            messagebox.showinfo('Exists', 'Profile already exists.')
            return
        
        profiles[name] = self._default_profile(name)
        save_json_file(PROFILES_FILE, profiles)
        
        self._refresh_profile_widgets()
        self._populate_profiles()
        self._render_profile_detail(name)

    def delete_profile(self):
        sel = self.profile_listbox.curselection()
        if not sel:
            return
        name = self.profile_listbox.get(sel[0])
        if messagebox.askyesno('Confirm', f'Delete profile {name}?'):
            if name == self.current_profile:
                self.current_profile = None 

            profiles.pop(name, None)
            save_json_file(PROFILES_FILE, profiles)
            
            self._refresh_profile_widgets() 
            self._populate_profiles()

    def _on_profile_select(self, event):
        sel = event.widget.curselection()
        if not sel:
            return
        name = event.widget.get(sel[0])
        self._render_profile_detail(name)

    def _render_profile_detail(self, name):
        for w in self.profile_detail.winfo_children():
            w.destroy()
        p = profiles.get(name, self._default_profile(name))
        
        # Container inside detail view
        d_con = Frame(self.profile_detail, bg='#0b1220')
        d_con.pack(padx=30, pady=30, fill='both')

        Label(d_con, text=name, font=('Segoe UI', 28, 'bold'), bg='#0b1220', fg=self._THEME["TEXT_LIGHT"]).pack(pady=10, anchor='w')
        Label(d_con, text=f"Created: {p.get('created', '-')}", font=('Segoe UI', 14), bg='#0b1220', fg=self._THEME["MUTED"]).pack(anchor='w')
        Label(d_con, text=f"Last score: {p.get('last_score','-')}", font=('Segoe UI', 16), bg='#0b1220', fg=self._THEME["ACCENT"]).pack(pady=10, anchor='w')
        
        Label(d_con, text='Achievements:', font=('Segoe UI', 18, 'bold'), bg='#0b1220', fg=self._THEME["TEXT_LIGHT"]).pack(pady=(20, 10), anchor='w')
        
        if not p.get('achievements'):
            Label(d_con, text='None yet', font=('Segoe UI', 14), bg='#0b1220', fg=self._THEME["MUTED"]).pack(anchor='w')
        
        for aid in p.get('achievements', []):
            a = next((x for x in ACHIEVEMENTS_DEF if x['id'] == aid), None)
            if a:
                Label(d_con, text=f"• {a['title']}", font=('Segoe UI', 14), bg='#0b1220', fg=self._THEME["TEXT_LIGHT"]).pack(anchor='w', padx=10)

    def _default_profile(self, name):
        return {'name': name, 'created': time.strftime('%Y-%m-%d %H:%M:%S'), 'history': [], 'achievements': [], 'last_score': None}

    # ---------- Settings ----------
    def _populate_settings(self):
        f = self.frames['settings']
        for w in f.winfo_children():
            w.destroy()
        
        Label(f, text='Settings', font=('Segoe UI', 32, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=30)
        
        Button(f, text='Toggle Dark/Light Mode', width=25, font=('Segoe UI', 14), command=self._toggle_dark).pack(pady=15)
        Button(f, text='Clear Leaderboard Data', width=25, font=('Segoe UI', 14), command=self._clear_leaderboard).pack(pady=15)
        
        Button(f, text='Back', width=15, font=('Segoe UI', 12), command=lambda: self.show_frame('home')).pack(pady=40)

    def _refresh_profile_widgets(self):
        profiles_list = list(profiles.keys())
        
        if hasattr(self, 'profile_select') and self.profile_select.winfo_exists():
            current_state = self.profile_select['state']
            self.profile_select['state'] = 'normal'
            self.profile_select['values'] = profiles_list if profiles_list else ['Anonymous']
            if current_state == 'readonly':
                 self.profile_select['state'] = 'readonly'
            
            if self.current_profile and self.current_profile in profiles_list:
                self.profile_select.set(self.current_profile)
            elif profiles_list:
                self.profile_select.set(profiles_list[0])
            else:
                self.profile_select.set('Anonymous')

        if hasattr(self, 'profile_listbox') and self.profile_listbox.winfo_exists():
            self.profile_listbox.delete(0, 'end')
            for name in profiles_list:
                self.profile_listbox.insert('end', name)

            if hasattr(self, 'profile_detail'):
                for w in self.profile_detail.winfo_children():
                    w.destroy()

    def _toggle_dark(self):
        self.dark_mode = not self.dark_mode
        bg = '#0f1724' if self.dark_mode else '#f3f4f6'
        for k, fr in self.frames.items():
            try:
                fr.config(bg=bg)
            except Exception:
                pass

    def _clear_leaderboard(self):
        if messagebox.askyesno('Confirm', 'Clear the leaderboard?'):
            global leaderboard
            leaderboard = []
            save_json_file(LEADERBOARD_FILE, leaderboard)
            messagebox.showinfo('Cleared', 'Leaderboard cleared.')
            self._populate_leaderboard()

    # ---------- Achievements ----------
    def _evaluate_achievements(self, perfect, total_time, pct):
        earned = []
        if total_time and total_time <= 30:
            earned.append('speed_demon')
        if pct >= 90:
            earned.append('brain_master')
        if perfect:
            earned.append('perfect_run')
        
        if len(self.questions_attempted) >= 3:
            initial_score_points = sum(
                10 if a[3] and self.questions_attempted.index(a) < 1 else 5 if a[3] else 0 
                for a in self.questions_attempted[:3] if a[3] is not None
            )
            initial_pct = (initial_score_points / 30) * 100 if 30 > 0 else 0 
            
            if initial_pct < 30 and pct >= 50:
                 earned.append('comeback')
                 
        if self.current_profile:
            existing = set(profiles.get(self.current_profile, {}).get('achievements', []))
            new = [e for e in earned if e not in existing]
            return new
        return earned

if __name__ == '__main__':
    app = EnhancedMathsQuizApp()
    app.mainloop()