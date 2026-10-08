"""Native Codex lifecycle check; requires prior project and /hooks trust.

Run with server/.venv/bin/python scripts/check_codex_hooks.py.
Uses a disposable approved fixture and restores the index in finally.
"""
import hashlib
import json
import os
import queue
import sqlite3
import subprocess
import threading
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evals/cross_agent"


def main():
    before = {p: p.read_bytes() for p in (ROOT / "prds").rglob("*.md")}
    fixture = ROOT / "prds" / f"hook-check-{uuid.uuid4().hex}.md"
    fixture.write_text('---\nstatus: approved\n---\n# Disposable hook fixture\n\n'
                       '## REQ-HOOK-001\nGiven a synthetic test, then marker is BEFORE.\n')
    events = []
    inbox = queue.Queue()
    proc = None

    def send(value):
        proc.stdin.write(json.dumps(value) + "\n")
        proc.stdin.flush()

    def receive(predicate, timeout=240):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                value = inbox.get(timeout=min(1, max(.01, deadline - time.monotonic())))
            except queue.Empty:
                continue
            if value is None:
                raise RuntimeError("Codex app-server exited")
            events.append(value)
            if "method" in value and "id" in value:
                raise RuntimeError(f"Unexpected approval request: {value['method']}")
            if predicate(value):
                if "error" in value:
                    raise RuntimeError(str(value["error"]))
                return value
        raise TimeoutError("Native Codex hook check timed out")

    def reader():
        for line in proc.stdout:
            inbox.put(json.loads(line))
        inbox.put(None)

    try:
        proc = subprocess.Popen(["codex", "app-server", "--stdio"], cwd=ROOT,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True, bufsize=1)
        threading.Thread(target=reader, daemon=True).start()
        send({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "prd-native-hook-check", "version": "1"},
            "capabilities": {"experimentalApi": True}}})
        receive(lambda v: v.get("id") == 1, 20)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "thread/start", "params": {
            "cwd": str(ROOT), "sandbox": "workspace-write", "ephemeral": True}})
        started = receive(lambda v: v.get("id") == 2, 30)
        thread_id = started["result"]["thread"]["id"]
        prompt = ("Explicitly invoke $prd-author for this authorized synthetic hook test. "
                  f"Only edit {fixture.relative_to(ROOT)} using apply_patch: replace BEFORE "
                  "with AFTER. Owner approves this exact fixture-only change. Preserve its "
                  "approved status and REQ ID for this test. Read the skill and query the "
                  "PRD tool before editing; make no MCP calls after editing and do not run "
                  "reindex yourself. Do not edit any other file. Finish after this one patch.")
        send({"id": 3, "method": "turn/start", "params": {"threadId": thread_id,
              "input": [{"type": "text", "text": prompt, "text_elements": []}]}})
        receive(lambda v: v.get("id") == 3, 30)
        completed = receive(lambda v: v.get("method") == "turn/completed")
        if completed["params"]["turn"]["status"] != "completed":
            raise RuntimeError(str(completed))
        items = [v["params"]["item"] for v in events if v.get("method") == "item/completed"]
        patches = [i for i, item in enumerate(items) if item.get("type") == "fileChange"]
        if len(patches) != 1 or any(item.get("type") == "mcpToolCall"
                                     for item in items[patches[0] + 1:]):
            raise RuntimeError("Expected one patch and no later MCP query")
        if any("reindex" in item.get("command", "") for item in items):
            raise RuntimeError("Agent ran reindex directly")
        hooks = [v["params"]["run"] for v in events
                 if v.get("method") == "hook/completed"
                 and v["params"]["run"]["sourcePath"] == str(ROOT / ".codex/hooks.json")]
        required = {"sessionStart", "userPromptSubmit", "preToolUse", "postToolUse", "stop"}
        observed = {h["eventName"] for h in hooks if h["status"] == "completed"}
        if not required <= observed:
            raise RuntimeError(f"Missing completed project hooks: {required - observed}")
        warnings = [e["text"] for h in hooks if h["eventName"] == "preToolUse" for e in h["entries"]]
        if not any("Approved PRD edit" in text for text in warnings):
            raise RuntimeError("Approved edit warning was not delivered")
        if "AFTER" not in fixture.read_text():
            raise RuntimeError("Fixture was not patched")
        with sqlite3.connect(ROOT / ".cache/prd_index.db") as db:
            digest = db.execute("SELECT digest FROM files WHERE path=?",
                                (fixture.name,)).fetchone()
        if not digest or digest[0] != hashlib.sha256(fixture.read_bytes()).hexdigest():
            raise RuntimeError("PostToolUse did not refresh the fixture digest")
        state_path = ROOT / ".cache" / ("hook-codex-" + hashlib.sha256(
            thread_id.encode()).hexdigest()[:24] + ".json")
        state = json.loads(state_path.read_text())
        if not state.get("prd_edited"):
            raise RuntimeError("Native patch payload was not recognized")
        report = {"thread_id": thread_id, "hooks": hooks, "session_state": state,
                  "index_matches_patch": True, "approved_warning_delivered": True}
        (OUT / "codex-native-edit-hooks.json").write_text(json.dumps(report, indent=2) + "\n")
        print("PASS: all five native project hooks; approved edit warning; index refreshed")
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        (OUT / "codex-native-edit-hooks.jsonl").write_text(
            "".join(json.dumps(v) + "\n" for v in events))
        fixture.unlink(missing_ok=True)
        subprocess.run([str(ROOT / "server/.venv/bin/prd-mcp"), "reindex"], cwd=ROOT,
                       env=os.environ | {"PRD_DIR": str(ROOT / "prds"),
                       "PRD_DB": str(ROOT / ".cache/prd_index.db")}, check=True,
                       stdout=subprocess.DEVNULL)
        after = {p: p.read_bytes() for p in (ROOT / "prds").rglob("*.md")}
        if after != before:
            raise RuntimeError("Existing PRD corpus changed during the check")


if __name__ == "__main__":
    main()
