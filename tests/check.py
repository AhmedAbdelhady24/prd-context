"""Run: server/.venv/bin/python tests/check.py"""
import asyncio
import json
import os
import subprocess
import shutil
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "server"), str(ROOT / "scripts")]
from prd_context.index import answer_context, reindex, search, status
from hook_io import normalize, output
from hooks import run as hook


async def protocol():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=str(ROOT / "server/.venv/bin/prd-mcp"), env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {t.name for t in tools.tools} == {"prd_answer_context", "prd_reindex"}
            result = await session.call_tool("prd_answer_context", {"query": "REQ-AUTH-001"})
            assert not result.isError and "5 failed" in str(result)
            schemas = [t.model_dump(mode="json", exclude_none=True) for t in tools.tools]
            (ROOT / "evals/tool-schemas.json").write_text(json.dumps(schemas, indent=2) + "\n")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        corpus = Path(tmp) / "prds"
        corpus.mkdir()
        approved = "---\nstatus: approved\n---\n## REQ-AUTH-001 Login\n5 failed attempts.\n"
        (corpus / "current.md").write_text(approved)
        (corpus / "old.md").write_text(approved.replace("approved", "superseded").replace("5 failed", "3 failed"))
        (corpus / "draft.md").write_text(approved.replace("approved", "draft"))
        (corpus / "missing.md").write_text("## REQ-AUTH-001 Login\nBAD\n")
        os.environ.update(PRD_DIR=str(corpus), PRD_DB=str(Path(tmp) / "index.db"))
        assert reindex()["changed"] == 4
        assert reindex()["changed"] == 0
        rows = search("REQ-AUTH-001")
        assert len(rows) == 1 and rows[0]["citation"].endswith("/current.md:4-5")
        assert not search("REQ-AUTH-0010")
        assert not answer_context("REQ-MISSING-999")["documented"]
        assert status("---\nstatus: approved\nstatus: draft\n---\n") == "unknown"
        assert status('---\nstatus: approved\nstatus: "draft"\n---\n') == "unknown"
        (corpus / "another.md").write_text(approved.replace("REQ-AUTH-001", "REQ-AUTH-002"))
        reindex()
        assert len(search("REQ-AUTH-001 and REQ-AUTH-002")) == 2
        (corpus / "current.md").write_text(approved.replace("approved", "superseded"))
        assert search("failed", limit=1)[0]["source"].endswith("/another.md")
        other = Path(tmp) / "other"
        other.mkdir()
        os.environ["PRD_DIR"] = str(other)
        try:
            search("REQ-AUTH-001")
            raise AssertionError("wrong corpus accepted")
        except ValueError:
            pass
        os.environ["PRD_DIR"] = str(corpus)
        (corpus / "another.md").unlink()
        (corpus / "current.md").write_text(approved)
        reindex()
        warning = hook("codex", "warning", {"cwd": str(corpus), "session_id": "unit",
                       "hook_event_name": "PreToolUse", "tool_input": {"command": "*** Update File: current.md\n"}})
        assert "Approved PRD edit" in warning["systemMessage"]
        cursor = hook("cursor", "warning", {"workspace_roots": [str(corpus)], "session_id": "unit", "file_path": "current.md"})
        assert cursor == {"permission": "allow"}
        (corpus / "current.md").write_text(approved.replace("5 failed", "7 failed"))
        hook("cursor", "edit", {"workspace_roots": [str(corpus)], "session_id": "unit", "file_path": "current.md"})
        assert "7 failed" in search("REQ-AUTH-001")[0]["text"]
        reminder = hook("cursor", "stop", {"session_id": "unit", "loop_count": 0})
        assert "REQ IDs" in reminder["followup_message"]
        assert hook("cursor", "stop", {"session_id": "unit", "loop_count": 1}) == {}
        hook("cursor", "prompt", {"session_id": "concurrent", "prompt": "REQ-AUTH-001"})
        with ThreadPoolExecutor(max_workers=4) as pool:
            reminders = list(pool.map(lambda _: hook("cursor", "stop", {"session_id": "concurrent", "loop_count": 0}), range(4)))
            assert sum(bool(value.get("followup_message")) for value in reminders) == 1
        (corpus / "current.md").write_text(approved)
        reindex()
        for query in ("", "x" * 4001):
            try:
                search(query)
                raise AssertionError("invalid query accepted")
            except ValueError:
                pass
        assert search('" OR 1=1 --') == []
        (corpus / "current.md").write_text(approved.replace("approved", "superseded"))
        assert not search("REQ-AUTH-001"), "stale superseded document leaked"
        (corpus / "current.md").write_text(approved)
        processes = [subprocess.Popen([sys.executable, "-m", "prd_context.app", "reindex"],
                     env={**os.environ, "PYTHONPATH": str(ROOT / "server")}, stdout=subprocess.PIPE) for _ in range(8)]
        for process in processes:
            process.communicate(timeout=15)
            assert process.returncode == 0
        assert len(search("REQ-AUTH-001")) == 1
        (corpus / "current.md").unlink()
        assert not search("REQ-AUTH-001")
        assert reindex()["removed"] == 1
        (corpus / "current.md").symlink_to(ROOT / "prds/auth.md")
        reindex()
        assert not search("REQ-AUTH-001"), "symlink escaped corpus"
    os.environ.update(PRD_DIR=str(ROOT / "prds"), PRD_DB=str(ROOT / ".cache/prd_index.db"))
    reindex()
    patch = "*** Begin Patch\n*** Update File: prds/auth.md\n@@\n-x\n+y\n*** Move to: prds/moved.md\n*** End Patch"
    data = normalize({"cwd": str(ROOT), "tool_input": {"command": patch}})
    assert data["files"] == [(ROOT / "prds/auth.md").resolve(), (ROOT / "prds/moved.md").resolve()]
    assert normalize({"workspace_roots": [str(ROOT)], "file_path": "prds/auth.md"})["files"][0] == ROOT / "prds/auth.md"
    for tool in ("claude", "cursor", "codex"):
        command = [sys.executable, str(ROOT / "scripts/hooks.py"), tool, "prompt"]
        bad = subprocess.run(command, input="{invalid", text=True, capture_output=True, check=True)
        assert json.loads(bad.stdout) == output(tool, "prompt", "", "")
        started = time.monotonic()
        good = subprocess.run(command, input=json.dumps({"session_id": "check", "prompt": "REQ-AUTH-001", "hook_event_name": "UserPromptSubmit"}), text=True, capture_output=True, check=True)
        elapsed = time.monotonic() - started
        assert elapsed < .300, f"{tool} prompt hook {elapsed:.3f}s"
        value = json.loads(good.stdout)
        assert ("auth.md:7-11" in str(value)) if tool != "cursor" else value == {"continue": True}
        print(f"{tool} prompt hook {elapsed * 1000:.1f} ms")
    asyncio.run(protocol())
    subprocess.run([sys.executable, str(ROOT / "scripts/sync_adapters.py"), "--check"], check=True)
    with tempfile.TemporaryDirectory(prefix="prd paths with spaces ") as tmp:
        clone = Path(tmp)
        shutil.copytree(ROOT / "core", clone / "core")
        (clone / "scripts").mkdir()
        for script in ("sync_adapters.py", "hooks.py", "hook_io.py"):
            shutil.copy2(ROOT / "scripts" / script, clone / "scripts" / script)
        shutil.copytree(ROOT / "server/prd_context", clone / "server/prd_context")
        shutil.copy2(ROOT / ".adapter-files.json", clone / ".adapter-files.json")
        for rel in json.loads((ROOT / ".adapter-files.json").read_text()):
            (clone / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, clone / rel)
        command = [sys.executable, str(clone / "scripts/sync_adapters.py")]
        subprocess.run(command + ["--check"], check=True)
        shared = clone / "core/PRD_CONTEXT.md"
        shared.write_text(shared.read_text() + "Extra line\n")
        optimized = subprocess.run([sys.executable, "-O", str(clone / "scripts/sync_adapters.py")], capture_output=True)
        assert optimized.returncode != 0 and b"10 lines" in optimized.stderr
        shared.write_text((ROOT / "core/PRD_CONTEXT.md").read_text())
        subprocess.run(command, check=True)
        skill = clone / ".agents/skills/prd-consult/SKILL.md"
        skill.write_text(skill.read_text() + "DRIFT\n")
        assert subprocess.run(command + ["--check"], capture_output=True).returncode == 1
        (clone / "AGENTS.md").write_text((clone / "AGENTS.md").read_text() + "\n## Other instructions\nKeep this section.\n")
        subprocess.run(command, check=True)
        assert "Keep this section." in (clone / "AGENTS.md").read_text()
        subprocess.run(command + ["--check"], check=True)
        hook_command = json.loads((clone / ".cursor/hooks.json").read_text())["hooks"]["sessionStart"][0]["command"]
        proc = subprocess.run(hook_command, input='{}', text=True, shell=True, capture_output=True)
        assert proc.returncode == 0 and json.loads(proc.stdout) == {"additional_context": ""}
        missing_args = subprocess.run([sys.executable, str(clone / "scripts/hooks.py")], input='{}', text=True, capture_output=True)
        assert missing_args.returncode == 0 and json.loads(missing_args.stdout) == {}
        fake_cli = clone / "server/.venv/bin/prd-mcp"
        fake_cli.parent.mkdir(parents=True)
        fake_cli.write_text('#!' + sys.executable + '\nprint("{}")\n')
        fake_cli.chmod(0o755)
        (clone / "core/PRD_CONTEXT.md").unlink()
        broken = subprocess.run(hook_command, input='{}', text=True, shell=True, capture_output=True)
        assert broken.returncode == 0 and json.loads(broken.stdout) == {"additional_context": ""}
    print("PASS: freshness, exclusion, citations, idempotence, 8-process locking, hook normalization/fail-open/latency, MCP protocol, adapter drift")


if __name__ == "__main__":
    main()
