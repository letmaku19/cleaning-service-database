import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database import Database
from ui_style import make_button, style_tables

class SearchSchedule:
    def __init__(self, root, back_callback=None):
        self.root = root
        self.back_callback = back_callback or (lambda: None)
        self.db = Database()
        self.root.title("Search Cleaning Schedules")
        self.root.geometry("1050x650")
        style_tables(self.root)
        self.build_ui()
        self.search()

    def build_ui(self):
        tk.Label(self.root, text="SEARCH CLEANING SCHEDULES",
                 font=("Arial", 20, "bold")).pack(pady=15)
        controls = tk.Frame(self.root)
        controls.pack(fill="x", padx=20, pady=10)
        self.query_var = tk.StringVar()
        self.field_var = tk.StringVar(value="All Fields")
        ttk.Combobox(controls, textvariable=self.field_var, state="readonly", width=20,
            values=["All Fields", "Customer", "Service Date", "Service Time",
                    "Service Type", "Utilities Used", "Status"]).pack(side="left", padx=(0, 8))
        tk.Entry(controls, textvariable=self.query_var, width=45).pack(side="left", padx=5)
        make_button(controls, text="Search", command=self.search).pack(side="left", padx=5)
        make_button(controls, text="Show All", command=self.show_all).pack(side="left", padx=5)
        self.count_label = tk.Label(self.root, text="Results: 0")
        self.count_label.pack(anchor="w", padx=22)

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.columns = ("id", "customer", "date", "time", "service", "utilities", "status")
        self.tree = ttk.Treeview(frame, columns=self.columns, show="headings")
        for col, heading, width in [
            ("id", "ID", 50), ("customer", "Customer", 180), ("date", "Service Date", 120),
            ("time", "Service Time", 110), ("service", "Service Type", 190),
            ("utilities", "Utilities Used", 250), ("status", "Status", 100)
        ]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="w")
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        xs = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.tree.pack(side="top", fill="both", expand=True)
        xs.pack(side="bottom", fill="x")
        ys.pack(side="right", fill="y")
        make_button(self.root, text="Back to Dashboard",
                  command=self.back_callback).pack(pady=(0, 15))
        self.root.bind("<Return>", lambda event: self.search())

    def search(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        query = self.query_var.get().strip().lower()
        field = self.field_var.get()
        field_index = {
            "Customer": 1, "Service Date": 2, "Service Time": 3,
            "Service Type": 4, "Utilities Used": 5, "Status": 6
        }
        conn = self.db.connect()
        try:
            rows = conn.execute("""SELECT s.id, c.name, s.service_date, s.service_time,
                s.service_type, s.utilities_used, s.status
                FROM schedules s JOIN customers c ON c.id=s.customer_id
                ORDER BY s.id DESC""").fetchall()
            count = 0
            for row in rows:
                if not query:
                    match = True
                elif field == "All Fields":
                    match = any(query in str(value).lower() for value in row)
                else:
                    match = query in str(row[field_index[field]]).lower()
                if match:
                    self.tree.insert("", "end", values=row)
                    count += 1
            self.count_label.config(text=f"Results: {count}")
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not search schedules.\n{exc}")
        finally:
            conn.close()

    def show_all(self):
        self.query_var.set("")
        self.field_var.set("All Fields")
        self.search()
