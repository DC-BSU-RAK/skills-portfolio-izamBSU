import os
import json
import random
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import time
import platform


# --- Configuration ---
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

# --- Utilities for storage ---
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

# --- Leaderboard and profiles ---
leaderboard = load_json_file(LEADERBOARD_FILE, [])
profiles = load_json_file(PROFILES_FILE, {})  # dict: username -> profile data

# --- Sound helpers (safe) ---
def _bell_if_possible():
    try:
        root = tk._get_default_root()
        if root:
            root.bell()
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
            _bell_if_possible()
        def play_sound_wrong():
            _bell_if_possible()
else:
    def play_sound_correct():
        _bell_if_possible()
    def play_sound_wrong():
        _bell_if_possible()

# --- App class ---
class EnhancedMathsQuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Enhanced Maths Quiz Application')
        self.geometry('900x600')
        self.minsize(800, 520)

        # -------------------------
        # --- Theme / Styling -----
        # -------------------------
        # Modern Dark Blue Professional Theme (Option 1)
        self._THEME = {}
        PRIMARY_BG = "#0b1220"     # Deep background
        MAIN_BG = "#071025"        # Main area backdrop
        SIDEBAR_BG = "#0f1724"     # Sidebar deep slate
        CARD_BG = "#0f172a"        # card-like panels
        TEXT_LIGHT = "#e6eef8"     # light text
        ACCENT = "#2b8ef6"         # professional blue
        ACCENT_HOVER = "#60a5fa"   # lighter hover blue
        ENTRY_BG = "#071829"       # input backgrounds
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

        # ttk style for themed widgets
        try:
            style = ttk.Style(self)
            # prefer clam for customizability
            style.theme_use("clam")
            style.configure("TButton",
                            font=("Segoe UI", 10),
                            padding=6,
                            foreground=TEXT_LIGHT,
                            background=ACCENT,
                            borderwidth=0)
            style.map("TButton",
                      background=[("active", ACCENT_HOVER), ("!active", ACCENT)])
            style.configure("TLabel",
                            background=MAIN_BG,
                            foreground=TEXT_LIGHT,
                            font=("Segoe UI", 11))
            style.configure("TFrame", background=MAIN_BG)
            style.configure("TCombobox",
                            fieldbackground=ENTRY_BG,
                            background=ENTRY_BG,
                            foreground=TEXT_LIGHT)
            style.configure("Treeview",
                            background=ENTRY_BG,
                            foreground=TEXT_LIGHT,
                            fieldbackground=ENTRY_BG,
                            font=("Segoe UI", 10))
            style.configure("Treeview.Heading",
                            background=ACCENT,
                            foreground="white",
                            font=("Segoe UI", 10, "bold"))
        except Exception:
            # If any style operation fails, continue silently (keeps logic intact)
            pass

        # Root-level defaults for classic widgets (tk.Button, tk.Label, etc.)
        try:
            # Many widgets set their own bg explicitly; option_add helps default the rest
            self.option_add("*Background", MAIN_BG)
            self.option_add("*Foreground", TEXT_LIGHT)
            self.option_add("*Label.Font", ("Segoe UI", 11))
            self.option_add("*Button.Font", ("Segoe UI", 10))
            self.option_add("*Entry.Font", ("Segoe UI", 11))
            # Button backgrounds via option_add (some platforms ignore this)
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
        self.questions_attempted = []  # (qstr, user_ans, correct, correct_bool, time_taken)

        # theme state
        self.dark_mode = True
        self.bg_image = None

        # UI layout
        self.sidebar = tk.Frame(self, width=200, bg=SIDEBAR_BG)
        self.sidebar.pack(side='left', fill='y')
        self.main_area = tk.Frame(self, bg=MAIN_BG)
        self.main_area.pack(side='right', fill='both', expand=True)

        # build UI
        self._build_sidebar()
        self._build_main_frames()

        # apply recursive theming to widgets created so far
        try:
            self._apply_theme_recursive(self)
        except Exception:
            # silent fallback — don't break behavior if theming hits an issue
            pass

        # start on home
        self.show_frame('home')

    # Helper: recursively apply theme to existing widgets (safe visual tweaks only)
    def _apply_theme_recursive(self, w):
        """
        Walks the widget tree and tweaks visual attributes for a consistent theme.
        This intentionally does not change widget types, commands, or logic.
        """
        t = self._THEME
        for child in w.winfo_children():
            try:
                cls = child.winfo_class()
                # Frames
                if isinstance(child, tk.Frame):
                    # keep sidebar distinct
                    if child is self.sidebar:
                        child.config(bg=t["SIDEBAR_BG"])
                    elif child is self.main_area:
                        child.config(bg=t["MAIN_BG"])
                    else:
                        # card-like panels: if background currently bright, convert to card bg
                        try:
                            child.config(bg=t["CARD_BG"])
                        except Exception:
                            pass
                # Labels
                if isinstance(child, tk.Label):
                    try:
                        child.config(bg=t["MAIN_BG"], fg=t["TEXT_LIGHT"])
                    except Exception:
                        pass
                # Buttons (tk.Button)
                if isinstance(child, tk.Button):
                    try:
                        child.config(bg=t["ACCENT"], fg=t["TEXT_LIGHT"], activebackground=t["ACCENT_HOVER"],
                                     relief='flat', bd=0, highlightthickness=0)
                        # hover
                        child.bind("<Enter>", lambda e, c=t["ACCENT_HOVER"]: e.widget.config(bg=c))
                        child.bind("<Leave>", lambda e, c=t["ACCENT"]: e.widget.config(bg=c))
                    except Exception:
                        pass
                # Entries
                if isinstance(child, tk.Entry):
                    try:
                        child.config(bg=t["ENTRY_BG"], fg=t["TEXT_LIGHT"], insertbackground=t["TEXT_LIGHT"],
                                     relief='flat', bd=0)
                    except Exception:
                        pass
                # Listbox
                if isinstance(child, tk.Listbox):
                    try:
                        child.config(bg=t["ENTRY_BG"], fg=t["TEXT_LIGHT"], bd=0, highlightthickness=0)
                    except Exception:
                        pass
                # Canvas
                if isinstance(child, tk.Canvas):
                    try:
                        child.config(bg=t["CARD_BG"], highlightthickness=0)
                    except Exception:
                        pass
                # Scrollbar
                if isinstance(child, tk.Scrollbar):
                    try:
                        child.config(bg=t["CARD_BG"], troughcolor=t["CARD_BG"])
                    except Exception:
                        pass
                # ttk widgets: rely on ttk.Style settings already applied
                # Recursively apply to children
                self._apply_theme_recursive(child)
            except Exception:
                # don't interrupt theming if a widget is unusual
                try:
                    self._apply_theme_recursive(child)
                except Exception:
                    pass

    # ---------- UI: Sidebar ----------
    def _build_sidebar(self):
        logo = tk.Label(self.sidebar, text='MathsQuiz', font=('Segoe UI', 18, 'bold'), bg='#0f1724', fg='#e6eef8')
        logo.pack(fill='x', pady=(12,8), padx=8)

        buttons = [
            ('Home', 'home'),
            ('Instructions', 'instructions'),
            ('New Quiz', 'quiz_setup'),
            ('Profiles', 'profiles'),
            ('Leaderboard', 'leaderboard'),
            ('Settings', 'settings')
        ]
        for text, frame_key in buttons:
            b = tk.Button(self.sidebar, text=text, font=('Segoe UI', 11), relief='flat',
                          bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"],
                          command=lambda k=frame_key: self.show_frame(k))
            b.pack(fill='x', padx=10, pady=6)

        self.profile_label = tk.Label(self.sidebar, text='No profile', bg=self._THEME["SIDEBAR_BG"], fg=self._THEME["TEXT_LIGHT"])
        self.profile_label.pack(side='bottom', pady=12)

    # ---------- UI: Main frames ----------
    def _build_main_frames(self):
        self.frames = {}
        keys = ['home', 'instructions', 'quiz_setup', 'quiz', 'results', 'leaderboard', 'profiles', 'settings']
        for key in keys:
            frame = tk.Frame(self.main_area, bg=self._THEME["MAIN_BG"])
            self.frames[key] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # populate each frame
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
        self.frames[key].lift()
        self.profile_label.config(text=f'User: {self.current_profile}' if self.current_profile else 'No profile')

    # ---------- Home ----------
    def _populate_home(self):
        f = self.frames['home']
        for w in f.winfo_children():
            w.destroy()
        tk.Label(f, text='Welcome to MathsQuiz', font=('Segoe UI', 20, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=16)
        tk.Button(f, text='Instructions', width=18, bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('instructions')).pack(pady=6)
        tk.Button(f, text='Start New Quiz', width=18, bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('quiz_setup')).pack(pady=6)
        tk.Button(f, text='View Leaderboard', width=18, bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('leaderboard')).pack(pady=6)

    # ---------- Instructions ----------
    def _populate_instructions(self):
        f = self.frames['instructions']
        for w in f.winfo_children():
            w.destroy()
        tk.Label(f, text='Instructions', font=('Segoe UI', 18, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=12)
        instructions_text = (
            "1. Select a profile (optional) or create new.\n"
            "2. Choose a difficulty level (Easy / Moderate / Advanced / Extreme).\n"
            "3. Each quiz contains 10 questions.\n"
            "4. Only addition and subtraction questions will appear.\n"
            "5. You have limited time per question; answer before timer ends.\n"
            "6. Correct on first try: +10 points. Correct on second try: +5 points.\n"
            "7. View results, achievements and export a PDF report at the end."
        )
        tk.Label(f, text=instructions_text, justify='left', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"], font=('Segoe UI', 12)).pack(padx=16, pady=8, anchor='w')
        tk.Button(f, text='Back to Home', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('home')).pack(pady=12)

    # ---------- Quiz Setup ----------
    def _populate_quiz_setup(self):
        f = self.frames['quiz_setup']
        for w in f.winfo_children():
            w.destroy()
        tk.Label(f, text='Quiz Setup', font=('Segoe UI', 16, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=12)

        pf = tk.Frame(f, bg=self._THEME["MAIN_BG"])
        pf.pack(pady=8)
        tk.Label(pf, text='Profile:', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).grid(row=0, column=0, sticky='e')
        profiles_list = list(profiles.keys())
        self.profile_select = ttk.Combobox(pf, values=profiles_list if profiles_list else ['Anonymous'], state='normal')
        self.profile_select.grid(row=0, column=1, padx=8)
        if profiles_list:
            self.profile_select.set(profiles_list[0])

        tk.Button(pf, text='Manage Profiles', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('profiles')).grid(row=0, column=2, padx=6)

        tk.Label(pf, text='Difficulty:', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).grid(row=1, column=0, sticky='e', pady=8)
        self.difficulty_combo = ttk.Combobox(pf, values=list(DIFFICULTY.keys()), state='readonly')
        self.difficulty_combo.set(self.difficulty)
        self.difficulty_combo.grid(row=1, column=1, padx=8)

        tk.Label(pf, text='Time per question (s):', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).grid(row=2, column=0, sticky='e')
        self.time_spin = tk.Spinbox(pf, from_=5, to=60, width=5)
        self.time_spin.delete(0, 'end')
        self.time_spin.insert(0, str(self.timer_seconds))
        self.time_spin.grid(row=2, column=1, sticky='w')

        tk.Button(f, text='Begin Quiz', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=self.begin_quiz).pack(pady=12)

    def begin_quiz(self):
        sel = self.profile_select.get().strip()
        if sel and sel in profiles:
            self.current_profile = sel
        else:
            if sel:
                if sel not in profiles:
                    profiles[sel] = self._default_profile(sel)
                    save_json_file(PROFILES_FILE, profiles)
                self.current_profile = sel
            else:
                self.current_profile = None

        self.difficulty = self.difficulty_combo.get() or self.difficulty
        try:
            self.timer_seconds = int(self.time_spin.get())
        except Exception:
            self.timer_seconds = 15

        # reset quiz state
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
        top = tk.Frame(f, bg=self._THEME["MAIN_BG"])
        top.pack(fill='x', pady=6)
        self.quiz_info_label = tk.Label(top, text='', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"])
        self.quiz_info_label.pack()
        self.question_label = tk.Label(f, text='', font=('Segoe UI', 28, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"])
        self.question_label.pack(pady=10)
        self.answer_entry = tk.Entry(f, font=('Segoe UI', 18), justify='center', bg=self._THEME["ENTRY_BG"], fg=self._THEME["TEXT_LIGHT"], insertbackground=self._THEME["TEXT_LIGHT"])
        self.answer_entry.pack()
        btn_frame = tk.Frame(f, bg=self._THEME["MAIN_BG"])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='Submit', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=self.submit_answer).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Skip', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=self.skip_question).pack(side='left', padx=6)
        bottom = tk.Frame(f, bg=self._THEME["MAIN_BG"])
        bottom.pack(side='bottom', fill='x', pady=8)
        self.progress_label = tk.Label(bottom, text='', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"])
        self.progress_label.pack()
        self.timer_label = tk.Label(bottom, text='', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"])
        self.timer_label.pack()

    def _random_numbers(self):
        min_v, max_v = DIFFICULTY.get(self.difficulty, (1, 99))
        return random.randint(min_v, max_v), random.randint(min_v, max_v)

    def _start_question(self):
        # cancel any previous timer
        if self.timer_after_id:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

        if self.question_index >= QUESTIONS_PER_QUIZ:
            self._end_quiz()
            return

        # generate only addition/subtraction
        n1, n2 = self._random_numbers()
        op = random.choice(['+', '-'])
        if op == '-' and n1 < n2:
            n1, n2 = n2, n1

        self.current_problem = (n1, n2, op)
        self.first_attempt = True

        # ensure UI exists
        if not hasattr(self, 'answer_entry') or not self.answer_entry.winfo_exists():
            self._populate_quiz()

        self.answer_entry.delete(0, 'end')
        self.question_label.config(text=f"{n1} {op} {n2} = ?")
        self.quiz_info_label.config(text=f"Profile: {self.current_profile or 'Guest'} — Difficulty: {self.difficulty}")
        self.progress_label.config(text=f"Question {self.question_index+1} / {QUESTIONS_PER_QUIZ}  |  Score: {self.score}")

        # start timer
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
            messagebox.showinfo('Correct', f'Correct! +{points} points')
            self._record_attempt(user_ans, time_taken)
            self.question_index += 1
            self._start_question()
        else:
            if self.first_attempt:
                self.first_attempt = False
                play_sound_wrong()
                messagebox.showinfo('Incorrect', 'Incorrect — try again (fewer points if correct).')
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
        # cancel timer
        if self.timer_after_id:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

        total_time = int(time.time() - self.quiz_start_time) if self.quiz_start_time else 0
        pct = (self.score / (QUESTIONS_PER_QUIZ * 10)) * 100 if QUESTIONS_PER_QUIZ > 0 else 0
        perfect = all(attempt[3] for attempt in self.questions_attempted) if self.questions_attempted else False
        earned = self._evaluate_achievements(perfect, total_time, pct)

        # save to leaderboard
        rec = {'name': self.current_profile or 'Guest', 'score': self.score, 'difficulty': self.difficulty, 'time': time.strftime('%Y-%m-%d %H:%M:%S')}
        leaderboard.append(rec)
        leaderboard.sort(key=lambda r: (-r['score'], r['time']))
        save_json_file(LEADERBOARD_FILE, leaderboard)

        if self.current_profile:
            p = profiles.get(self.current_profile, self._default_profile(self.current_profile))
            p['last_score'] = self.score
            p['history'].append({'score': self.score, 'time': time.strftime('%Y-%m-%d %H:%M:%S')})
            for a in earned:
                if a not in p['achievements']:
                    p['achievements'].append(a)
            profiles[self.current_profile] = p
            save_json_file(PROFILES_FILE, profiles)

        # show results frame
        self._populate_results(earned=earned, total_time=total_time)
        self.show_frame('results')

    def _populate_results(self, earned=None, total_time=0):
        f = self.frames['results']
        for w in f.winfo_children():
            w.destroy()
        tk.Label(f, text='Quiz Results', font=('Segoe UI', 18, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=8)
        tk.Label(f, text=f'Score: {self.score} / {QUESTIONS_PER_QUIZ*10}', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack()
        tk.Label(f, text=f'Time taken: {total_time} s', bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack()

        if earned:
            tk.Label(f, text='Achievements Unlocked:', font=('Segoe UI', 12, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=6)
            for aid in earned:
                a = next((x for x in ACHIEVEMENTS_DEF if x['id'] == aid), None)
                if a:
                    tk.Label(f, text=f"• {a['title']}: {a['desc']}", bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(anchor='w', padx=20)

    # ---------- Leaderboard ----------
    def _populate_leaderboard(self):
        f = self.frames['leaderboard']
        for w in f.winfo_children():
            w.destroy()
        tk.Label(f, text='Leaderboard', font=('Segoe UI', 16, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=8)
        cols = ('Rank', 'Name', 'Score', 'Difficulty', 'When')
        tree = ttk.Treeview(f, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor='center')
        tree.pack(fill='both', expand=True, padx=8, pady=8)
        for i, r in enumerate(leaderboard[:50], start=1):
            tree.insert('', 'end', values=(i, r.get('name'), r.get('score'), r.get('difficulty', '-'), r.get('time', '-')))
        tk.Button(f, text='Back', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=lambda: self.show_frame('home')).pack(pady=6)

    # ---------- Profiles ----------
    def _populate_profiles(self):
        f = self.frames['profiles']
        for w in f.winfo_children():
            w.destroy()
        tk.Label(f, text='Profiles', font=('Segoe UI', 16, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=8)
        left = tk.Frame(f, bg=self._THEME["MAIN_BG"])
        left.pack(side='left', fill='y', padx=12, pady=12)
        right = tk.Frame(f, bg=self._THEME["MAIN_BG"])
        right.pack(side='right', fill='both', expand=True, padx=12, pady=12)

        self.profile_listbox = tk.Listbox(left, height=15, bg=self._THEME["ENTRY_BG"], fg=self._THEME["TEXT_LIGHT"], bd=0, highlightthickness=0)
        self.profile_listbox.pack()
        for name in profiles.keys():
            self.profile_listbox.insert('end', name)
        tk.Button(left, text='New Profile', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=self.create_profile).pack(pady=6)
        tk.Button(left, text='Delete Profile', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=self.delete_profile).pack()

        self.profile_detail = tk.Frame(right, bg='#0b1220', bd=1, relief='solid')
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
        self._populate_profiles()

    def delete_profile(self):
        sel = self.profile_listbox.curselection()
        if not sel:
            return
        name = self.profile_listbox.get(sel[0])
        if messagebox.askyesno('Confirm', f'Delete profile {name}?'):
            profiles.pop(name, None)
            save_json_file(PROFILES_FILE, profiles)
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
        tk.Label(self.profile_detail, text=name, font=('Segoe UI', 14, 'bold'), bg='#0b1220', fg=self._THEME["TEXT_LIGHT"]).pack(pady=8)
        tk.Label(self.profile_detail, text=f"Last score: {p.get('last_score','-')}", bg='#0b1220', fg=self._THEME["TEXT_LIGHT"]).pack()
        tk.Label(self.profile_detail, text='Achievements:', bg='#0b1220', fg=self._THEME["TEXT_LIGHT"]).pack(pady=6)
        for aid in p.get('achievements', []):
            a = next((x for x in ACHIEVEMENTS_DEF if x['id'] == aid), None)
            if a:
                tk.Label(self.profile_detail, text=f"• {a['title']}", bg='#0b1220', fg=self._THEME["TEXT_LIGHT"]).pack(anchor='w', padx=12)

    def _default_profile(self, name):
        return {'name': name, 'created': time.strftime('%Y-%m-%d %H:%M:%S'), 'history': [], 'achievements': [], 'last_score': None}

    # ---------- Settings ----------
    def _populate_settings(self):
        f = self.frames['settings']
        for w in f.winfo_children():
            w.destroy()
        tk.Label(f, text='Settings', font=('Segoe UI', 16, 'bold'), bg=self._THEME["MAIN_BG"], fg=self._THEME["TEXT_LIGHT"]).pack(pady=8)
        tk.Button(f, text='Toggle Dark Mode', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=self._toggle_dark).pack(pady=6)
        tk.Button(f, text='Clear Leaderboard', bg=self._THEME["ACCENT"], fg=self._THEME["TEXT_LIGHT"], command=self._clear_leaderboard).pack(pady=6)

    def _toggle_dark(self):
        # Keep logic same; only toggle visual bg across frames
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
        first3 = self.questions_attempted[:3]
        first3_score = sum(1 for a in first3 if a[3])
        first3_pct = (first3_score / max(1, len(first3))) * 100
        if first3_pct < 30 and pct >= 50:
            earned.append('comeback')
        if self.current_profile:
            existing = set(profiles.get(self.current_profile, {}).get('achievements', []))
            new = [e for e in earned if e not in existing]
            return new
        return earned

# ---------- Run ----------
if __name__ == '__main__':
    app = EnhancedMathsQuizApp()
    app.mainloop()
