# FixPilot Studio V1.0 — Windows Setup

## Option A — packaged build

If you received the packaged `dist/FixPilot-Studio` folder:

1. Open the folder.
2. Run `FixPilot-Studio.exe`.
3. Windows may show a security warning for an unsigned locally built executable. Verify the source/build before allowing it.

## Option B — build locally

Requirements:
- Windows
- Python 3.10+
- Internet access only while installing PyInstaller

Run:

```bat
build\install_build_tools.bat
build\build_windows.bat
```

The result is:

```text
dist\FixPilot-Studio\
    FixPilot-Studio.exe
    ...
```

Then run:

```text
FixPilot-Studio.exe
```

## Runtime data

Mutable logs and snapshots are stored under the user's local application-data directory rather than inside the packaged application.

## Security model

V1.0 does not grant the AI unrestricted operating-system access.

The application keeps:

- allowlisted repair actions
- explicit approval
- `shell=False`
- command timeouts
- audit logging
- project snapshots
- verification
- conservative rollback
- local VS Code bridge
- human-controlled Teach Me mode
