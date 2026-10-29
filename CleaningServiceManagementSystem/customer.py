import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import re
from database import Database
from ui_style import make_button, style_tables, BG

class Customer:
    def __init__(self, root, back_callback=None, search_callback=None):
        self.root = root
        self.back_callback = back_callback or (lambda *args: None)
        self.search_callback = search_callback or (lambda: None)
        self.db = Database()
        self.selected_id = None
        self.root.configure(bg=BG)
        self.root.title("Customer Records")
        self.root.geometry("1000x700")
        style_tables(self.root)
        self.build_ui()
        self.load_customers()

    def build_ui(self):
        # Keep navigation at the very top so it stays visible even when the
        # customer table expands to fill the window.
        header = tk.Frame(self.root)
        header.pack(fill="x", padx=20, pady=(12, 0))
        make_button(header, text="← Back to Dashboard", width=20, pady=11,
                    font=("Arial", 11, "bold"), bg="#244C86",
                    command=self.back_to_dashboard).pack(side="left")
        tk.Label(header, text="CUSTOMER RECORDS",
                 font=("Arial", 23, "bold")).pack(side="left", padx=22)
        form = tk.LabelFrame(self.root, text="Customer Information", padx=15, pady=12)
        form.pack(fill="x", padx=20, pady=8)
        self.name_var, self.phone_var, self.address_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)
        for row, (label, var) in enumerate([
            ("Full Name:", self.name_var),
            ("Phone (09XXXXXXXXX):", self.phone_var),
            ("Address:", self.address_var),
        ]):
            tk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=5)
            tk.Entry(form, textvariable=var, width=55).grid(row=row, column=1, sticky="w", pady=5)

        buttons = tk.Frame(form)
        buttons.grid(row=3, column=0, columnspan=2, pady=10)
        for label, command, color in [
            ("Add Customer", self.add_customer, "#35A66F"),
            ("Update", self.update_customer, "#3978D4"),
            ("Delete", self.delete_customer, "#D9534F"),
            ("Clear", self.clear_form, "#64748B"),
        ]:
            make_button(buttons, text=label, width=13, pady=12, font=("Arial", 11, "bold"),
                        bg=color, command=command).pack(side="left", padx=5)

        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=20, pady=(6, 0))
        tk.Label(search_frame, text="Search customers:", font=("Arial", 11, "bold")).pack(side="left", padx=(0, 8))
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("Arial", 12), width=42, relief="solid", bd=1)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=6)
        tk.Label(search_frame, text="Type to filter name, phone, or address", font=("Arial", 9),
                 fg="#64748B").pack(side="left", padx=10)

        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("id", "name", "phone", "address")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for col, heading, width in [
            ("id", "ID", 60), ("name", "Name", 220),
            ("phone", "Phone", 150), ("address", "Address", 420)
        ]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="w")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)


    def validate_fields(self):
        name, phone, address = (self.name_var.get().strip(),
                                self.phone_var.get().strip(),
                                self.address_var.get().strip())
        if not name or not phone or not address:
            messagebox.showwarning("Required Fields", "Please fill in all customer fields.")
            return None
        if not re.fullmatch(r"09\d{9}", phone):
            messagebox.showerror("Invalid Phone Number",
                "Enter an 11-digit Philippine mobile number starting with 09.\nExample: 09171234567")
            return None
        return name, phone, address

    def add_customer(self):
        values = self.validate_fields()
        if values is None:
            return
        conn = self.db.connect()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", values)
            new_id = cur.lastrowid
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            messagebox.showerror("Database Error", f"Could not add customer.\n{exc}")
            return
        finally:
            conn.close()
        self.load_customers()
        # Continue directly to Cleaning Schedule with the newly added customer selected.
        messagebox.showinfo("Customer Added", "Customer saved successfully. Opening Cleaning Schedule...")
        self.back_callback(new_id)

    def update_customer(self):
        if self.selected_id is None:
            messagebox.showwarning("Select Customer", "Select a customer from the table first.")
            return
        values = self.validate_fields()
        if values is None:
            return
        conn = self.db.connect()
        try:
            conn.execute("UPDATE customers SET name=?, phone=?, address=? WHERE id=?",
                         (*values, self.selected_id))
            conn.commit()
            messagebox.showinfo("Success", "Customer updated successfully.")
        except sqlite3.Error as exc:
            conn.rollback()
            messagebox.showerror("Database Error", f"Could not update customer.\n{exc}")
        finally:
            conn.close()
        self.load_customers()

    def delete_customer(self):
        if self.selected_id is None:
            messagebox.showwarning("Select Customer", "Select a customer from the table first.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this customer? This cannot be undone."):
            return
        conn = self.db.connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM schedules WHERE customer_id=?", (self.selected_id,))
            if cur.fetchone()[0] > 0:
                messagebox.showerror("Cannot Delete",
                    "This customer has schedules. Delete or reassign those schedules first.")
                return
            conn.execute("DELETE FROM customers WHERE id=?", (self.selected_id,))
            conn.commit()
            messagebox.showinfo("Deleted", "Customer deleted.")
        except sqlite3.Error as exc:
            conn.rollback()
            messagebox.showerror("Database Error", f"Could not delete customer.\n{exc}")
        finally:
            conn.close()
        self.clear_form()
        self.load_customers()

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        row = self.tree.item(selected[0], "values")
        self.selected_id = int(row[0])
        self.name_var.set(row[1])
        self.phone_var.set(row[2])
        self.address_var.set(row[3])

    def on_search_change(self, *_args):
        # Live search: update the table as each character is typed.
        self.load_customers(self.search_var.get().strip())

    def load_customers(self, query=""):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = self.db.connect()
        try:
            if query:
                pattern = f"%{query}%"
                rows = conn.execute(
                    """SELECT id, name, phone, address FROM customers
                       WHERE name LIKE ? OR phone LIKE ? OR address LIKE ?
                       ORDER BY id DESC""",
                    (pattern, pattern, pattern)
                ).fetchall()
            else:
                rows = conn.execute("SELECT id, name, phone, address FROM customers ORDER BY id DESC").fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", str(exc))
        finally:
            conn.close()

    def clear_form(self):
        self.selected_id = None
        self.name_var.set("")
        self.phone_var.set("")
        self.address_var.set("")
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def schedule_selected(self):
        if self.selected_id is None:
            messagebox.showwarning("Select Customer", "Select a customer from the table first.")
            return
        self.back_callback(self.selected_id)

    def back_to_dashboard(self):
        self.back_callback()
