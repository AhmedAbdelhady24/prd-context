"""Shared advisory hooks: bounded JSON input, CLI reuse, fail open."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))


def cli(*args, timeout=10):
    # Use the already-installed environment, avoiding uv startup/network on each prompt.
    executable = ROOT / "server/.venv/bin/prd-mcp"
    return json.loads(subprocess.run([str(executable), *args], capture_output=True,
                                    text=True, check=True, timeout=timeout).stdout)


def run(tool, behavior, payload):
    from hook_io import normalize
    from prd_context.index import paths, file_lock
    data = normalize(payload)
    root, db = paths()
    session = hashlib.sha256(data["session"].encode()).hexdigest()[:24]
    statefile = db.parent / f"hook-{tool}-{session}.json"
    with file_lock(statefile.with_suffix(".lock"), timeout=.04 if behavior == "prompt" else 10):
        return run_locked(tool, behavior, data, root, statefile)


def run_locked(tool, behavior, data, root, statefile):
    from hook_io import output
    from prd_context.index import status
    state = json.loads(statefile.read_text()) if statefile.exists() else {}
    message = ""
    if behavior == "session":
        cli("reindex")
        message = (ROOT / "core/PRD_CONTEXT.md").read_text()
    elif behavior == "prompt":
        # ponytail: keyword gate, tune from real trigger evaluations if false matches matter.
        business = any(word in data["prompt"].lower() for word in
                       ("req-", "business rule", "acceptance", "password policy", "refund", "session policy", "mfa"))
        state["business"] = business
        if business:
            pointers = cli("search", data["prompt"], "--limit", "3", "--timeout", ".10", timeout=.18)
            message = "PRD pointers (verify through prd_answer_context): " + ", ".join(p["citation"] for p in pointers)
    elif behavior in ("edit", "warning"):
        edited = [file for file in data["files"] if file.is_relative_to(root) and file.suffix == ".md"]
        if edited and behavior == "edit":
            cli("reindex")
            state["prd_edited"] = True
        elif behavior == "warning":
            if any(file.exists() and status(file.read_text()) == "approved" for file in edited):
                message = "Approved PRD edit: use explicitly invoked prd-author, preserve REQ IDs and review status; get owner approval before changing business rules."
    elif behavior == "stop" and not data["stop_active"]:
        if (state.get("business") or state.get("prd_edited")) and not state.get("reminded"):
            message = "Before finishing business work, include REQ IDs and PRD source citations in the implementation handoff, or say not documented."
            state["reminded"] = True
    if behavior == "prompt":
        state["reminded"] = False
    statefile.parent.mkdir(parents=True, exist_ok=True)
    temp = statefile.with_suffix(f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(state))
    temp.replace(statefile)
    if tool == "cursor" and message and behavior in ("prompt", "warning"):
        print(message, file=sys.stderr)  # advisory diagnostic; documented schema has no allow-context field
    return output(tool, behavior, data["event"], message)


if __name__ == "__main__":
    tool = sys.argv[1] if len(sys.argv) > 1 else "claude"
    behavior = sys.argv[2] if len(sys.argv) > 2 else ""
    output_adapter = None
    try:
        from hook_io import output as output_adapter
        if tool not in ("claude", "cursor", "codex") or behavior not in ("session", "prompt", "edit", "warning", "stop"):
            raise ValueError("unknown hook arguments")
        raw = sys.stdin.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("oversize hook input")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("expected JSON object")
        result = run(tool, behavior, payload)
    except Exception as exc:
        print(f"prd-context hook skipped: {type(exc).__name__}", file=sys.stderr)
        if output_adapter is None:
            # Missing adapter: non-2 hook failure follows each host's documented fail-open behavior.
            raise SystemExit(1)
        result = output_adapter(tool, behavior, "", "")
    print(json.dumps(result))
