
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from database import Database
from ui_style import style_tables


class CompletedJobs:
    def __init__(self, root, back_callback=None, update_callback=None):
        self.root = root
        self.back_callback = back_callback or (lambda: None)
        self.update_callback = update_callback or (lambda **kwargs: None)

        self.db = Database()
        self.selected_id = None
        self.search_var = tk.StringVar()

        self.root.title("Completed Jobs")
        self.root.geometry("1150x650")

        style_tables(self.root)
        self.build_ui()
        self.load_completed_jobs()

    def build_ui(self):
        # Header
        header = tk.Frame(self.root)
        header.pack(fill="x", padx=20, pady=(12, 5))

        tk.Button(
            header,
            text="← Back to Dashboard",
            font=("Arial", 10, "bold"),
            bg="#244C86",
            fg="white",
            activebackground="#193967",
            activeforeground="white",
            cursor="hand2",
            padx=12,
            pady=8,
            command=self.back_callback
        ).pack(side="left")

        tk.Label(
            header,
            text="COMPLETED JOBS",
            font=("Arial", 23, "bold")
        ).pack(side="left", padx=22)

        tk.Label(
            self.root,
            text="Double-click a job to select it, then use Edit or Delete.",
            font=("Arial", 10)
        ).pack(anchor="w", padx=22, pady=(5, 10))

        # Search bar
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(
            search_frame,
            text="Search:",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(0, 8))

        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 11),
            width=32
        )
        self.search_entry.pack(side="left", ipady=5)
        self.search_entry.bind("<KeyRelease>", self.search_jobs)
        self.search_entry.bind("<Return>", self.search_jobs)

        tk.Button(
            search_frame,
            text="Search",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.search_jobs
        ).pack(side="left", padx=6)

        tk.Button(
            search_frame,
            text="Clear",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.clear_search
        ).pack(side="left", padx=3)

        # Action buttons are packed BEFORE the expandable table.
        # This keeps them visible at the bottom of the window.
        self.action_frame = tk.Frame(
            self.root,
            bd=0
        )
        self.action_frame.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=(8, 14)
        )

        self.edit_button = tk.Button(
            self.action_frame,
            text="EDIT",
            font=("Arial", 12, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            width=22,
            height=2,
            relief="flat",
            cursor="hand2",
            command=self.edit_selected
        )
        self.edit_button.pack(side="left", padx=(0, 12))

        self.delete_button = tk.Button(
            self.action_frame,
            text="DELETE",
            font=("Arial", 12, "bold"),
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            width=22,
            height=2,
            relief="flat",
            cursor="hand2",
            command=self.delete_selected
        )
        self.delete_button.pack(side="left", padx=12)

        # Table
        table_frame = tk.Frame(self.root)
        table_frame.pack(
            side="top",
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )

        self.columns = (
            "id",
            "customer",
            "date",
            "time",
            "service",
            "utilities",
            "status"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=self.columns,
            show="headings",
            selectmode="browse"
        )

        headings = [
            ("id", "ID", 55),
            ("customer", "Customer", 175),
            ("date", "Cleaning Date", 120),
            ("time", "Cleaning Time", 110),
            ("service", "Cleaning Service", 180),
            ("utilities", "Utilities Used", 280),
            ("status", "Status", 110)
        ]

        for column, heading, width in headings:
            self.tree.heading(column, text=heading)
            self.tree.column(
                column,
                width=width,
                minwidth=45,
                anchor="w"
            )

        yscroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        xscroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Single-click and double-click selection events
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-Button-1>", self.on_double_click)

    def load_completed_jobs(self):
        self.selected_id = None

        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.db.connect()

        try:
            rows = conn.execute("""
                SELECT
                    s.id,
                    c.name,
                    s.service_date,
                    s.service_time,
                    s.service_type,
                    s.utilities_used,
                    s.status
                FROM schedules AS s
                JOIN customers AS c
                    ON c.id = s.customer_id
                WHERE LOWER(TRIM(COALESCE(s.status, ''))) = 'completed'
                ORDER BY s.id DESC
            """).fetchall()

            for row in rows:
                self.tree.insert("", "end", values=row)

            self.search_jobs()

        except sqlite3.Error as exc:
            messagebox.showerror(
                "Database Error",
                f"Could not load completed jobs.\n\n{exc}"
            )

        finally:
            conn.close()

    def on_select(self, _event=None):
        selection = self.tree.selection()

        if not selection:
            return

        values = self.tree.item(selection[0], "values")

        if not values:
            return

        try:
            self.selected_id = int(values[0])
        except (ValueError, TypeError, IndexError):
            self.selected_id = None

    def on_double_click(self, event):
        # Select the actual row underneath the pointer.
        item_id = self.tree.identify_row(event.y)

        if not item_id:
            return

        self.tree.selection_set(item_id)
        self.tree.focus(item_id)
        self.tree.see(item_id)

        self.on_select()

    def search_jobs(self, _event=None):
        query = self.search_var.get().strip().casefold()

        self.selected_id = None

        for item in self.tree.selection():
            self.tree.selection_remove(item)

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")

            searchable_text = " ".join(
                str(value) for value in values[1:]
            ).casefold()

            if query in searchable_text:
                self.tree.reattach(item, "", "end")
            else:
                self.tree.detach(item)

    def clear_search(self):
        self.search_var.set("")
        self.search_jobs()

    def edit_selected(self):
        if self.selected_id is None:
            messagebox.showwarning(
                "Select Job",
                "Please click or double-click a job in the table first."
            )
            return

        # Uses the callback supplied by the main application.
        try:
            self.update_callback(
                selected_schedule_id=self.selected_id
            )
        except Exception as exc:
            messagebox.showerror(
                "Edit Error",
                "Could not open the selected schedule for editing.\n\n"
                f"{exc}\n\n"
                "Check the update_callback in main.py."
            )

    def delete_selected(self):
        if self.selected_id is None:
            messagebox.showwarning(
                "Select Job",
                "Please click or double-click a job in the table first."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this completed job?\n\n"
            "This will permanently remove the schedule record."
        )

        if not confirm:
            return

        conn = self.db.connect()

        try:
            cursor = conn.execute("""
                DELETE FROM schedules
                WHERE id = ?
                  AND LOWER(TRIM(COALESCE(status, ''))) = 'completed'
            """, (self.selected_id,))

            conn.commit()

            if cursor.rowcount == 0:
                messagebox.showwarning(
                    "Not Deleted",
                    "The job was not found or is no longer completed."
                )
                self.load_completed_jobs()
                return

            self.selected_id = None

            messagebox.showinfo(
                "Success",
                "Completed job deleted successfully."
            )

            self.load_completed_jobs()

        except sqlite3.Error as exc:
            conn.rollback()
            messagebox.showerror(
                "Database Error",
                f"Could not delete the completed job.\n\n{exc}"
            )

        finally:
            conn.close()
