const vscode = require("vscode");

function bridgeUrl() {
  return vscode.workspace
    .getConfiguration("fixpilot")
    .get("bridgeUrl", "http://127.0.0.1:8765");
}

async function analyze(errorText) {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders) {
    vscode.window.showErrorMessage("Open a project folder first.");
    return;
  }

  if (!errorText || !errorText.trim()) {
    vscode.window.showWarningMessage("Select or provide a terminal error first.");
    return;
  }

  const response = await fetch(`${bridgeUrl()}/analyze`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      error: errorText,
      project: folders[0].uri.fsPath
    })
  });

  if (!response.ok) {
    throw new Error(`FixPilot bridge returned HTTP ${response.status}`);
  }

  const data = await response.json();
  const panel = vscode.window.createWebviewPanel(
    "fixpilotResult",
    "FixPilot Analysis",
    vscode.ViewColumn.Beside,
    {enableScripts: false}
  );

  const diagnosis = data.diagnosis || {};
  const ai = data.ai || {};
  const hints = (data.project_hints || [])
    .map(x => `<li>${escapeHtml(x)}</li>`).join("");
  const plan = (data.repair_plan || [])
    .map(x => `<li><b>${escapeHtml(x.title || "")}</b> — ${escapeHtml(x.action || "")}</li>`)
    .join("");

  panel.webview.html = `
    <!doctype html>
    <html>
      <body>
        <h2>FixPilot</h2>
        <h3>${escapeHtml(diagnosis.category || "Diagnosis")}</h3>
        <p><b>Cause:</b> ${escapeHtml(diagnosis.cause || "")}</p>
        <p><b>Confidence:</b> ${escapeHtml(diagnosis.confidence || "")}</p>
        <p><b>AI mode:</b> ${escapeHtml(ai.mode || "")}</p>
        <h3>Project hints</h3><ul>${hints || "<li>None</li>"}</ul>
        <h3>Repair plan</h3><ul>${plan || "<li>No supported repair</li>"}</ul>
        <p>FixPilot does not execute repairs from this panel. Use the desktop app approval flow.</p>
      </body>
    </html>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand("fixpilot.analyzeSelection", async () => {
      const editor = vscode.window.activeTextEditor;
      const selected = editor ? editor.document.getText(editor.selection) : "";
      try {
        await analyze(selected);
      } catch (err) {
        vscode.window.showErrorMessage(`FixPilot: ${err.message}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("fixpilot.analyzeTerminal", async () => {
      const input = await vscode.window.showInputBox({
        prompt: "Paste the terminal error for FixPilot"
      });
      if (!input) return;
      try {
        await analyze(input);
      } catch (err) {
        vscode.window.showErrorMessage(`FixPilot: ${err.message}`);
      }
    })
  );
}

function deactivate() {}

module.exports = {activate, deactivate};
