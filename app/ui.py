import tkinter as tk
from tkinter import messagebox
from app.diagnostics import run_all_diagnostics
from app.agent import diagnose_error
from app.agent.project_reasoner import reason_about_project
from app.ai.reasoner import analyze_with_ai
from app.teachme import TutorialEngine
from app.teachme.engine import build_generic_tutorial, build_python_dependency_tutorial
from app.teachme.cursor import get_cursor_position
from app.teachme.overlay import CursorGuideOverlay
from app.runtime import version_text
from app.repair import execute_plan, verify_plan
from app.repair.service import RepairService

APP_NAME = "FixPilot Studio"
VERSION = "0.5.0"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(version_text())
        self.root.geometry("1200x760")
        self.root.minsize(980, 600)
        self.last_plan = None
        self.repair_service = RepairService('.')
        self.original_command = None

        header = tk.Frame(root, padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(header, text=APP_NAME, font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Label(header, text="  Diagnose • Plan • Approve • Repair • Verify",
                 font=("Segoe UI", 10)).pack(side="left", pady=(5, 0))

        body = tk.Frame(root)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        left = tk.Frame(body, width=310, relief="groove", bd=1)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="ERROR INPUT", font=("Segoe UI", 9, "bold")).pack(
            anchor="w", padx=12, pady=(12, 6))
        tk.Label(left, text="Paste a real terminal error:", font=("Segoe UI", 9)).pack(
            anchor="w", padx=12)
        self.error_box = tk.Text(left, height=13, wrap="word", font=("Consolas", 9))
        self.error_box.pack(fill="x", padx=12, pady=8)

        tk.Button(left, text="Analyze Error", command=self.analyze,
                  padx=10, pady=8).pack(fill="x", padx=12, pady=5)
        tk.Button(left, text="Run Diagnostics", command=self.diagnose_environment,
                  padx=10, pady=8).pack(fill="x", padx=12, pady=5)

        center = tk.Frame(body)
        center.pack(side="left", fill="both", expand=True, padx=12)

        tk.Label(center, text="FIXPILOT CONSOLE", font=("Segoe UI", 9, "bold")).pack(
            anchor="w", pady=(0, 6))
        self.output = tk.Text(center, bg="#111111", fg="#eeeeee",
                              insertbackground="#ffffff",
                              font=("Consolas", 10), wrap="word")
        self.output.pack(fill="both", expand=True)

        right = tk.Frame(body, width=250, relief="groove", bd=1)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="STATUS", font=("Segoe UI", 9, "bold")).pack(
            anchor="w", padx=12, pady=(12, 10))
        self.status = tk.Label(right, text="● Ready", font=("Segoe UI", 11, "bold"),
                               anchor="w")
        self.status.pack(fill="x", padx=12)

        tk.Button(right, text="Build Plan", command=self.plan,
                  padx=10, pady=8).pack(fill="x", padx=12, pady=(18, 6))
        tk.Button(right, text="Approve & Repair", command=self.approve_repair,
                  padx=10, pady=8).pack(fill="x", padx=12, pady=6)
        tk.Button(right, text="Verify", command=self.verify,
                  padx=10, pady=8).pack(fill="x", padx=12, pady=6)
        tk.Button(right, text="Teach Me", command=self.start_teach_me,
                  padx=10, pady=8).pack(fill="x", padx=12, pady=6)
        tk.Button(right, text="Rollback Manifests", command=self.rollback_manifests,
                  padx=10, pady=8).pack(fill="x", padx=12, pady=6)

        tk.Label(
            right,
            text="\nV0.5 introduces real, low-risk repair actions.\n\n"
                 "Every action is allowlisted and requires explicit approval.",
            justify="left", anchor="w", font=("Segoe UI", 9)
        ).pack(fill="x", padx=12, pady=12)

    def write(self, text):
        self.output.insert("end", text)
        self.output.see("end")
        self.root.update_idletasks()

    def analyze(self):
        error = self.error_box.get("1.0", "end").strip()
        if not error:
            messagebox.showwarning("FixPilot", "Paste a real error first.")
            return
        self.output.delete("1.0", "end")
        self.status.config(text="● Analyzing")
        result = diagnose_error(error)
        self.write("DIAGNOSIS\n" + "=" * 60 + "\n")
        self.write(f"Category: {result['category']}\n")
        self.write(f"Cause: {result['cause']}\n")
        self.write(f"Confidence: {result['confidence']}\n\n")
        self.write("EVIDENCE\n" + "-" * 60 + "\n")
        for source in result["sources"]:
            self.write(f"• {source['title']}\n  {source['content']}\n\n")
        self.write("RECOMMENDATION\n" + "-" * 60 + "\n")
        self.write(result["recommendation"] + "\n")
        self.last_plan = result.get("repair_plan")

        reasoning = reason_about_project(error, ".")
        ai = analyze_with_ai(reasoning)
        self.write("\nPROJECT-AWARE ANALYSIS\n" + "=" * 60 + "\n")
        self.write(f"Project files discovered: {reasoning['context']['file_count']}\n")
        for hint in reasoning["project_hints"]:
            self.write(f"• {hint}\n")
        self.write(f"AI mode: {ai.get('mode')}\n")
        if ai.get("warning"):
            self.write(f"Warning: {ai['warning']}\n")
        self.write(f"Root cause: {ai.get('root_cause', ai.get('result', 'See analysis'))}\n")
        self.write(f"Next step: {ai.get('safe_next_step', '')}\n")
        self.status.config(text="● Analysis complete")

    def diagnose_environment(self):
        self.output.delete("1.0", "end")
        self.status.config(text="● Diagnosing")
        for item in run_all_diagnostics():
            self.write(f"[{item['status']}] {item['name']}\n")
            self.write(f"  {item['message']}\n")
            if item.get("version"):
                self.write(f"  Version: {item['version']}\n")
            self.write("\n")
        self.status.config(text="● Diagnosis complete")

    def plan(self):
        if not self.last_plan:
            messagebox.showinfo("FixPilot", "Analyze an error first.")
            return
        self.write("\nREPAIR PLAN\n" + "=" * 60 + "\n")
        for i, item in enumerate(self.last_plan, 1):
            self.write(f"{i}. {item['title']}\n")
            self.write(f"   Reason: {item['reason']}\n")
            self.write(f"   Action: {item['action']}\n")
            self.write(f"   Risk: {item['risk']}\n")
            if item.get("preview"):
                self.write(f"   Preview: {item['preview']}\n")
            self.write("\n")
        self.status.config(text="● Awaiting approval")

    def approve_repair(self):
        if not self.last_plan:
            messagebox.showinfo("FixPilot", "Analyze an error first.")
            return

        for item in self.last_plan:
            if item["risk"] not in {"LOW", "MEDIUM"}:
                messagebox.showerror("FixPilot", "Unsafe repair blocked.")
                return

        if not messagebox.askyesno(
            "Approve Repair",
            "FixPilot will execute only the allowlisted repair action(s) shown in the plan.\n\n"
            "Continue?"
        ):
            self.write("\nRepair cancelled by user.\n")
            return

        self.status.config(text="● Repairing")
        self.repair_service.prepare()
        for item in self.last_plan:
            self.write(f"\nExecuting: {item['title']}\n")
            result = execute_plan(item, cwd=".")
            self.write(result["message"] + "\n")
            if not result["success"]:
                self.status.config(text="● Repair failed")
                return
        changes = self.repair_service.prepare()
        self.status.config(text="● Repair complete")
        self.write("\nRepair completed. Run Verify to confirm the original workflow.\n")

    def verify(self):
        if not self.last_plan:
            messagebox.showinfo("FixPilot", "No repair plan available.")
            return
        self.status.config(text="● Verifying")
        result = self.repair_service.verify(self.last_plan, self.original_command)
        self.write("\nVERIFICATION\n" + "=" * 60 + "\n")
        self.write(result["message"] + "\n")
        self.status.config(text="● Verified" if result["success"] else "● Needs attention")

    def rollback_manifests(self):
        from app.repair.rollback import rollback_project_manifests
        if not messagebox.askyesno(
            "Rollback",
            "Restore project manifest files from the latest FixPilot snapshot?"
        ):
            return
        result = rollback_project_manifests(".")
        self.write("\nROLLBACK\n" + "=" * 60 + "\n")
        self.write(result["message"] + "\n")
        self.status.config(text="● Rollback complete" if result["success"] else "● Rollback unavailable")

    def start_teach_me(self):
        error = self.error_box.get("1.0", "end").strip()
        if not error:
            messagebox.showinfo("Teach Me", "Paste an error first.")
            return

        package = None
        if "No module named" in error:
            import re
            match = re.search(r"No module named ['\"]([^'\"]+)", error, re.I)
            if match:
                package = match.group(1).split(".")[0]

        steps = (
            build_python_dependency_tutorial(package)
            if package
            else build_generic_tutorial()
        )
        self.teach_engine = TutorialEngine(steps)

        def closed():
            self.teach_overlay = None
            self.status.config(text="● Ready")

        self.teach_overlay = CursorGuideOverlay(self.root, on_close=closed)
        self.status.config(text="● Teach Me")
        self.update_teach_overlay()

        controls = tk.Toplevel(self.root)
        controls.title("FixPilot Teach Me Controls")
        controls.geometry("420x170")
        controls.attributes("-topmost", True)

        tk.Label(
            controls,
            text="Perform the step yourself, then continue.",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(16, 8))

        button_row = tk.Frame(controls)
        button_row.pack(pady=8)

        tk.Button(button_row, text="← Back",
                  command=lambda: self.teach_back(controls)).pack(side="left", padx=5)
        tk.Button(button_row, text="Next →",
                  command=lambda: self.teach_next(controls)).pack(side="left", padx=5)
        tk.Button(button_row, text="Check",
                  command=self.teach_check).pack(side="left", padx=5)

        tk.Label(
            controls,
            text="Teach Me never moves the cursor, clicks, types,\\nor runs commands for you.",
            justify="center"
        ).pack(pady=8)

        self.teach_controls = controls

    def update_teach_overlay(self):
        if not getattr(self, "teach_overlay", None):
            return
        position = get_cursor_position()
        engine = self.teach_engine
        progress = f"Step {min(engine.state.index + 1, len(engine.steps))} / {len(engine.steps)}"
        self.teach_overlay.update(engine.current, position, progress)

    def teach_next(self, controls):
        if self.teach_engine.is_finished():
            return
        self.teach_engine.next()
        if self.teach_engine.is_finished():
            self.write("\nTEACH ME COMPLETE\n" + "=" * 60 + "\n")
            self.write("All tutorial steps were completed by the user.\n")
            self.status.config(text="● Teach Me complete")
            controls.destroy()
            if getattr(self, "teach_overlay", None):
                self.teach_overlay.close()
            return
        self.update_teach_overlay()

    def teach_back(self, controls):
        self.teach_engine.back()
        self.update_teach_overlay()

    def teach_check(self):
        result = self.teach_engine.check_current()
        if result is None:
            self.write("\nTeach Me: manual confirmation required for this step.\n")
        elif result:
            self.write("\nTeach Me: check passed.\n")
        else:
            self.write("\nTeach Me: check did not pass yet.\n")
        self.update_teach_overlay()

def run():
    root = tk.Tk()
    App(root)
    root.mainloop()
