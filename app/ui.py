import shlex
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, filedialog

from app.diagnostics import run_all_diagnostics
from app.agent import diagnose_error
from app.agent.project_reasoner import reason_about_project
from app.agent.repair_agent import RepairAgent
from app.ai.reasoner import analyze_with_ai
from app.repair.planner import build_reasoned_repair_plan
from app.diagnostics.original_command_verifier import OriginalCommandVerifier

from app.teachme import TutorialEngine
from app.teachme.engine import (
    build_generic_tutorial,
    build_python_dependency_tutorial,
)
from app.teachme.cursor import get_cursor_position
from app.teachme.overlay import CursorGuideOverlay
from app.runtime import version_text


APP_NAME = "FixPilot Studio"
VERSION = "1.5.0"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - V{VERSION}")
        self.root.geometry("1250x800")
        self.root.minsize(1050, 650)

        self.last_plan = None
        self.last_result = None
        self.original_command = None

        self.project_root = str(Path(".").resolve())

        self.build_ui()

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):
        header = tk.Frame(self.root, padx=16, pady=12)
        header.pack(fill="x")

        tk.Label(
            header,
            text=APP_NAME,
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Label(
            header,
            text="  Detect • Explain • Plan • Approve • Repair • Verify",
            font=("Segoe UI", 10),
        ).pack(side="left", pady=(5, 0))

        # --------------------------------------------------------
        # Project configuration
        # --------------------------------------------------------

        config = tk.Frame(
            self.root,
            padx=16,
            pady=8,
            relief="groove",
            bd=1,
        )
        config.pack(fill="x", padx=16, pady=(0, 10))

        tk.Label(
            config,
            text="PROJECT ROOT",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=5)

        self.project_box = tk.Entry(
            config,
            font=("Consolas", 9),
        )
        self.project_box.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=8,
            pady=5,
        )
        self.project_box.insert(0, self.project_root)

        tk.Button(
            config,
            text="Browse",
            command=self.browse_project,
        ).grid(row=0, column=2, padx=5)

        tk.Label(
            config,
            text="ORIGINAL COMMAND",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=1, column=0, sticky="w", padx=8, pady=5)

        self.command_box = tk.Entry(
            config,
            font=("Consolas", 9),
        )
        self.command_box.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=8,
            pady=5,
        )

        tk.Label(
            config,
            text="Example: .venv\\Scripts\\python.exe app.py",
            font=("Segoe UI", 8),
        ).grid(
            row=1,
            column=2,
            sticky="w",
            padx=5,
        )

        config.columnconfigure(1, weight=1)

        # --------------------------------------------------------
        # Main body
        # --------------------------------------------------------

        body = tk.Frame(self.root)
        body.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=(0, 16),
        )

        # --------------------------------------------------------
        # LEFT
        # --------------------------------------------------------

        left = tk.Frame(
            body,
            width=330,
            relief="groove",
            bd=1,
        )
        left.pack(
            side="left",
            fill="y",
        )
        left.pack_propagate(False)

        tk.Label(
            left,
            text="ERROR INPUT",
            font=("Segoe UI", 9, "bold"),
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 6),
        )

        tk.Label(
            left,
            text="Paste the real terminal error:",
            font=("Segoe UI", 9),
        ).pack(
            anchor="w",
            padx=12,
        )

        self.error_box = tk.Text(
            left,
            height=15,
            wrap="word",
            font=("Consolas", 9),
        )
        self.error_box.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=8,
        )

        tk.Button(
            left,
            text="Analyze Error",
            command=self.analyze,
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=12,
            pady=5,
        )

        tk.Button(
            left,
            text="Run Diagnostics",
            command=self.diagnose_environment,
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=12,
            pady=5,
        )

        # --------------------------------------------------------
        # CENTER
        # --------------------------------------------------------

        center = tk.Frame(body)

        center.pack(
            side="left",
            fill="both",
            expand=True,
            padx=12,
        )

        tk.Label(
            center,
            text="FIXPILOT CONSOLE",
            font=("Segoe UI", 9, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 6),
        )

        self.output = tk.Text(
            center,
            bg="#111111",
            fg="#eeeeee",
            insertbackground="#ffffff",
            font=("Consolas", 10),
            wrap="word",
        )

        self.output.pack(
            fill="both",
            expand=True,
        )

        # --------------------------------------------------------
        # RIGHT
        # --------------------------------------------------------

        right = tk.Frame(
            body,
            width=250,
            relief="groove",
            bd=1,
        )

        right.pack(
            side="right",
            fill="y",
        )

        right.pack_propagate(False)

        tk.Label(
            right,
            text="STATUS",
            font=("Segoe UI", 9, "bold"),
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 10),
        )

        self.status = tk.Label(
            right,
            text="● Ready",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )

        self.status.pack(
            fill="x",
            padx=12,
        )

        tk.Button(
            right,
            text="Build Repair Plan",
            command=self.plan,
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=12,
            pady=(18, 6),
        )

        tk.Button(
            right,
            text="Approve & Repair",
            command=self.approve_repair,
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=12,
            pady=6,
        )

        tk.Button(
            right,
            text="Verify Original Command",
            command=self.verify,
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=12,
            pady=6,
        )

        tk.Button(
            right,
            text="Teach Me",
            command=self.start_teach_me,
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=12,
            pady=6,
        )

        tk.Button(
            right,
            text="Rollback Manifests",
            command=self.rollback_manifests,
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=12,
            pady=6,
        )

        tk.Button(
            right,
            text="Clear Console",
            command=self.clear_console,
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=12,
            pady=6,
        )

        tk.Label(
            right,
            text=(
                "\nV1.5 Repair Engine\n\n"
                "Detect\n"
                "↓\n"
                "Diagnose\n"
                "↓\n"
                "Plan\n"
                "↓\n"
                "User Approval\n"
                "↓\n"
                "Repair\n"
                "↓\n"
                "Verify\n\n"
                "Only allowlisted actions are executed."
            ),
            justify="left",
            anchor="w",
            font=("Segoe UI", 9),
        ).pack(
            fill="x",
            padx=12,
            pady=12,
        )

    # ============================================================
    # Helpers
    # ============================================================

    def write(self, text):
        self.output.insert("end", text)
        self.output.see("end")
        self.root.update_idletasks()

    def clear_console(self):
        self.output.delete("1.0", "end")
        self.status.config(text="● Ready")

    def get_project_root(self):
        value = self.project_box.get().strip()

        if not value:
            return str(Path(".").resolve())

        path = Path(value).expanduser().resolve()

        if not path.exists():
            raise ValueError(
                f"Project root does not exist:\n{path}"
            )

        if not path.is_dir():
            raise ValueError(
                f"Project root is not a directory:\n{path}"
            )

        return str(path)

    def parse_command(self):
        text = self.command_box.get().strip()

        if not text:
            return None

        try:
            parts = shlex.split(text, posix=False)
        except ValueError as exc:
            raise ValueError(
                f"Invalid command syntax: {exc}"
            )

        cleaned = []

        for part in parts:
            value = part.strip()

            if (
                len(value) >= 2
                and value[0] == '"'
                and value[-1] == '"'
            ):
                value = value[1:-1]

            cleaned.append(value)

        if not cleaned:
            return None

        return cleaned

    def get_error(self):
        return self.error_box.get(
            "1.0",
            "end",
        ).strip()

    # ============================================================
    # Browse project
    # ============================================================

    def browse_project(self):
        selected = filedialog.askdirectory(
            title="Select Project Root"
        )

        if selected:
            self.project_box.delete(0, "end")
            self.project_box.insert(0, selected)

            self.write(
                f"\nProject root selected:\n{selected}\n"
            )

    # ============================================================
    # Analyze
    # ============================================================

    def analyze(self):
        error = self.get_error()

        if not error:
            messagebox.showwarning(
                "FixPilot",
                "Paste a real terminal error first.",
            )
            return

        try:
            project_root = self.get_project_root()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Project",
                str(exc),
            )
            return

        self.output.delete("1.0", "end")
        self.status.config(text="● Analyzing")

        self.write(
            "FIXPILOT ANALYSIS\n"
            + "=" * 70
            + "\n\n"
        )

        # --------------------------------------------------------
        # Basic diagnosis
        # --------------------------------------------------------

        result = diagnose_error(error)

        self.write("DIAGNOSIS\n")
        self.write("-" * 70 + "\n")

        self.write(
            f"Category: {result.get('category')}\n"
        )

        self.write(
            f"Cause: {result.get('cause')}\n"
        )

        self.write(
            f"Confidence: {result.get('confidence')}\n\n"
        )

        self.write("EVIDENCE\n")
        self.write("-" * 70 + "\n")

        for source in result.get("sources", []):
            self.write(
                f"• {source.get('title')}\n"
            )

            self.write(
                f"  {source.get('content')}\n\n"
            )

        self.write("RECOMMENDATION\n")
        self.write("-" * 70 + "\n")

        self.write(
            f"{result.get('recommendation', '')}\n"
        )

        # --------------------------------------------------------
        # Project-aware reasoning
        # --------------------------------------------------------

        try:
            reasoning = reason_about_project(
                error,
                project_root,
            )

            self.write(
                "\nPROJECT-AWARE ANALYSIS\n"
                + "=" * 70
                + "\n"
            )

            context = reasoning.get(
                "context",
                {},
            )

            self.write(
                f"Project root: {project_root}\n"
            )

            self.write(
                f"Project files discovered: "
                f"{context.get('file_count', 0)}\n"
            )

            for hint in reasoning.get(
                "project_hints",
                [],
            ):
                self.write(
                    f"• {hint}\n"
                )

            try:
                ai = analyze_with_ai(reasoning)

                self.write(
                    f"\nAI mode: "
                    f"{ai.get('mode')}\n"
                )

                if ai.get("warning"):
                    self.write(
                        f"Warning: "
                        f"{ai.get('warning')}\n"
                    )

                self.write(
                    f"Root cause: "
                    f"{ai.get('root_cause', ai.get('result', 'See analysis'))}\n"
                )

                self.write(
                    f"Next step: "
                    f"{ai.get('safe_next_step', '')}\n"
                )

            except Exception as exc:
                self.write(
                    f"\nAI analysis unavailable: {exc}\n"
                )

        except Exception as exc:
            self.write(
                f"\nProject reasoning failed: {exc}\n"
            )

        self.last_plan = result.get(
            "repair_plan"
        )

        self.status.config(
            text="● Analysis complete"
        )

    # ============================================================
    # Environment diagnostics
    # ============================================================

    def diagnose_environment(self):
        self.output.delete(
            "1.0",
            "end",
        )

        self.status.config(
            text="● Diagnosing"
        )

        self.write(
            "ENVIRONMENT DIAGNOSTICS\n"
            + "=" * 70
            + "\n\n"
        )

        try:
            items = run_all_diagnostics()

            for item in items:
                self.write(
                    f"[{item.get('status')}] "
                    f"{item.get('name')}\n"
                )

                self.write(
                    f"  {item.get('message')}\n"
                )

                if item.get("version"):
                    self.write(
                        f"  Version: "
                        f"{item.get('version')}\n"
                    )

                self.write("\n")

            self.status.config(
                text="● Diagnosis complete"
            )

        except Exception as exc:
            self.write(
                f"Diagnostics failed:\n{exc}\n"
            )

            self.status.config(
                text="● Diagnostics failed"
            )

    # ============================================================
    # Build V1.5 repair plan
    # ============================================================

    def plan(self):
        error = self.get_error()

        if not error:
            messagebox.showinfo(
                "FixPilot",
                "Paste an error first.",
            )
            return

        try:
            project_root = self.get_project_root()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Project",
                str(exc),
            )
            return

        self.status.config(
            text="● Building plan"
        )

        self.write(
            "\nREPAIR PLAN\n"
            + "=" * 70
            + "\n"
        )

        try:
            plan = build_reasoned_repair_plan(
                error,
                project_root,
            )

            self.last_plan = plan

            if not plan:
                self.write(
                    "No repair plan was generated.\n"
                )

                self.status.config(
                    text="● No repair plan"
                )

                return

            for index, item in enumerate(
                plan,
                1,
            ):
                action = item.get(
                    "action",
                    "unknown",
                )

                package = item.get(
                    "package"
                )

                risk = item.get(
                    "risk",
                    "UNKNOWN",
                )

                reason = item.get(
                    "reason",
                    "",
                )

                confidence = item.get(
                    "confidence"
                )

                self.write(
                    f"\n{index}. {action}\n"
                )

                if package:
                    self.write(
                        f"   Target: {package}\n"
                    )

                self.write(
                    f"   Reason: {reason}\n"
                )

                self.write(
                    f"   Risk: {risk}\n"
                )

                if confidence is not None:
                    self.write(
                        f"   Confidence: "
                        f"{confidence}\n"
                    )

                if item.get(
                    "cause_code"
                ):
                    self.write(
                        f"   Cause code: "
                        f"{item.get('cause_code')}\n"
                    )

                if item.get(
                    "dependency_state"
                ):
                    self.write(
                        f"   Dependency state: "
                        f"{item.get('dependency_state')}\n"
                    )

                evidence = item.get(
                    "evidence",
                    [],
                )

                if evidence:
                    self.write(
                        "   Evidence:\n"
                    )

                    for evidence_item in evidence:
                        self.write(
                            f"     • {evidence_item}\n"
                        )

            self.write(
                "\n"
                + "=" * 70
                + "\n"
            )

            self.write(
                "Modification actions require explicit approval.\n"
            )

            self.status.config(
                text="● Awaiting approval"
            )

        except Exception as exc:
            self.write(
                f"\nPlan generation failed:\n{exc}\n"
            )

            self.status.config(
                text="● Plan failed"
            )

    # ============================================================
    # Approve + real V1.5 repair
    # ============================================================

    def approve_repair(self):
        error = self.get_error()

        if not error:
            messagebox.showinfo(
                "FixPilot",
                "Paste an error first.",
            )
            return

        try:
            project_root = self.get_project_root()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Project",
                str(exc),
            )
            return

        try:
            command = self.parse_command()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Command",
                str(exc),
            )
            return

        if not command:
            messagebox.showwarning(
                "Original Command Required",
                "Enter the exact command that originally failed.\n\n"
                "Example:\n"
                ".venv\\Scripts\\python.exe app.py",
            )
            return

        if not self.last_plan:
            self.plan()

        if not self.last_plan:
            messagebox.showinfo(
                "FixPilot",
                "No repair plan is available.",
            )
            return

        # --------------------------------------------------------
        # Safety check
        # --------------------------------------------------------

        for item in self.last_plan:
            risk = str(
                item.get(
                    "risk",
                    "UNKNOWN",
                )
            ).upper()

            if risk not in {
                "LOW",
                "MEDIUM",
            }:
                messagebox.showerror(
                    "FixPilot",
                    "Unsafe repair blocked.",
                )
                return

        # --------------------------------------------------------
        # Explicit user approval
        # --------------------------------------------------------

        summary_lines = []

        for item in self.last_plan:
            action = item.get(
                "action",
                "unknown",
            )

            package = item.get(
                "package"
            )

            if package:
                summary_lines.append(
                    f"• {action} → {package}"
                )
            else:
                summary_lines.append(
                    f"• {action}"
                )

        summary = "\n".join(
            summary_lines
        )

        approved = messagebox.askyesno(
            "Approve Repair",
            "FixPilot is requesting permission to execute "
            "the following allowlisted repair:\n\n"
            f"{summary}\n\n"
            "The original command will be re-run after repair "
            "to verify the fix.\n\n"
            "Continue?",
        )

        if not approved:
            self.write(
                "\nRepair cancelled by user.\n"
            )

            self.status.config(
                text="● Approval cancelled"
            )

            return

        # --------------------------------------------------------
        # Real RepairAgent V1.5
        # --------------------------------------------------------

        self.status.config(
            text="● Repairing"
        )

        self.write(
            "\n"
            + "=" * 70
            + "\n"
            "V1.5 REPAIR TRANSACTION\n"
            + "=" * 70
            + "\n"
        )

        self.write(
            f"Project: {project_root}\n"
        )

        self.write(
            f"Original command: "
            f"{' '.join(command)}\n\n"
        )

        try:
            agent = RepairAgent()

            result = agent.analyze_and_repair(
                command=command,
                project_root=project_root,
                error_text=error,
                approved=True,
            )

            self.last_result = result

            data = (
                result.as_dict()
                if hasattr(result, "as_dict")
                else result
            )

            self.display_repair_result(
                data
            )

            if data.get("success"):
                self.status.config(
                    text="● Repair verified"
                )
            else:
                stage = data.get(
                    "stage",
                    "failed",
                )

                self.status.config(
                    text=f"● Repair {stage}"
                )

        except Exception as exc:
            self.write(
                "\nREPAIR EXCEPTION\n"
                + "=" * 70
                + "\n"
                f"{exc}\n"
            )

            self.status.config(
                text="● Repair failed"
            )

            messagebox.showerror(
                "Repair Error",
                str(exc),
            )

    # ============================================================
    # Display repair result
    # ============================================================

    def display_repair_result(
        self,
        data,
    ):
        self.write(
            "\nREPAIR RESULT\n"
            + "=" * 70
            + "\n"
        )

        self.write(
            f"Success: "
            f"{data.get('success')}\n"
        )

        self.write(
            f"Stage: "
            f"{data.get('stage')}\n"
        )

        self.write(
            f"Message: "
            f"{data.get('message')}\n"
        )

        reproduction = data.get(
            "reproduction"
        )

        if reproduction:
            self.write(
                "\nREPRODUCTION\n"
                + "-" * 70
                + "\n"
            )

            self.write(
                f"Success: "
                f"{reproduction.get('success')}\n"
            )

            self.write(
                f"Exit code: "
                f"{reproduction.get('exit_code')}\n"
            )

            if reproduction.get(
                "output"
            ):
                self.write(
                    f"\n{reproduction.get('output')}\n"
                )

        diagnosis = data.get(
            "diagnosis"
        )

        if diagnosis:
            self.write(
                "\nDIAGNOSIS\n"
                + "-" * 70
                + "\n"
            )

            self.write(
                f"Category: "
                f"{diagnosis.get('category')}\n"
            )

            self.write(
                f"Cause: "
                f"{diagnosis.get('cause')}\n"
            )

        fingerprint = data.get(
            "fingerprint"
        )

        if fingerprint:
            self.write(
                "\nERROR FINGERPRINT\n"
                + "-" * 70
                + "\n"
            )

            for key in (
                "language",
                "error_type",
                "module",
                "package",
                "port",
                "normalized",
            ):
                if fingerprint.get(key) is not None:
                    self.write(
                        f"{key}: "
                        f"{fingerprint.get(key)}\n"
                    )

        root_cause = data.get(
            "root_cause"
        )

        if root_cause:
            self.write(
                "\nROOT CAUSE\n"
                + "-" * 70
                + "\n"
            )

            for key in (
                "code",
                "title",
                "confidence",
                "reason",
            ):
                if root_cause.get(key) is not None:
                    self.write(
                        f"{key}: "
                        f"{root_cause.get(key)}\n"
                    )

        pipeline = data.get(
            "pipeline"
        )

        if pipeline:
            self.write(
                "\nPIPELINE\n"
                + "-" * 70
                + "\n"
            )

            self.write(
                f"Status: "
                f"{pipeline.get('status')}\n"
            )

            self.write(
                f"Completed: "
                f"{pipeline.get('completed')}\n"
            )

            self.write(
                f"Changed: "
                f"{pipeline.get('changed')}\n"
            )

            repair_result = pipeline.get(
                "repair_result"
            )

            if repair_result:
                self.write(
                    f"Repair stage: "
                    f"{repair_result.get('stage')}\n"
                )

                self.write(
                    f"Repair message: "
                    f"{repair_result.get('message')}\n"
                )

            command_verification = pipeline.get(
                "original_command_verification"
            )

            if command_verification:
                self.write(
                    "\nORIGINAL COMMAND VERIFICATION\n"
                    + "-" * 70
                    + "\n"
                )

                self.write(
                    f"Success: "
                    f"{command_verification.get('success')}\n"
                )

                self.write(
                    f"Failure resolved: "
                    f"{command_verification.get('failure_resolved')}\n"
                )

                self.write(
                    f"Exit code: "
                    f"{command_verification.get('exit_code')}\n"
                )

                if command_verification.get(
                    "output"
                ):
                    self.write(
                        f"\n{command_verification.get('output')}\n"
                    )

    # ============================================================
    # Verify original command
    # ============================================================

    def verify(self):
        try:
            project_root = self.get_project_root()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Project",
                str(exc),
            )
            return

        try:
            command = self.parse_command()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Command",
                str(exc),
            )
            return

        if not command:
            messagebox.showwarning(
                "Verification",
                "Enter the original command first.",
            )
            return

        self.status.config(
            text="● Verifying"
        )

        self.write(
            "\nORIGINAL COMMAND VERIFICATION\n"
            + "=" * 70
            + "\n"
        )

        self.write(
            f"Command: "
            f"{' '.join(command)}\n"
        )

        self.write(
            f"Project: "
            f"{project_root}\n\n"
        )

        try:
            verifier = OriginalCommandVerifier()

            result = verifier.verify(
                command=command,
                project_root=project_root,
            )

            data = (
                result.as_dict()
                if hasattr(result, "as_dict")
                else result
            )

            self.write(
                f"Success: "
                f"{data.get('success')}\n"
            )

            self.write(
                f"Failure resolved: "
                f"{data.get('failure_resolved')}\n"
            )

            self.write(
                f"Exit code: "
                f"{data.get('exit_code')}\n"
            )

            self.write(
                f"Duration: "
                f"{data.get('duration_seconds')} seconds\n"
            )

            if data.get("output"):
                self.write(
                    "\nOUTPUT\n"
                    + "-" * 70
                    + "\n"
                )

                self.write(
                    data.get("output")
                )

            if data.get(
                "failure_resolved"
            ):
                self.status.config(
                    text="● Verified"
                )
            else:
                self.status.config(
                    text="● Still failing"
                )

        except Exception as exc:
            self.write(
                f"\nVerification failed:\n{exc}\n"
            )

            self.status.config(
                text="● Verification failed"
            )

    # ============================================================
    # Rollback
    # ============================================================

    def rollback_manifests(self):
        from app.repair.rollback import (
            rollback_project_manifests
        )

        try:
            project_root = self.get_project_root()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Project",
                str(exc),
            )
            return

        if not messagebox.askyesno(
            "Rollback",
            "Restore project manifest files from the "
            "latest FixPilot snapshot?",
        ):
            return

        result = rollback_project_manifests(
            project_root
        )

        self.write(
            "\nROLLBACK\n"
            + "=" * 70
            + "\n"
        )

        self.write(
            result.get(
                "message",
                "Rollback completed.",
            )
            + "\n"
        )

        self.status.config(
            text=(
                "● Rollback complete"
                if result.get("success")
                else "● Rollback unavailable"
            )
        )

    # ============================================================
    # Teach Me
    # ============================================================

    def start_teach_me(self):
        error = self.get_error()

        if not error:
            messagebox.showinfo(
                "Teach Me",
                "Paste an error first.",
            )
            return

        package = None

        if "No module named" in error:
            import re

            match = re.search(
                r"No module named ['\"]([^'\"]+)",
                error,
                re.I,
            )

            if match:
                package = (
                    match.group(1)
                    .split(".")[0]
                )

        steps = (
            build_python_dependency_tutorial(
                package
            )
            if package
            else build_generic_tutorial()
        )

        self.teach_engine = TutorialEngine(
            steps
        )

        def closed():
            self.teach_overlay = None

            if getattr(
                self,
                "teach_controls",
                None,
            ):
                try:
                    self.teach_controls.destroy()
                except Exception:
                    pass

            self.status.config(
                text="● Ready"
            )

        self.teach_overlay = CursorGuideOverlay(
            self.root,
            on_close=closed,
        )

        self.status.config(
            text="● Teach Me"
        )

        self.update_teach_overlay()

        controls = tk.Toplevel(
            self.root
        )

        controls.title(
            "FixPilot Teach Me Controls"
        )

        controls.geometry(
            "430x190"
        )

        controls.attributes(
            "-topmost",
            True,
        )

        tk.Label(
            controls,
            text=(
                "Perform the step yourself, "
                "then continue."
            ),
            font=("Segoe UI", 10, "bold"),
        ).pack(
            pady=(16, 8)
        )

        button_row = tk.Frame(
            controls
        )

        button_row.pack(
            pady=8
        )

        tk.Button(
            button_row,
            text="← Back",
            command=lambda:
                self.teach_back(controls),
        ).pack(
            side="left",
            padx=5,
        )

        tk.Button(
            button_row,
            text="Next →",
            command=lambda:
                self.teach_next(controls),
        ).pack(
            side="left",
            padx=5,
        )

        tk.Button(
            button_row,
            text="Check",
            command=self.teach_check,
        ).pack(
            side="left",
            padx=5,
        )

        tk.Button(
            button_row,
            text="Close",
            command=closed,
        ).pack(
            side="left",
            padx=5,
        )

        tk.Label(
            controls,
            text=(
                "Teach Me never moves the cursor, "
                "clicks, types,\nor runs commands for you."
            ),
            justify="center",
        ).pack(
            pady=8
        )

        self.teach_controls = controls

    # ============================================================
    # Teach Me overlay
    # ============================================================

    def update_teach_overlay(self):
        if not getattr(
            self,
            "teach_overlay",
            None,
        ):
            return

        position = get_cursor_position()

        engine = self.teach_engine

        progress = (
            f"Step "
            f"{min(engine.state.index + 1, len(engine.steps))}"
            f" / "
            f"{len(engine.steps)}"
        )

        self.teach_overlay.update(
            engine.current,
            position,
            progress,
        )

    def teach_next(self, controls):
        if self.teach_engine.is_finished():
            return

        self.teach_engine.next()

        if self.teach_engine.is_finished():
            self.write(
                "\nTEACH ME COMPLETE\n"
                + "=" * 70
                + "\n"
            )

            self.write(
                "All tutorial steps were completed "
                "by the user.\n"
            )

            self.status.config(
                text="● Teach Me complete"
            )

            controls.destroy()

            if getattr(
                self,
                "teach_overlay",
                None,
            ):
                self.teach_overlay.close()

            return

        self.update_teach_overlay()

    def teach_back(self, controls):
        self.teach_engine.back()
        self.update_teach_overlay()

    def teach_check(self):
        result = (
            self.teach_engine.check_current()
        )

        if result is None:
            self.write(
                "\nTeach Me: manual confirmation "
                "required for this step.\n"
            )

        elif result:
            self.write(
                "\nTeach Me: check passed.\n"
            )

        else:
            self.write(
                "\nTeach Me: check did not pass yet.\n"
            )

        self.update_teach_overlay()


# ================================================================
# APPLICATION ENTRY POINT
# ================================================================

def run():
    root = tk.Tk()

    App(root)

    root.mainloop()


if __name__ == "__main__":
    run()