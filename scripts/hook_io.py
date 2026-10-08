"""Only tool-specific payload/output translation lives here."""
import json
import re
from pathlib import Path


def normalize(payload):
    roots = payload.get("workspace_roots") or []
    cwd = Path(payload.get("cwd") or (roots[0] if roots else Path.cwd()))
    inputs = payload.get("tool_input") or {}
    if isinstance(inputs, str):
        try:
            inputs = json.loads(inputs)
        except ValueError:
            inputs = {"command": inputs}
    if not isinstance(inputs, dict):
        inputs = {}
    files = [payload.get("file_path"), inputs.get("file_path"), inputs.get("path")]
    command = inputs.get("command", inputs.get("patch", ""))
    if isinstance(command, str):
        files += re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", command, re.M)
    return {"event": payload.get("hook_event_name", ""),
            "prompt": payload.get("prompt", ""), "cwd": cwd,
            "files": [(cwd / f).resolve() for f in files if isinstance(f, str) and f],
            "session": str(payload.get("session_id") or payload.get("conversation_id") or "unknown"),
            "stop_active": bool(payload.get("stop_hook_active") or payload.get("loop_count", 0)),
            "last_message": payload.get("last_assistant_message", "")}


def output(tool, behavior, event, message):
    if tool == "cursor":
        if behavior == "session":
            return {"additional_context": message}
        if behavior == "prompt":
            # Cursor documents no model-context field here; only a blocked-prompt message.
            return {"continue": True}
        if behavior == "warning":
            return {"permission": "allow"}
        if behavior == "stop":
            return {"followup_message": message} if message else {}
        return {}
    if not message:
        return {}
    if behavior == "stop":
        return {"systemMessage": message}  # advisory; never force a continuation
    result = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": message}}
    if behavior == "warning":
        result["systemMessage"] = message
    return result
