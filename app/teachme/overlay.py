import tkinter as tk


class CursorGuideOverlay:
    """Non-invasive visual Teach Me guide.

    The overlay only presents information. It never moves the pointer,
    clicks, types, launches applications, or sends keyboard input.
    """

    def __init__(self, root, on_close=None, adapter=None):
        self.root = root
        self.on_close = on_close
        self.adapter = adapter

        self.window = tk.Toplevel(root)
        self.window.title("FixPilot Teach Me")
        self.window.geometry("560x360")
        self.window.attributes("-topmost", True)

        self.title = tk.Label(
            self.window,
            text="Teach Me",
            font=("Segoe UI", 16, "bold"),
        )
        self.title.pack(anchor="w", padx=18, pady=(16, 6))

        self.progress = tk.Label(
            self.window,
            text="",
            font=("Segoe UI", 9),
        )
        self.progress.pack(anchor="w", padx=18, pady=(0, 8))

        self.instruction = tk.Label(
            self.window,
            text="",
            justify="left",
            wraplength=520,
            font=("Segoe UI", 11),
        )
        self.instruction.pack(anchor="w", padx=18, pady=8)

        self.why = tk.Label(
            self.window,
            text="",
            justify="left",
            wraplength=520,
            font=("Segoe UI", 9),
        )
        self.why.pack(anchor="w", padx=18, pady=4)

        self.target = tk.Label(
            self.window,
            text="",
            justify="left",
            wraplength=520,
            font=("Segoe UI", 9),
        )
        self.target.pack(anchor="w", padx=18, pady=4)

        self.status = tk.Label(
            self.window,
            text="",
            font=("Segoe UI", 10, "bold"),
        )
        self.status.pack(anchor="w", padx=18, pady=8)

        self.cursor = tk.Label(
            self.window,
            text="Pointer: unavailable",
            font=("Consolas", 9),
        )
        self.cursor.pack(anchor="w", padx=18, pady=4)

        self.close_button = tk.Button(
            self.window,
            text="Close Guide",
            command=self.close,
        )
        self.close_button.pack(anchor="e", padx=18, pady=12)

    def update(
        self,
        step=None,
        cursor_position=None,
        progress_text="",
        snapshot=None,
    ):
        """Update the overlay from a tutorial step or UI snapshot."""

        if snapshot is None and self.adapter is not None:
            snapshot = self.adapter.snapshot()

        if snapshot is not None:
            if cursor_position is None:
                cursor_position = self._adapter_cursor_position()

            self._update_from_snapshot(
                snapshot,
                cursor_position=cursor_position,
            )
            return

        if not step:
            self.title.config(text="Teach Me Complete")
            self.progress.config(text=progress_text)
            self.instruction.config(text="Tutorial complete.")
            self.why.config(text="")
            self.target.config(text="")
            self.status.config(text="Completed")
            self._update_cursor(cursor_position)
            return

        self.title.config(text=step.title)
        self.instruction.config(text=step.instruction)

        self.why.config(
            text=f"Why: {step.why}"
        )

        self.target.config(
            text=f"Target: {step.target_hint}\n{progress_text}"
        )

        self.status.config(
            text="Waiting for you to perform the step."
        )

        self._update_cursor(cursor_position)

    def refresh_from_adapter(self):
        """Refresh the overlay from the connected Teach Me adapter.

        Returns the snapshot used for the refresh.
        """

        if self.adapter is None:
            return None

        snapshot = self.adapter.snapshot()

        self.update(snapshot=snapshot)

        return snapshot

    def _adapter_cursor_position(self):
        if self.adapter is None:
            return None

        try:
            return self.adapter.cursor_position()
        except (RuntimeError, OSError):
            return None

    def _update_from_snapshot(
        self,
        snapshot,
        cursor_position=None,
    ):
        if not isinstance(snapshot, dict):
            return

        state = snapshot.get("state", "unknown")
        step = snapshot.get("step", 0)
        total = snapshot.get("total_steps", 0)
        progress = snapshot.get("progress", 0.0)

        title = snapshot.get("title")
        instruction = snapshot.get("instruction")
        why = snapshot.get("why")
        target_hint = snapshot.get("target_hint")
        expected_result = snapshot.get("expected_result")

        self.progress.config(
            text=(
                f"Step {step + 1} of {total}  •  "
                f"{progress * 100:.0f}%"
            )
        )

        if state == "completed" or snapshot.get("finished"):
            self.title.config(text="Teach Me Complete")
            self.instruction.config(
                text="All Teach Me steps have been completed."
            )
            self.why.config(text="")
            self.target.config(text="")
            self.status.config(text="Completed")
            self._update_cursor(cursor_position)
            return

        self.title.config(text=title or "Teach Me")

        self.instruction.config(
            text=instruction or ""
        )

        self.why.config(
            text=f"Why: {why}" if why else ""
        )

        target_text = (
            f"Target: {target_hint}"
            if target_hint
            else ""
        )

        if expected_result:
            target_text += (
                f"\nExpected result: {expected_result}"
            )

        self.target.config(text=target_text)

        if state == "observe":
            status_text = "Observing the current step..."
        elif state == "explain":
            status_text = "Preparing your instructions..."
        elif state == "wait_for_user":
            status_text = "Your action is required."
        elif state == "check_result":
            status_text = "Checking the result..."
        elif state == "next_step":
            status_text = "Step completed. Ready for the next step."
        elif state == "failed":
            status_text = "The expected result was not detected."
        else:
            status_text = f"State: {state}"

        self.status.config(text=status_text)

        self._update_cursor(cursor_position)

    def _update_cursor(self, cursor_position):
        if cursor_position:
            self.cursor.config(
                text=(
                    f"Pointer: X={cursor_position['x']} "
                    f"Y={cursor_position['y']}"
                )
            )
        else:
            self.cursor.config(
                text="Pointer: unavailable"
            )

    def close(self):
        try:
            self.window.destroy()
        finally:
            if self.on_close:
                self.on_close()