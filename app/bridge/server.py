import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.agent.project_reasoner import reason_about_project
from app.ai.reasoner import analyze_with_ai

HOST = "127.0.0.1"
PORT = 8765

class Handler(BaseHTTPRequestHandler):
    server_version = "FixPilotBridge/0.7"

    def _send(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "service": "fixpilot-bridge", "version": "0.7"})
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/analyze":
            self._send(404, {"error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                self._send(413, {"error": "payload_too_large"})
                return

            data = json.loads(self.rfile.read(length).decode("utf-8"))
            error = str(data.get("error", "")).strip()
            project = str(data.get("project", ".")).strip()

            if not error:
                self._send(400, {"error": "error_text_required"})
                return

            project_path = Path(project).resolve()
            if not project_path.exists() or not project_path.is_dir():
                self._send(400, {"error": "project_directory_not_found"})
                return

            reasoning = reason_about_project(error, project_path)
            ai = analyze_with_ai(reasoning)

            self._send(200, {
                "diagnosis": reasoning["diagnosis"],
                "project": reasoning["context"],
                "project_hints": reasoning["project_hints"],
                "evidence": reasoning["evidence"],
                "ai": ai,
                "repair_plan": reasoning["diagnosis"].get("repair_plan", []),
            })
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid_json"})
        except Exception as exc:
            self._send(500, {"error": "analysis_failed", "detail": str(exc)})

def run():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"FixPilot Bridge listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    run()
