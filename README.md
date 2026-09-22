# FixPilot Studio V1.0

## AI-native developer environment repair assistant

FixPilot Studio is a focused Windows developer tool that helps diagnose and repair common project-environment failures.

It is **not a VS Code clone**.

Its unique workflow is:

```text
DETECT
  ↓
UNDERSTAND
  ↓
EXPLAIN
  ↓
PLAN
  ↓
APPROVE
  ↓
REPAIR
  ↓
VERIFY
  ↓
TEACH
```

## V1.0 capabilities

### Diagnostics
- Windows environment
- Python
- Node.js
- npm
- Git
- common development ports

### RAG
Local trusted troubleshooting knowledge for supported error classes.

### Project-aware reasoning
Understands:
- project structure
- package.json
- requirements.txt
- pyproject.toml
- source-file context

### Controlled repair
Currently supports selected low-risk package repairs and guidance.

### Safety
- explicit user approval
- allowlisted actions
- package-name validation
- `shell=False`
- execution timeout
- bounded command output
- audit log

### Verification
Can check whether the repaired environment actually changed and optionally re-run the original command.

### Snapshots / rollback
Important project manifests can be snapshotted before repair. Conservative rollback restores only those captured manifest files.

### VS Code integration
A local bridge allows a VS Code extension to send an error and workspace path to FixPilot.

### Teach Me
Guides the user step-by-step while keeping all desktop interaction under human control.

## Production packaging

Build a Windows application with:

```bat
build\install_build_tools.bat
build\build_windows.bat
```

Output:

```text
dist\FixPilot-Studio\
```

The packaged application is a PyInstaller build.

## Architecture

```text
                 ┌─────────────────────┐
                 │   FixPilot Studio   │
                 │     Windows UI      │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              ↓             ↓             ↓
        Diagnostics       RAG       Project Context
              │             │             │
              └─────────────┼─────────────┘
                            ↓
                       AI Reasoner
                            ↓
                     Repair Planner
                            ↓
                     Safety Validator
                            ↓
                      User Approval
                            ↓
                    Controlled Executor
                            ↓
                  Snapshot / Audit Log
                            ↓
                       Verification
                            ↓
                    Teach Me / Guidance
```

## V1.0 boundary

The AI is not allowed to become an unrestricted shell agent.

Future capabilities should continue to use:

```text
AI proposal
   ↓
structured action
   ↓
policy/safety validation
   ↓
user approval
   ↓
execution
   ↓
verification
```

## Roadmap after V1.0

- V1.1 — richer error parsers
- V1.2 — deeper dependency graph analysis
- V1.3 — smarter verification
- V1.4 — controlled computer-use experiments
- V1.5 — plugin architecture
- V2.0 — broader developer-environment automation
"# FixPilot-Studio" 
