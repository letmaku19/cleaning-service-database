"""Shared visual theme for the Cleaning Service Management System."""
import tkinter as tk
from tkinter import ttk

# Palette based on the supplied blue-and-white mockup.
BLUE = "#2583F5"
DARK_BLUE = "#164A91"
LIGHT_BLUE = "#EAF3FF"
GREEN = "#12A66A"
ORANGE = "#FFA21A"
PURPLE = "#8753E8"
BG = "#F3F7FD"
TEXT = "#102D5A"
WHITE = "#FFFFFF"
MUTED = "#55739F"
BORDER = "#D6E4F8"
RED = "#EF4444"

STATUS_COLORS = {
    "Pending": {"bg": "#FFF0BD", "fg": "#A95A00"},
    "In Progress": {"bg": "#D9EBFF", "fg": "#1266D6"},
    "Completed": {"bg": "#D2F6E1", "fg": "#087A43"},
    "Cancelled": {"bg": "#FEE2E2", "fg": "#B91C1C"},
}

def make_button(parent, **kwargs):
    options = {
        "font": ("Segoe UI", 10, "bold"), "padx": 13, "pady": 8,
        "bg": BLUE, "fg": WHITE, "activebackground": DARK_BLUE,
        "activeforeground": WHITE, "relief": "flat", "bd": 0,
        "cursor": "hand2",
    }
    options.update(kwargs)
    return tk.Button(parent, **options)

def style_tables(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=36,
                    background=WHITE, fieldbackground=WHITE, foreground=TEXT,
                    borderwidth=0)
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                    padding=(8, 10), background=LIGHT_BLUE, foreground=TEXT,
                    relief="flat")
    style.map("Treeview", background=[("selected", "#CFE2FF")],
              foreground=[("selected", TEXT)])
    style.configure("TCombobox", padding=6, fieldbackground=WHITE)
    style.configure("TEntry", padding=6, fieldbackground=WHITE)
    style.configure("TButton", font=("Segoe UI", 10))
