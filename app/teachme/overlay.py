import tkinter as tk

class CursorGuideOverlay:
    """Non-invasive visual guide.

    It shows instructions and the current pointer coordinates. It never moves
    the pointer, clicks, types, or sends keyboard input to another application.
    """
    def __init__(self, root, on_close=None):
        self.root = root
        self.on_close = on_close
        self.window = tk.Toplevel(root)
        self.window.title("FixPilot Teach Me")
        self.window.geometry("520x250")
        self.window.attributes("-topmost", True)

        self.title = tk.Label(self.window, text="Teach Me",
                              font=("Segoe UI", 16, "bold"))
        self.title.pack(anchor="w", padx=18, pady=(16, 6))

        self.instruction = tk.Label(
            self.window, text="", justify="left", wraplength=480,
            font=("Segoe UI", 11)
        )
        self.instruction.pack(anchor="w", padx=18, pady=8)

        self.target = tk.Label(
            self.window, text="", justify="left", wraplength=480,
            font=("Segoe UI", 9)
        )
        self.target.pack(anchor="w", padx=18, pady=4)

        self.cursor = tk.Label(self.window, text="Pointer: unavailable",
                               font=("Consolas", 9))
        self.cursor.pack(anchor="w", padx=18, pady=4)

        tk.Button(self.window, text="Close Guide", command=self.close).pack(
            anchor="e", padx=18, pady=12
        )

    def update(self, step, cursor_position=None, progress_text=""):
        if not step:
            self.instruction.config(text="Tutorial complete.")
            self.target.config(text=progress_text)
            return
        self.title.config(text=step.title)
        self.instruction.config(text=step.instruction)
        self.target.config(
            text=f"Why: {step.why}\nTarget: {step.target_hint}\n{progress_text}"
        )
        if cursor_position:
            self.cursor.config(
                text=f"Pointer: X={cursor_position['x']} Y={cursor_position['y']}"
            )

    def close(self):
        try:
            self.window.destroy()
        finally:
            if self.on_close:
                self.on_close()
