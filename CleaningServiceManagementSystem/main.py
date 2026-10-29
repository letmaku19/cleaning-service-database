import tkinter as tk
from database import Database
from auth import Auth

def main():
    Database()
    root = tk.Tk()
    Auth(root)
    root.mainloop()

if __name__ == "__main__":
    main()
