import customtkinter as ctk

class KeyboardShortcutScreen(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        label = ctk.CTkLabel(self, text="Keyboard Shortcut Screen Content",
                             font=ctk.CTkFont(size=24, weight="bold"),
                             text_color="#1f2937")
        label.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
