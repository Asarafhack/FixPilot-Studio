from app.repair.executor import execute_plan
from app.repair.snapshot import create_project_snapshot, compare_project_snapshot
from app.repair.verifier import verify_plan

class RepairService:
    def __init__(self, project_root="."):
        self.project_root = project_root

    def prepare(self):
        return create_project_snapshot(self.project_root)

    def execute(self, plan):
        result = execute_plan(plan, cwd=self.project_root)
        changes = compare_project_snapshot(self.project_root)
        return {"execution": result, "changes": changes}

    def verify(self, plan, original_command=None):
        return verify_plan(
            plan,
            [],
            cwd=self.project_root,
            original_command=original_command,
        )
