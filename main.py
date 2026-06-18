import tkinter as tk
from app.application import RetailerDesktopApp

def main():
    try:
        app = RetailerDesktopApp()
        app.mainloop()
    except Exception as e:
        # Fallback to a simpler UI or show error if the main app fails to load
        print(f"Error starting application: {e}")
        root = tk.Tk()
        root.title("MedicVista Retailer - Error")
        root.geometry("400x200")
        tk.Label(root, text="Failed to start application", font=("Arial", 14, "bold"), pady=20).pack()
        tk.Label(root, text=str(e), wraplength=350).pack()
        tk.Button(root, text="Close", command=root.destroy).pack(pady=20)
        root.mainloop()

if __name__ == "__main__":
    main()