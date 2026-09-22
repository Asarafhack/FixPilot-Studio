import json
import os
import urllib.request

SYSTEM_PROMPT = """You are FixPilot, a developer-environment repair assistant.
Analyze the supplied error and project context.
Do not invent files, commands, package versions, or documentation.
Return concise structured JSON with category, root_cause, confidence,
explanation, and safe_next_step.
Never propose destructive commands.
"""

def _local_fallback(reasoning):
    diagnosis = reasoning["diagnosis"]
    hints = reasoning["project_hints"]
    next_step = (
        hints[0] if hints
        else "Use the generated repair plan and approve only a known safe action."
    )
    return {
        "mode": "local",
        "category": diagnosis["category"],
        "root_cause": diagnosis["cause"],
        "confidence": diagnosis["confidence"],
        "explanation": diagnosis["recommendation"],
        "safe_next_step": next_step,
    }

def analyze_with_ai(reasoning):
    endpoint = os.getenv("FIXPILOT_LLM_ENDPOINT")
    api_key = os.getenv("FIXPILOT_LLM_API_KEY")

    if not endpoint or not api_key:
        return _local_fallback(reasoning)

    payload = {
        "system": SYSTEM_PROMPT,
        "error": reasoning["diagnosis"],
        "project": reasoning["project_summary"][:16000],
        "evidence": reasoning["evidence"][:5],
    }

    try:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        return {"mode": "remote", "result": data}
    except Exception as exc:
        return {
            "mode": "local_fallback",
            "warning": f"LLM request failed safely: {exc}",
            **_local_fallback(reasoning),
        }
