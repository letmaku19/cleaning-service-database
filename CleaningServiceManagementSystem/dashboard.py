import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox
from database import Database
from customer import Customer
from schedule import Schedule
from search_schedule import SearchSchedule
from completed_jobs import CompletedJobs
from ui_style import make_button, style_tables, BLUE, DARK_BLUE, LIGHT_BLUE, GREEN, ORANGE, PURPLE, BG, TEXT, WHITE

class Dashboard:
    def __init__(self, root, username="admin"):
        self.root = root
        self.username = username
        self.db = Database()
        self.show_dashboard()

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def get_counts(self):
        conn = self.db.connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(DISTINCT id) FROM customers"); customers = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT id) FROM schedules"); schedules = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT id) FROM schedules WHERE LOWER(TRIM(status))='pending'"); pending = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT id) FROM schedules WHERE LOWER(TRIM(status))='completed'"); completed = cur.fetchone()[0]
            return customers, schedules, pending, completed
        finally:
            conn.close()

    def show_dashboard(self):
        self.clear_root()
        self.root.title("Cleaning Service Management System")
        self.root.geometry("1180x720")
        self.root.configure(bg=BG)
        style_tables(self.root)

        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True)
        sidebar = tk.Frame(shell, bg=DARK_BLUE, width=225)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="🧹", font=("Arial", 29), bg=DARK_BLUE, fg=WHITE).pack(pady=(24, 0))
        tk.Frame(sidebar, bg=DARK_BLUE, height=18).pack()
        nav = [
            ("▦   Dashboard", self.show_dashboard, BLUE),
            ("♙   Customers", self.open_customers, DARK_BLUE),
            ("▤   Cleaning Schedules", self.open_schedule, DARK_BLUE),
            ("✓   Completed Jobs", self.open_completed_jobs, DARK_BLUE),
        ]
        for label, command, color in nav:
            b = tk.Button(sidebar, text=label, command=command, anchor="w",
                          font=("Arial", 11, "bold"), padx=17, pady=14,
                          bg=color, fg=WHITE, activebackground=BLUE,
                          activeforeground=WHITE, relief="flat", bd=0, cursor="hand2")
            b.pack(fill="x", padx=10, pady=3)
        tk.Button(sidebar, text="⇥   Logout", command=self.logout, anchor="w",
                  font=("Arial", 10, "bold"), padx=17, pady=12,
                  bg="#304F7C", fg=WHITE, activebackground=ORANGE,
                  relief="flat", bd=0, cursor="hand2").pack(side="bottom", fill="x", padx=10, pady=5)

        content = tk.Frame(shell, bg=BG)
        content.pack(side="left", fill="both", expand=True)
        top = tk.Frame(content, bg=BG)
        top.pack(fill="x", padx=28, pady=(26, 8))
        tk.Label(top, text="Dashboard", font=("Arial", 26, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(top, text=f"Welcome back, {self.username}  👋",
                 font=("Arial", 11), bg=BG, fg="#64748B").pack(side="right", pady=8)
        tk.Label(content, text="Here's what's happening with your cleaning service today.",
                 font=("Arial", 11), bg=BG, fg="#64748B").pack(anchor="w", padx=30, pady=(0, 16))

        card_frame = tk.Frame(content, bg=BG)
        card_frame.pack(fill="x", padx=22, pady=(4, 14))
        labels = ["Total Customers", "Total Schedules", "Pending Jobs", "Completed Jobs"]
        values = self.get_counts()
        actions = [self.open_customers, self.open_schedule,
                   lambda: self.open_schedule(status_filter="Pending"), self.open_completed_jobs]
        colors = [BLUE, GREEN, ORANGE, PURPLE]
        icons = ["♙", "▤", "◷", "✓"]
        for i, (label, value, command, color, icon) in enumerate(zip(labels, values, actions, colors, icons)):
            card = tk.Frame(card_frame, bg=color, highlightbackground=color, highlightthickness=1)
            card.grid(row=0, column=i, padx=7, sticky="nsew")
            card_frame.grid_columnconfigure(i, weight=1)
            body = tk.Frame(card, bg=color, padx=13, pady=12, cursor="hand2")
            body.pack(fill="both", expand=True)
            tk.Label(body, text=icon, font=("Arial", 19, "bold"), fg=WHITE, bg=color).pack(anchor="w")
            tk.Label(body, text=label, font=("Arial", 10, "bold"), fg=WHITE, bg=color).pack(anchor="w", pady=(3, 0))
            tk.Label(body, text=str(value), font=("Arial", 25, "bold"), fg=WHITE, bg=color).pack(anchor="w", pady=(4, 0))
            tk.Label(body, text="→", font=("Arial", 16, "bold"), fg=WHITE, bg=color).pack(anchor="e")
            for w in (card, body, *body.winfo_children()):
                w.bind("<Button-1>", lambda event, action=command: action())
                w.configure(cursor="hand2")

        # Recent Schedules panel, matching the generated UI mockup.
        recent_panel = tk.Frame(content, bg=WHITE, highlightbackground="#DCE7F5", highlightthickness=1)
        recent_panel.pack(fill="both", expand=True, padx=29, pady=(4, 18))
        recent_head = tk.Frame(recent_panel, bg=WHITE)
        recent_head.pack(fill="x", padx=16, pady=(12, 8))
        tk.Label(recent_head, text="Recent Schedules", font=("Arial", 16, "bold"),
                 bg=WHITE, fg=TEXT).pack(side="left")
        make_button(recent_head, text="View All  →", bg=WHITE, fg=BLUE,
                    activebackground=LIGHT_BLUE, activeforeground=DARK_BLUE,
                    font=("Arial", 10, "bold"), padx=8, pady=5,
                    command=self.open_schedule).pack(side="right")

        recent_frame = tk.Frame(recent_panel, bg=WHITE)
        recent_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        recent_cols = ("id", "customer", "service", "date", "time", "status")
        self.recent_tree = ttk.Treeview(recent_frame, columns=recent_cols,
                                        show="headings", height=5)
        for col, label, width in [
            ("id", "ID", 70), ("customer", "Customer", 170),
            ("service", "Service", 150), ("date", "Date", 110),
            ("time", "Time", 95), ("status", "Status", 115)
        ]:
            self.recent_tree.heading(col, text=label)
            self.recent_tree.column(col, width=width, anchor="w", stretch=True)
        self.recent_tree.pack(side="left", fill="both", expand=True)
        recent_scroll = ttk.Scrollbar(recent_frame, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=recent_scroll.set)
        recent_scroll.pack(side="right", fill="y")
        self.load_recent_schedules()
        self.recent_tree.bind("<Double-1>", lambda event: self.open_schedule())

    def load_recent_schedules(self):
        if not hasattr(self, "recent_tree") or not self.recent_tree.winfo_exists():
            return
        self.recent_tree.delete(*self.recent_tree.get_children())
        conn = self.db.connect()
        try:
            rows = conn.execute("""SELECT s.id, c.name, s.service_type,
                s.service_date, s.service_time, s.status
                FROM schedules s JOIN customers c ON c.id=s.customer_id
                WHERE TRIM(COALESCE(c.name, '')) <> ''
                ORDER BY s.id DESC LIMIT 6""").fetchall()
            for row in rows:
                self.recent_tree.insert("", "end", values=row)
        except Exception as exc:
            messagebox.showerror("Database Error", f"Could not load recent schedules.\n{exc}")
        finally:
            conn.close()

    def open_customers(self):
        self.clear_root()
        Customer(self.root, back_callback=self.customer_callback, search_callback=self.open_search)

    def customer_callback(self, customer_id=None):
        if customer_id is not None:
            self.open_schedule(customer_id)
        else:
            self.show_dashboard()

    def open_schedule(self, customer_id=None, status_filter=None, selected_schedule_id=None):
        self.clear_root()
        Schedule(self.root, back_callback=self.show_dashboard,
                 selected_customer_id=customer_id, status_filter=status_filter,
                 selected_schedule_id=selected_schedule_id)

    def open_completed_jobs(self):
        self.clear_root()
        CompletedJobs(self.root, back_callback=self.show_dashboard,
                      update_callback=self.open_schedule)

    def open_search(self):
        self.clear_root()
        SearchSchedule(self.root, back_callback=self.show_dashboard)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.clear_root()
            from auth import Auth
            Auth(self.root)
