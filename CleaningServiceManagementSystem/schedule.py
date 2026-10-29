import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import calendar
from datetime import datetime
from database import Database
from ui_style import make_button, style_tables, BG

class Schedule:
    def __init__(self, root, back_callback=None, selected_customer_id=None, status_filter=None, selected_schedule_id=None):
        self.root = root
        self.back_callback = back_callback or (lambda: None)
        self.db = Database()
        self.selected_customer_id = selected_customer_id
        self.status_filter = status_filter
        self.selected_schedule_id = selected_schedule_id
        self.selected_id = None
        self.customer_map = {}
        self.root.configure(bg=BG)
        self.root.title("Cleaning Schedule Management")
        self.root.geometry("1150x760")
        style_tables(self.root)
        self.build_ui()
        self.load_customers()
        self.load_schedules()
        self.root.after(30000, self.refresh_automatic_statuses)
        if self.selected_schedule_id is not None:
            self.select_schedule_by_id(self.selected_schedule_id)

    def build_ui(self):
        heading = "CLEANING SCHEDULE MANAGEMENT"
        if self.status_filter:
            heading += f" — {self.status_filter.upper()} JOBS"
        top_bar = tk.Frame(self.root)
        top_bar.pack(fill="x", padx=18, pady=(10, 0))
        make_button(top_bar, text="← Back to Dashboard", width=20, pady=11,
                    font=("Arial", 11, "bold"), bg="#244C86",
                    command=self.back_callback).pack(side="left", padx=(0, 12))
        title_label = tk.Label(top_bar, text=heading, font=("Arial", 20, "bold"))
        title_label.place(relx=0.56, rely=0.5, anchor="center")
        form = tk.LabelFrame(self.root, text="Schedule Information", padx=12, pady=10)
        form.pack(fill="x", padx=34, pady=8, anchor="center")
        for col in range(4):
            form.grid_columnconfigure(col, weight=1)
        self.customer_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.time_var = tk.StringVar()
        self.service_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Pending")

        tk.Label(form, text="Customer:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.customer_combo = ttk.Combobox(form, textvariable=self.customer_var, state="readonly", width=30)
        self.customer_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        tk.Label(form, text="Cleaning Date (MM/DD/YYYY):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        date_frame = tk.Frame(form)
        date_frame.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        tk.Entry(date_frame, textvariable=self.date_var, width=13).pack(side="left")
        make_button(date_frame, text="📅 Calendar", command=self.open_calendar).pack(side="left", padx=3)
        make_button(date_frame, text="Today", command=self.set_today).pack(side="left", padx=3)

        tk.Label(form, text="Cleaning Time:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        time_frame = tk.Frame(form)
        time_frame.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.time_entry = ttk.Entry(time_frame, textvariable=self.time_var, width=13)
        self.time_entry.pack(side="left")
        make_button(time_frame, text="🕒 Choose Time", command=self.open_time_picker).pack(side="left", padx=3)
        make_button(time_frame, text="Time Now", command=self.set_time_now).pack(side="left", padx=3)
        tk.Label(form, text="Cleaning Service:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.service_combo = ttk.Combobox(form, textvariable=self.service_var, state="readonly", width=25,
            values=["Basic Cleaning", "Deep Cleaning", "Bathroom Cleaning", "Kitchen Cleaning", "Move-in/Move-out Cleaning", "Office Cleaning", "Carpet Cleaning", "Sofa/Upholstery Cleaning", "Window Cleaning"])
        self.service_combo.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        self.service_combo.bind("<<ComboboxSelected>>", self.set_default_utilities)

        tk.Label(form, text="Utilities Used:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        utilities_frame = tk.Frame(form)
        utilities_frame.grid(row=2, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        self.utility_vars = {}
        utility_names = ["Soap", "Dishwashing Liquid", "All-Purpose Cleaner", "Disinfectant", "Bleach",
                         "Glass Cleaner", "Floor Cleaner", "Toilet Bowl Cleaner", "Furniture Polish",
                         "Degreaser", "Air Freshener", "Upholstery Cleaner", "Mop", "Broom", "Dustpan",
                         "Vacuum", "Wax", "Cleaning Cloth", "Microfiber Cloth", "Sponge", "Scrub Brush",
                         "Rubber Gloves", "Trash Bags", "Paper Towels", "Bucket"]
        for idx, utility in enumerate(utility_names):
            var = tk.BooleanVar()
            self.utility_vars[utility] = var
            tk.Checkbutton(utilities_frame, text=utility, variable=var).grid(row=idx // 5, column=idx % 5, sticky="w", padx=4, pady=2)

        tk.Label(form, text="Status:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.status_combo = ttk.Combobox(form, textvariable=self.status_var, state="readonly",
                     values=["Pending", "In Progress", "Completed", "Cancelled"], width=20)
        self.status_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        tk.Label(form, text="For new schedules, status is automatic:").grid(row=3, column=2, columnspan=2, sticky="w", padx=5, pady=5)
        self.date_var.trace_add("write", self.update_status_preview)
        self.time_var.trace_add("write", self.update_status_preview)

        actions = tk.Frame(form)
        actions.grid(row=4, column=0, columnspan=4, pady=10)
        for label, command in [
            ("Add Schedule", self.add_schedule), ("Update", self.update_schedule),
            ("Delete", self.delete_schedule), ("Clear", self.clear_form),
            ("Refresh", self.load_schedules)
        ]:
            make_button(actions, text=label, width=13, command=command).pack(side="left", padx=3)

        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=20, pady=(6, 0))
        tk.Label(search_frame, text="Search schedules:", font=("Arial", 11, "bold")).pack(side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("Arial", 12), width=42, relief="solid", bd=1)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=6)
        make_button(search_frame, text="Search", width=10, command=self.load_schedules).pack(side="left", padx=(8, 0))
        make_button(search_frame, text="Clear", width=8, bg="#64748B", command=self.show_all).pack(side="left", padx=(5, 0))
        tk.Label(search_frame, text="Live search",
                 font=("Arial", 9), fg="#64748B").pack(side="left", padx=10)

        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=20, pady=8)
        self.columns = ("id", "customer", "date", "time", "service", "utilities", "status")
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        for col, heading, width in [
            ("id", "ID", 45), ("customer", "Customer", 180), ("date", "Date", 110),
            ("time", "Time", 100), ("service", "Service", 180),
            ("utilities", "Utilities Used", 250), ("status", "Status", 100)
        ]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="w")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.pack(side="top", fill="both", expand=True)
        xscroll.pack(side="bottom", fill="x")
        yscroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)


    def set_today(self):
        self.date_var.set(datetime.now().strftime("%m/%d/%Y"))

    def set_time_now(self):
        """Fill Cleaning Time with the computer's current local time."""
        self.time_var.set(datetime.now().strftime("%I:%M %p"))

    @staticmethod
    def parse_schedule_datetime(date_text, time_text):
        """Parse the app's standard date/time format; return None if invalid."""
        try:
            return datetime.strptime(
                f"{str(date_text).strip()} {str(time_text).strip().upper()}",
                "%m/%d/%Y %I:%M %p"
            )
        except (TypeError, ValueError):
            return None

    def has_time_conflict(self, conn, date_text, time_text, exclude_id=None):
        """Prevent two schedules from using the exact same date and time."""
        wanted = self.parse_schedule_datetime(date_text, time_text)
        if wanted is None:
            return False
        rows = conn.execute(
            "SELECT id, service_date, service_time FROM schedules"
        ).fetchall()
        for schedule_id, existing_date, existing_time in rows:
            if exclude_id is not None and int(schedule_id) == int(exclude_id):
                continue
            existing = self.parse_schedule_datetime(existing_date, existing_time)
            if existing is not None and existing == wanted:
                return True
        return False

    def open_time_picker(self):
        """Open a time picker that allows any hour and minute, such as 6:30 or 5:53."""
        try:
            current = datetime.strptime(self.time_var.get().strip().upper(), "%I:%M %p")
        except ValueError:
            current = datetime.now()
        popup = tk.Toplevel(self.root)
        popup.title("Select Cleaning Time")
        popup.transient(self.root)
        popup.grab_set()
        popup.resizable(False, False)
        tk.Label(popup, text="Choose hour, minute, and AM/PM", font=("Arial", 11, "bold")).pack(padx=14, pady=(12, 8))
        picker = tk.Frame(popup)
        picker.pack(padx=14, pady=4)
        hour_var = tk.StringVar(value=current.strftime("%I"))
        minute_var = tk.StringVar(value=current.strftime("%M"))
        ampm_var = tk.StringVar(value=current.strftime("%p"))
        ttk.Combobox(picker, textvariable=hour_var, values=[f"{h:02d}" for h in range(1, 13)], width=4, state="readonly").grid(row=0, column=0, padx=4)
        tk.Label(picker, text=":", font=("Arial", 14, "bold")).grid(row=0, column=1)
        ttk.Combobox(picker, textvariable=minute_var, values=[f"{m:02d}" for m in range(60)], width=4, state="readonly").grid(row=0, column=2, padx=4)
        ttk.Combobox(picker, textvariable=ampm_var, values=["AM", "PM"], width=5, state="readonly").grid(row=0, column=3, padx=4)
        def choose_time():
            self.time_var.set(f"{int(hour_var.get()):02d}:{minute_var.get()} {ampm_var.get()}")
            popup.destroy()
        make_button(popup, text="Use This Time", command=choose_time).pack(pady=(8, 12))

    @staticmethod
    def status_for_datetime(date_text, time_text):
        """Return Pending before the scheduled date/time, otherwise In Progress."""
        scheduled = Schedule.parse_schedule_datetime(date_text, time_text)
        if scheduled is None:
            return "Pending"
        return "Pending" if scheduled > datetime.now() else "In Progress"

    def refresh_automatic_statuses(self):
        """Keep Pending/In Progress schedules synchronized with their scheduled date/time.
        Completed and Cancelled schedules are left unchanged.
        """
        try:
            conn = self.db.connect()
            try:
                rows = conn.execute(
                    "SELECT id, service_date, service_time, status FROM schedules "
                    "WHERE LOWER(TRIM(status)) IN ('pending', 'in progress')"
                ).fetchall()
                for schedule_id, date_text, time_text, old_status in rows:
                    new_status = self.status_for_datetime(date_text, time_text)
                    if new_status != old_status:
                        conn.execute("UPDATE schedules SET status=? WHERE id=?", (new_status, schedule_id))
                conn.commit()
            finally:
                conn.close()
            if hasattr(self, "tree") and self.tree.winfo_exists():
                self.load_schedules()
        except (sqlite3.Error, tk.TclError):
            pass
        finally:
            try:
                if self.root.winfo_exists():
                    self.root.after(30000, self.refresh_automatic_statuses)
            except tk.TclError:
                pass

    def automatic_status(self):
        return self.status_for_datetime(self.date_var.get(), self.time_var.get())

    def update_status_preview(self, *_args):
        # Keep the status field useful while entering a new schedule. Existing completed/cancelled
        # jobs are still selectable when updating a record.
        if self.selected_id is None:
            self.status_var.set(self.automatic_status())

    def open_calendar(self):
        """Open a small built-in calendar popup without requiring extra packages."""
        try:
            current = datetime.strptime(self.date_var.get().strip(), "%m/%d/%Y")
        except ValueError:
            current = datetime.now()
        year, month = current.year, current.month
        popup = tk.Toplevel(self.root)
        popup.title("Select Cleaning Date")
        popup.transient(self.root)
        popup.grab_set()
        header = tk.Frame(popup)
        header.pack(fill="x", padx=8, pady=8)
        make_button(header, text="‹", command=lambda: draw_prev()).pack(side="left")
        title = tk.Label(header, font=("Arial", 12, "bold"))
        title.pack(side="left", expand=True)
        make_button(header, text="›", command=lambda: draw_next()).pack(side="right")
        grid = tk.Frame(popup)
        grid.pack(padx=8, pady=(0, 8))
        def draw(y, m):
            for child in grid.winfo_children(): child.destroy()
            title.config(text=f"{calendar.month_name[m]} {y}")
            for col, day in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
                tk.Label(grid, text=day, width=4, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=1, pady=2)
            for row, week in enumerate(calendar.monthcalendar(y, m), start=1):
                for col, daynum in enumerate(week):
                    if daynum:
                        make_button(grid, text=str(daynum), width=3,
                                  command=lambda d=daynum, yy=y, mm=m: choose_date(yy, mm, d)).grid(row=row, column=col, padx=1, pady=1)
        def choose_date(y, m, d):
            self.date_var.set(datetime(y, m, d).strftime("%m/%d/%Y"))
            popup.destroy()
        def draw_prev():
            nonlocal year, month
            year, month = (year - 1, 12) if month == 1 else (year, month - 1)
            draw(year, month)
        def draw_next():
            nonlocal year, month
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
            draw(year, month)
        draw(year, month)

    def set_default_utilities(self, _event=None):
        defaults = {
            "Basic Cleaning": ["Soap", "All-Purpose Cleaner", "Mop", "Broom", "Microfiber Cloth", "Trash Bags"],
            "Deep Cleaning": ["All-Purpose Cleaner", "Disinfectant", "Bleach", "Degreaser", "Floor Cleaner", "Scrub Brush", "Microfiber Cloth", "Rubber Gloves", "Mop", "Vacuum"],
            "Bathroom Cleaning": ["Toilet Bowl Cleaner", "Bleach", "Disinfectant", "Scrub Brush", "Rubber Gloves", "Microfiber Cloth"],
            "Kitchen Cleaning": ["Dishwashing Liquid", "Degreaser", "Sponge", "All-Purpose Cleaner", "Disinfectant", "Microfiber Cloth", "Trash Bags"],
            "Move-in/Move-out Cleaning": ["All-Purpose Cleaner", "Glass Cleaner", "Floor Cleaner", "Disinfectant", "Mop", "Broom", "Vacuum", "Microfiber Cloth", "Trash Bags"],
            "Office Cleaning": ["All-Purpose Cleaner", "Disinfectant", "Glass Cleaner", "Mop", "Broom", "Vacuum", "Microfiber Cloth", "Trash Bags"],
            "Carpet Cleaning": ["Vacuum", "Upholstery Cleaner", "Microfiber Cloth", "Rubber Gloves"],
            "Sofa/Upholstery Cleaning": ["Upholstery Cleaner", "Vacuum", "Microfiber Cloth", "Sponge", "Rubber Gloves"],
            "Window Cleaning": ["Glass Cleaner", "Microfiber Cloth", "Sponge", "Rubber Gloves"]
        }
        selected = defaults.get(self.service_var.get(), [])
        for name, var in self.utility_vars.items():
            var.set(name in selected)

    def load_customers(self):
        conn = self.db.connect()
        try:
            rows = conn.execute("SELECT id, name FROM customers ORDER BY name").fetchall()
            self.customer_map = {f"{name} [ID:{customer_id}]": customer_id for customer_id, name in rows}
            self.customer_combo["values"] = list(self.customer_map.keys())
            if self.selected_customer_id is not None:
                for label, customer_id in self.customer_map.items():
                    if customer_id == self.selected_customer_id:
                        self.customer_var.set(label)
                        break
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", str(exc))
        finally:
            conn.close()

    def selected_utilities(self):
        return ", ".join(name for name, var in self.utility_vars.items() if var.get())

    def validate_form(self):
        customer_label = self.customer_var.get()
        date_text = self.date_var.get().strip()
        time_text = self.time_var.get().strip()
        service = self.service_var.get().strip()
        utilities = self.selected_utilities()
        status = self.status_var.get().strip()
        customer_id = self.customer_map.get(customer_label)

        if not customer_id:
            messagebox.showwarning("Required Field", "Please select a customer.")
            return None
        try:
            date_text = datetime.strptime(date_text, "%m/%d/%Y").strftime("%m/%d/%Y")
        except ValueError:
            messagebox.showerror("Invalid Date", "Use MM/DD/YYYY, for example 10/27/2026.")
            return None
        try:
            time_text = datetime.strptime(time_text.upper(), "%I:%M %p").strftime("%I:%M %p")
        except ValueError:
            messagebox.showerror("Invalid Time", "Use a time like 09:00 AM or 02:30 PM.")
            return None
        if not service:
            messagebox.showwarning("Required Field", "Please select a cleaning service.")
            return None
        if not utilities:
            messagebox.showwarning("Required Field", "Please select at least one utility.")
            return None
        if status not in ("Pending", "In Progress", "Completed", "Cancelled"):
            messagebox.showwarning("Required Field", "Please select a valid status.")
            return None
        return customer_id, date_text, time_text, service, utilities, status

    def add_schedule(self):
        values = self.validate_form()
        if values is None:
            return
        # New schedules get their status from the selected date and time automatically.
        values = (*values[:5], self.automatic_status())
        conn = self.db.connect()
        try:
            if self.has_time_conflict(conn, values[1], values[2]):
                messagebox.showwarning(
                    "Time Not Available",
                    f"May schedule na sa {values[1]} at {values[2]}. Pumili ng ibang oras o petsa."
                )
                return
            conn.execute("""INSERT INTO schedules
                (customer_id, service_date, service_time, service_type, utilities_used, status)
                VALUES (?, ?, ?, ?, ?, ?)""", values)
            conn.commit()
            messagebox.showinfo("Success", "Cleaning schedule added.")
            self.clear_form()
            self.load_schedules()
        except sqlite3.Error as exc:
            conn.rollback()
            messagebox.showerror("Database Error", f"Could not add schedule.\n{exc}")
        finally:
            conn.close()

    def update_schedule(self):
        if self.selected_id is None:
            messagebox.showwarning("Select Schedule", "Select a schedule from the table first.")
            return
        values = self.validate_form()
        if values is None:
            return
        conn = self.db.connect()
        try:
            previous = conn.execute(
                "SELECT service_date, service_time FROM schedules WHERE id=?", (self.selected_id,)
            ).fetchone()
            if self.has_time_conflict(conn, values[1], values[2], exclude_id=self.selected_id):
                messagebox.showwarning(
                    "Time Not Available",
                    f"May ibang schedule na sa {values[1]} at {values[2]}. Pumili ng ibang oras o petsa."
                )
                return
            changed_datetime = previous is not None and (
                str(previous[0]).strip() != values[1] or str(previous[1]).strip().upper() != values[2].upper()
            )
            # Recalculate immediately after a date/time change: future = Pending;
            # current/past = In Progress. The periodic refresh keeps it current later.
            saved_status = self.status_for_datetime(values[1], values[2]) if changed_datetime else values[5]
            conn.execute("""UPDATE schedules SET customer_id=?, service_date=?, service_time=?,
                service_type=?, utilities_used=?, status=? WHERE id=?""", (*values[:5], saved_status, self.selected_id))
            conn.commit()
            messagebox.showinfo(
                "Success",
                f"Schedule updated. Status: {saved_status}." if changed_datetime else "Schedule updated."
            )
            self.clear_form()
            self.load_schedules()
        except sqlite3.Error as exc:
            conn.rollback()
            messagebox.showerror("Database Error", f"Could not update schedule.\n{exc}")
        finally:
            conn.close()

    def delete_schedule(self):
        if self.selected_id is None:
            messagebox.showwarning("Select Schedule", "Select a schedule from the table first.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete the selected schedule? This cannot be undone."):
            return
        conn = self.db.connect()
        try:
            conn.execute("DELETE FROM schedules WHERE id=?", (self.selected_id,))
            conn.commit()
            messagebox.showinfo("Deleted", "Schedule deleted.")
            self.clear_form()
            self.load_schedules()
        except sqlite3.Error as exc:
            conn.rollback()
            messagebox.showerror("Database Error", str(exc))
        finally:
            conn.close()

    def on_search_change(self, *_args):
        # Refresh results immediately after each typed character.
        self.load_schedules()

    def load_schedules(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        search = self.search_var.get().strip().lower()
        conn = self.db.connect()
        try:
            rows = conn.execute("""SELECT s.id, c.name, s.service_date, s.service_time,
                s.service_type, s.utilities_used, s.status
                FROM schedules s JOIN customers c ON c.id=s.customer_id
                WHERE TRIM(COALESCE(c.name, '')) <> ''
                ORDER BY s.id DESC""").fetchall()
            for row in rows:
                if self.status_filter and str(row[6]).strip().lower() != self.status_filter.lower():
                    continue
                # Match the beginning of any displayed field (e.g. J finds customers
                # whose names start with J); do not wait for a Search button.
                if not search or any(str(value or "").strip().lower().startswith(search) for value in row):
                    self.tree.insert("", "end", values=row)
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not load schedules.\n{exc}")
        finally:
            conn.close()

    def show_all(self):
        self.search_var.set("")
        self.status_filter = None
        self.load_schedules()

    def on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        row = self.tree.item(selection[0], "values")
        self.selected_id = int(row[0])
        conn = self.db.connect()
        try:
            detail = conn.execute("""SELECT customer_id, service_date, service_time,
                service_type, utilities_used, status FROM schedules WHERE id=?""",
                (self.selected_id,)).fetchone()
        finally:
            conn.close()
        if not detail:
            return
        customer_id, date_text, time_text, service, utilities, status = detail
        for label, cid in self.customer_map.items():
            if cid == customer_id:
                self.customer_var.set(label)
                break
        self.date_var.set(date_text)
        self.time_var.set(time_text)
        self.service_var.set(service)
        self.status_var.set(status)
        selected_utilities = {x.strip() for x in (utilities or "").split(",") if x.strip()}
        for name, var in self.utility_vars.items():
            var.set(name in selected_utilities)


    def select_schedule_by_id(self, schedule_id):
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and int(values[0]) == int(schedule_id):
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.see(item)
                self.on_select()
                break

    def clear_form(self):
        self.selected_id = None
        self.customer_var.set("")
        self.date_var.set("")
        self.time_var.set("")
        self.service_var.set("")
        self.status_var.set("Pending")
        for var in self.utility_vars.values():
            var.set(False)
        for item in self.tree.selection():
            self.tree.selection_remove(item)
