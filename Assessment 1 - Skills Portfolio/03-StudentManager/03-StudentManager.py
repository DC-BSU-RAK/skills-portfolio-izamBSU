from tkinter import *
from tkinter import ttk, messagebox, simpledialog
import os
import sys

#--- PALETTE (PREMIUM DARK THEME) ---
COLORS = {
    'sidebar_bg': '#0f172a',      #Deep Navy
    'sidebar_hover': '#1e293b',   #Lighter Navy
    'accent': '#38bdf8',          #Neon Sky Blue
    'bg_fallback': '#f1f5f9',     #Light Grey Background
    'card_bg': '#1e293b',         #Dark Card Background
    'input_bg': '#334155',        #Input Field Background
    'text_light': '#f8fafc',      #White Text
    'text_sub': '#94a3b8',        #Grey Text
    'grade_A': '#34d399',         #Emerald
    'grade_B': '#38bdf8',         #Blue
    'grade_C': '#fbbf24',         #Amber
    'grade_D': '#94a3b8',         #Grey
    'grade_F': '#f87171',         #Red
}

FONTS = {
    'logo': ("Verdana", 19, "bold"),
    'nav': ("Segoe UI", 10),
    'h1': ("Segoe UI", 22, "bold"),
    'card_val': ("Segoe UI", 24, "bold"),
    'table_head': ("Segoe UI", 10, "bold"),
    'table_body': ("Segoe UI", 10)
}

class StudentManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Manager | Enterprise Edition")
        self.root.geometry("1280x800")
        self.root.configure(bg=COLORS['bg_fallback'])

        #Path Setup
        if getattr(sys, 'frozen', False):
            self.app_path = os.path.dirname(sys.executable)
        elif __file__:
            self.app_path = os.path.dirname(os.path.abspath(__file__))
        else:
            self.app_path = os.getcwd()
            
        self.filename = os.path.join(self.app_path, "studentMarks.txt")
        self.students = [] 

        self.setup_styles()
        self.create_interface()
        self.load_data()
        self.view_all_records()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        #Table Styles (Dark Mode)
        style.configure("Treeview", 
                        background=COLORS['card_bg'],
                        foreground=COLORS['text_light'],
                        fieldbackground=COLORS['card_bg'],
                        rowheight=45,               
                        font=FONTS['table_body'],
                        borderwidth=0)
        
        style.configure("Treeview.Heading", 
                        background="#334155",
                        foreground=COLORS['text_light'],
                        font=FONTS['table_head'],
                        relief="flat")
        
        style.map("Treeview", 
                  background=[('selected', COLORS['accent'])], 
                  foreground=[('selected', 'white')])

        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) 

    def create_interface(self):
        #--- Sidebar ---
        self.sidebar = Frame(self.root, bg=COLORS['sidebar_bg'], width=260)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        #Logo
        logo_frame = Frame(self.sidebar, bg=COLORS['sidebar_bg'], pady=40, padx=30)
        logo_frame.pack(fill=X)
        Label(logo_frame, text="UniManage", font=FONTS['logo'], fg="white", bg=COLORS['sidebar_bg'], anchor="w").pack(fill=X)
        Label(logo_frame, text="Enterprise System", font=("Segoe UI", 9), fg="#94a3b8", bg=COLORS['sidebar_bg'], anchor="w").pack(fill=X)

        #Navigation
        self.nav_frame = Frame(self.sidebar, bg=COLORS['sidebar_bg'])
        self.nav_frame.pack(fill=BOTH, expand=True, pady=20)

        self.add_nav_item("DASHBOARD", is_header=True)
        self.add_nav_item("Overview / All", self.view_all_records, icon="📊")
        self.add_nav_item("Find Student", self.find_student, icon="🔍")
        
        self.add_nav_item("ANALYTICS", is_header=True)
        self.add_nav_item("Top Performer", self.show_highest, icon="🏆")
        self.add_nav_item("Lowest Score", self.show_lowest, icon="📉")
        
        self.add_nav_item("MANAGEMENT", is_header=True)
        self.add_nav_item("Sort Records", self.sort_menu, icon="🔃")
        self.add_nav_item("Add Student", self.add_student_window, icon="➕")
        self.add_nav_item("Update", self.update_student_window, icon="✏️")
        self.add_nav_item("Delete", self.delete_student, icon="🗑️")

        #--- Main Area ---
        self.canvas = Canvas(self.root, bg=COLORS['bg_fallback'], highlightthickness=0)
        self.canvas.pack(side=RIGHT, fill=BOTH, expand=True)

        #Background Image
        bg_path = os.path.join(self.app_path, "c:\\Users\\Le\\OneDrive\\Documents\\CODELAB-2\\Blue Gradient Flow.png")
        if os.path.exists(bg_path):
            try:
                self.bg_photo = PhotoImage(file=bg_path)
                self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
            except: pass 

        #--- Floating Elements ---
        
        #1. Search Bar
        search_vis = Frame(self.canvas, bg=COLORS['card_bg'], padx=10, pady=2) 
        Label(search_vis, text="🔍", fg=COLORS['text_sub'], bg=COLORS['card_bg'], font=("Segoe UI", 10)).pack(side=LEFT)
        self.search_entry = Entry(search_vis, bg=COLORS['card_bg'], bd=0, fg=COLORS['text_light'], insertbackground="white", font=("Segoe UI", 9))
        self.search_entry.pack(side=LEFT, fill=X, expand=True, padx=5)
        self.search_entry.insert(0, "Search...")
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<Return>", self.run_quick_search)
        self.win_search = self.canvas.create_window(950, 20, window=search_vis, anchor="ne", width=220, height=35)

        #2. Stat Cards
        self.card1 = self.create_modern_card("Total Students", "👤", "0", COLORS['accent'])
        self.canvas.create_window(40, 65, window=self.card1, anchor="nw", width=280, height=100)

        self.card2 = self.create_modern_card("Class Average", "📊", "0%", COLORS['grade_A'])
        self.canvas.create_window(350, 65, window=self.card2, anchor="nw", width=280, height=100)

        self.card3 = self.create_modern_card("Top Grade", "🏆", "-", COLORS['grade_C']) 
        self.canvas.create_window(660, 65, window=self.card3, anchor="nw", width=280, height=100)

        #3. Table
        self.table_frame = Frame(self.canvas, bg=COLORS['card_bg'], padx=20, pady=20)
        Label(self.table_frame, text="Dashboard Overview", font=("Segoe UI", 14, "bold"), bg=COLORS['card_bg'], fg=COLORS['text_light']).pack(anchor="w", pady=(0, 15))

        columns = ("code", "name", "cw_total", "exam", "percent", "grade")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="browse")
        
        sb = ttk.Scrollbar(self.table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)

        headers = [("code", "ID", 80), ("name", "Student Name", 220), ("cw_total", "CW Total", 100), 
                   ("exam", "Exam", 100), ("percent", "Percentage", 120), ("grade", "Grade", 80)]
        for col, text, width in headers:
            self.tree.heading(col, text=text, anchor="w")
            self.tree.column(col, width=width, anchor="w")

        #Grade Color Tags
        self.tree.tag_configure('grade_A', foreground=COLORS['grade_A'], font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure('grade_B', foreground=COLORS['grade_B'], font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure('grade_C', foreground=COLORS['grade_C'], font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure('grade_D', foreground=COLORS['grade_D'], font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure('grade_F', foreground=COLORS['grade_F'], font=("Segoe UI", 10, "bold"))

        self.win_table = self.canvas.create_window(40, 190, window=self.table_frame, anchor="nw", width=900, height=530)

        self.canvas.bind('<Configure>', self.on_resize)

    def create_modern_card(self, title, icon, value, accent_color):
        card = Frame(self.canvas, bg=COLORS['card_bg'])
        strip = Frame(card, bg=accent_color, width=6)
        strip.pack(side=LEFT, fill=Y)
        content_f = Frame(card, bg=COLORS['card_bg'], padx=15, pady=15)
        content_f.pack(side=LEFT, fill=BOTH, expand=True)
        
        icon_f = Frame(content_f, bg=accent_color, width=45, height=45)
        icon_f.pack(side=LEFT, padx=(0, 15))
        icon_f.pack_propagate(False)
        Label(icon_f, text=icon, font=("Segoe UI", 18), bg=accent_color, fg="white").pack(expand=True)
        
        txt_f = Frame(content_f, bg=COLORS['card_bg'])
        txt_f.pack(side=LEFT, fill=Y, expand=True)
        Label(txt_f, text=title, font=COLORS['text_sub'], fg=COLORS['text_sub'], bg=COLORS['card_bg']).pack(anchor="w")
        val_lbl = Label(txt_f, text=value, font=FONTS['card_val'], fg=COLORS['text_light'], bg=COLORS['card_bg'])
        val_lbl.pack(anchor="w")
        
        if title == "Total Students": self.lbl_total = val_lbl
        if title == "Class Average": self.lbl_avg = val_lbl
        if title == "Top Grade": self.lbl_top = val_lbl
        return card

    def add_nav_item(self, text, command=None, icon="", is_header=False):
        if is_header:
            Label(self.nav_frame, text=text, font=("Segoe UI", 8, "bold"), fg="#475569", bg=COLORS['sidebar_bg'], anchor="w", padx=25).pack(fill=X, pady=(20, 5))
        else:
            btn = Button(self.nav_frame, text=f"  {icon}   {text}", command=command,
                            font=FONTS['nav'], bg=COLORS['sidebar_bg'], fg="#cbd5e1",
                            activebackground=COLORS['sidebar_hover'], activeforeground="white",
                            bd=0, anchor="w", padx=20, pady=10, cursor="hand2")
            btn.pack(fill=X)
            btn.bind("<Enter>", lambda e: btn.config(bg=COLORS['sidebar_hover'], fg="white"))
            btn.bind("<Leave>", lambda e: btn.config(bg=COLORS['sidebar_bg'], fg="#cbd5e1"))

    #--- Search ---
    def _on_search_focus_in(self, event):
        if self.search_entry.get() == "Search...":
            self.search_entry.delete(0, END)
            self.search_entry.config(fg=COLORS['text_light'])

    def _on_search_focus_out(self, event):
        if self.search_entry.get() == "":
            self.search_entry.insert(0, "Search...")
            self.search_entry.config(fg=COLORS['text_sub'])

    def run_quick_search(self, event=None):
        q = self.search_entry.get()
        if q and q != "Search...":
            res = [s for s in self.students if q.lower() in s['name'].lower() or q in str(s['code'])]
            if res: self.refresh_tree(res)
            else: messagebox.showinfo("Search Info", "No matches found.")
        else:
            self.refresh_tree() 

    def on_resize(self, event):
        w = event.width
        h = event.height
        if w > 600:
            
            new_height = h - 190 - 20
            if new_height < 200: new_height = 200 #Minimum height
            
            self.canvas.itemconfigure(self.win_table, width=w - 80, height=new_height)
            self.canvas.coords(self.win_search, w - 30, 20)

    #--- Data Logic ---
    def calculate_results(self, cw1, cw2, cw3, exam):
        total_score = cw1 + cw2 + cw3 + exam
        percent = (total_score / 160) * 100
        if percent >= 70: grade = 'A'
        elif percent >= 60: grade = 'B'
        elif percent >= 50: grade = 'C'
        elif percent >= 40: grade = 'D'
        else: grade = 'F'
        return round(percent, 2), grade, (cw1+cw2+cw3)

    def load_data(self):
        self.students = []
        if not os.path.exists(self.filename):
            try: open(self.filename, 'w').write("0\n")
            except: pass
        try:
            with open(self.filename, 'r') as f:
                lines = f.readlines()
                if not lines: return
                for line in lines[1:]:
                    line = line.strip()
                    if not line: continue
                    p = line.split(',')
                    if len(p) == 6:
                        code, name = int(p[0]), p[1]
                        c1, c2, c3, ex = int(p[2]), int(p[3]), int(p[4]), int(p[5])
                        perc, gr, cwt = self.calculate_results(c1, c2, c3, ex)
                        self.students.append({'code': code, 'name': name, 'cw1': c1, 'cw2': c2, 'cw3': c3, 'exam': ex, 'cw_total': cwt, 'percent': perc, 'grade': gr})
        except Exception as e: messagebox.showerror("Error", str(e))

    def save_data(self):
        try:
            with open(self.filename, 'w') as f:
                f.write(f"{len(self.students)}\n")
                for s in self.students:
                    f.write(f"{s['code']},{s['name']},{s['cw1']},{s['cw2']},{s['cw3']},{s['exam']}\n")
        except: pass

    def refresh_tree(self, data=None):
        #Clear existing
        for i in self.tree.get_children(): self.tree.delete(i)
        d = data if data else self.students
        
        #Populate
        total_p = 0
        grades = []
        for s in d:
            g_tag = f"grade_{s['grade']}"
            self.tree.insert("", END, values=(s['code'], s['name'], s['cw_total'], s['exam'], f"{s['percent']}%", s['grade']), tags=(g_tag,))
            total_p += s['percent']
            grades.append(s['grade'])
            
        count = len(d)
        avg = round(total_p/count, 2) if count > 0 else 0
        
        #Update Cards
        self.lbl_total.config(text=str(count))
        self.lbl_avg.config(text=f"{avg}%")
        self.lbl_top.config(text=min(grades) if grades else "-")
        
        #Force UI Update
        self.root.update_idletasks()

    #--- Actions ---
    def view_all_records(self):
        #Reset search bar and view all
        self.search_entry.delete(0, END)
        self.search_entry.insert(0, "Search...")
        self.search_entry.config(fg=COLORS['text_sub'])
        self.refresh_tree()
    
    def find_student(self):
        win = Toplevel(self.root)
        win.title("Find Student")
        win.geometry("400x200")
        win.configure(bg=COLORS['card_bg'])
        Label(win, text="Search Student", font=("Segoe UI", 12, "bold"), bg=COLORS['card_bg'], fg=COLORS['text_light']).pack(pady=(20,10))
        Label(win, text="Enter Name or ID:", font=("Segoe UI", 10), bg=COLORS['card_bg'], fg=COLORS['text_sub']).pack(pady=(0,5))
        e = Entry(win, font=("Segoe UI", 11), bg=COLORS['input_bg'], fg="white", insertbackground="white", relief="flat", bd=5)
        e.pack(fill=X, padx=40, pady=5)
        e.focus()
        def do_search():
            q = e.get()
            win.destroy()
            if q:
                res = [s for s in self.students if q.lower() in s['name'].lower() or q in str(s['code'])]
                if res: self.refresh_tree(res)
                else: messagebox.showinfo("Info", "No matches found.")
        Button(win, text="Search", command=do_search, bg=COLORS['accent'], fg="white", bd=0, padx=20, pady=5).pack(pady=20)
        win.bind('<Return>', lambda e: do_search())

    def show_highest(self):
        if self.students: self.refresh_tree([max(self.students, key=lambda x: x['percent'])])

    def show_lowest(self):
        if self.students: self.refresh_tree([min(self.students, key=lambda x: x['percent'])])

    def sort_menu(self):
        top = Toplevel(self.root)
        top.title("Sort")
        top.geometry("300x250")
        top.configure(bg=COLORS['card_bg'])
        Label(top, text="Sort By", font=("Segoe UI", 14, "bold"), bg=COLORS['card_bg'], fg=COLORS['text_light']).pack(pady=(20,10))
        def s(k, r):
            self.students.sort(key=lambda x: x[k], reverse=r)
            self.view_all_records()
            top.destroy()
        def mk_btn(txt, cmd):
            Button(top, text=txt, command=cmd, font=("Segoe UI", 10), bg=COLORS['input_bg'], fg="white", 
                   activebackground=COLORS['accent'], activeforeground="white", bd=0, pady=8, cursor="hand2").pack(fill=X, padx=30, pady=5)
        mk_btn("Highest Percentage ⬇️", lambda: s('percent', True))
        mk_btn("Lowest Percentage ⬆️", lambda: s('percent', False))
        mk_btn("Name (A-Z)", lambda: s('name', False))

    def delete_student(self):
        sel = self.tree.selection()
        if not sel: return
        sid = self.tree.item(sel)['values'][0]
        if messagebox.askyesno("Delete", "Delete record?"):
            self.students = [s for s in self.students if s['code'] != sid]
            self.save_data()
            self.view_all_records()

    def add_student_window(self): self.form("Add Student")
    
    def update_student_window(self):
        sel = self.tree.selection()
        if not sel: return
        sid = self.tree.item(sel)['values'][0]
        obj = next((s for s in self.students if s['code'] == sid), None)
        if obj: self.form("Edit Student", obj)

    def form(self, title, stu=None):
        win = Toplevel(self.root)
        win.title(title)
        win.geometry("450x700") 
        win.configure(bg=COLORS['card_bg'])
        
        #1. Title (Top)
        Label(win, text=title, font=("Segoe UI", 16, "bold"), bg=COLORS['card_bg'], fg=COLORS['text_light']).pack(pady=(20, 10))
        
        #2. Buttons (Bottom)
        btn_frame = Frame(win, bg=COLORS['card_bg'])
        btn_frame.pack(side=BOTTOM, fill=X, pady=20, padx=40)
        
        ents = {}
        
        def save():
            try:
                c = stu['code'] if stu else int(ents['code'].get())
                n = ents['name'].get()
                m = [int(ents[x].get()) for x in ['cw1','cw2','cw3']]
                ex = int(ents['exam'].get())
                if not (1000<=c<=9999): raise ValueError("ID must be 4 digits")
                if not all(0<=x<=20 for x in m): raise ValueError("Coursework marks must be 0-20")
                if not (0<=ex<=100): raise ValueError("Exam mark must be 0-100")
                
                p, g, t = self.calculate_results(*m, ex)
                new = {'code': c, 'name': n, 'cw1': m[0], 'cw2': m[1], 'cw3': m[2], 'exam': ex, 'cw_total': t, 'percent': p, 'grade': g}
                
                if stu: stu.update(new)
                else: self.students.append(new)
                self.save_data()
                self.view_all_records()
                win.destroy()
                
                # Auto-Scroll to bottom to show new student
                if not stu and self.students: 
                    # Get the last item in the tree (which is the new student)
                    children = self.tree.get_children()
                    if children:
                        last_item = children[-1]
                        self.tree.selection_set(last_item)
                        self.tree.focus(last_item)
                        self.tree.see(last_item) # Scroll to ensure visibility
                    
            except Exception as e: messagebox.showerror("Error", str(e))
            
        Button(btn_frame, text="Cancel", command=win.destroy, font=("Segoe UI", 10), bg=COLORS['sidebar_bg'], fg="white", bd=0, padx=20, pady=10, cursor="hand2").pack(side=LEFT)
        Button(btn_frame, text="Submit", command=save, font=("Segoe UI", 10, "bold"), bg=COLORS['accent'], fg="white", bd=0, padx=20, pady=10, cursor="hand2").pack(side=RIGHT)

        #3. Form Content
        form_frame = Frame(win, bg=COLORS['card_bg'])
        form_frame.pack(side=TOP, fill=BOTH, expand=True, padx=40)
        
        def create_entry(lbl, key):
            f = Frame(form_frame, bg=COLORS['card_bg'])
            f.pack(fill=X, pady=4)
            Label(f, text=lbl, font=("Segoe UI", 10), bg=COLORS['card_bg'], fg=COLORS['text_sub'], anchor="w").pack(fill=X)
            e = Entry(f, font=("Segoe UI", 11), bg=COLORS['input_bg'], fg="white", insertbackground="white", relief="flat", bd=5)
            e.pack(fill=X, ipady=3)
            ents[key] = e
            if stu:
                e.insert(0, str(stu[key]))
                if key == 'code': e.config(state='disabled')

        create_entry("Student ID", 'code')
        create_entry("Full Name", 'name')
        
        Frame(form_frame, bg=COLORS['sidebar_bg'], height=2).pack(fill=X, pady=10)
        Label(form_frame, text="Academic Performance", font=("Segoe UI", 9, "bold"), bg=COLORS['card_bg'], fg=COLORS['accent']).pack(anchor="w")

        create_entry("Coursework 1 (0-20)", 'cw1')
        create_entry("Coursework 2 (0-20)", 'cw2')
        create_entry("Coursework 3 (0-20)", 'cw3')
        create_entry("Final Exam (0-100)", 'exam')

if __name__ == "__main__":
    root = Tk()
    app = StudentManagerApp(root)
    root.mainloop()