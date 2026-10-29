import tkinter as tk
from tkinter import messagebox
import sqlite3
from database import Database
from dashboard import Dashboard
from ui_style import make_button

class Auth:
    def __init__(self, root):
        self.root = root
        self.db = Database()
        self.root.title("Login - Cleaning Service Management System")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        tk.Label(root, text="CLEANING SERVICE\nMANAGEMENT SYSTEM",
                 font=("Arial", 20, "bold")).pack(pady=40)
        tk.Label(root, text="Username:", font=("Arial", 11)).pack()
        self.username_entry = tk.Entry(root, width=30, font=("Arial", 11))
        self.username_entry.pack(pady=5)

        tk.Label(root, text="Password:", font=("Arial", 11)).pack(pady=(10, 0))
        password_frame = tk.Frame(root)
        password_frame.pack(pady=5)
        self.password_entry = tk.Entry(password_frame, width=25,
                                       font=("Arial", 11), show="*")
        self.password_entry.pack(side="left")
        self.show_password_button = make_button(
            password_frame, text="👁", width=4, command=self.toggle_password)
        self.show_password_button.pack(side="left", padx=5)

        make_button(root, text="LOGIN", font=("Arial", 11, "bold"),
                  width=20, height=2, command=self.login).pack(pady=25)
        self.username_entry.focus_set()
        self.root.bind("<Return>", self._enter_login)

    def _enter_login(self, _event=None):
        self.login()

    def toggle_password(self):
        hidden = self.password_entry.cget("show") == "*"
        self.password_entry.config(show="" if hidden else "*")
        self.show_password_button.config(text="🙈" if hidden else "👁")

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Warning", "Please enter username and password.")
            return

        conn = None
        try:
            conn = self.db.connect()
            cur = conn.cursor()
            cur.execute("SELECT username FROM users WHERE username=? AND password=?",
                        (username, password))
            user = cur.fetchone()
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not verify login.\n{exc}")
            return
        finally:
            if conn:
                conn.close()

        if user:
            self.root.unbind("<Return>")
            for widget in self.root.winfo_children():
                widget.destroy()
            Dashboard(self.root, username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
