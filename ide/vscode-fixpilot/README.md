# FixPilot VS Code Integration

## 1. Start the local bridge

From the FixPilot V0.7 root:

```bat
python -m app.bridge.server
```

It listens only on:

```text
http://127.0.0.1:8765
```

## 2. Install the extension locally

In VS Code:

1. Open `ide/vscode-fixpilot`.
2. Run `npm install` only if you add packaging/build tooling later; V0.7 has no runtime npm dependency.
3. Press `F5` from an Extension Development Host setup, or package it with VSCE later.

## Commands

Open Command Palette:

- `FixPilot: Analyze Selected Error`
- `FixPilot: Analyze Terminal Error`

The extension sends only the selected/pasted error and workspace path to the local bridge. The bridge scans the project locally.

## Safety

The VS Code panel is analysis-only.

Repairs still require the FixPilot desktop approval workflow.
