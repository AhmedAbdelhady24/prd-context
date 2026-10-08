"""Noninteractive read-only independent agent checks; raw transcripts + explicit verdicts.

Run with the native authenticated CLIs. Trust Codex hooks separately via /hooks.
No auto trust bypass, authoring, or global configuration changes.
"""
import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evals/cross_agent"
TOOLS = ("claude", "cursor", "codex")


def command(tool, prompt):
    if tool == "codex":
        # Explicit MCP overrides let headless evals work without changing user's project trust.
        config = ['-c', 'mcp_servers.prd.command="uv"', '-c', 'mcp_servers.prd.args=' + json.dumps(["run", "--directory", str(ROOT / "server"), "prd-mcp"]),
                  '-c', 'mcp_servers.prd.env.PRD_DIR=' + json.dumps(str(ROOT / "prds")),
                  '-c', 'mcp_servers.prd.env.PRD_DB=' + json.dumps(str(ROOT / ".cache/prd_index.db"))]
        return ["codex", "exec", "--ignore-user-config", "--skip-git-repo-check", "--sandbox", "read-only", "--ephemeral", "--json", "--color", "never", *config, prompt]
    if tool == "cursor":
        return ["cursor-agent", "-p", "--mode", "ask", "--trust", "--approve-mcps", "--workspace", str(ROOT), "--output-format", "stream-json", prompt]
    return ["claude", "-p", "--plugin-dir", str(ROOT / "prd-context"), "--strict-mcp-config", "--mcp-config", str(ROOT / "prd-context/.mcp.json"),
            "--setting-sources", "project", "--tools", "Read,Glob,Grep,Skill", "--allowedTools", "Read,Glob,Grep,Skill,mcp__prd__prd_answer_context,mcp__plugin_prd-context_prd__prd_answer_context",
            "--output-format", "stream-json", "--verbose", prompt]


def response(raw):
    messages = []
    for line in raw.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if item.get("type") == "item.completed" and item.get("item", {}).get("type") == "agent_message":
            messages.append(item["item"]["text"])
        elif item.get("type") == "assistant":
            content = item.get("message", {}).get("content", [])
            messages.extend(c.get("text", "") for c in content if c.get("type") == "text")
        elif item.get("type") == "result" and isinstance(item.get("result"), str):
            messages.append(item["result"])
    return "\n".join(messages)


def run(tool, case, timeout=180):
    name = f"{tool}-{case['id']}"
    started = time.monotonic()
    try:
        proc = subprocess.run(command(tool, case["question"]), cwd=ROOT, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        raw, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout or b""
        stderr = exc.stderr or b""
        raw = raw.decode(errors="replace") if isinstance(raw, bytes) else raw
        stderr = stderr.decode(errors="replace") if isinstance(stderr, bytes) else stderr
        code = 124
    (OUT / f"{name}.jsonl").write_text(raw)
    (OUT / f"{name}.stderr").write_text(stderr)
    final = response(raw)
    (OUT / f"{name}.txt").write_text(final)
    # Tool-call trace required: textual claims to have used MCP/skills do not count.
    calls, mcp_used, mcp_succeeded, prd_calls = [], False, False, set()
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        item = event.get("item", {})
        if item.get("type") == "command_execution":
            calls.append(item.get("command", ""))
        if item.get("type") == "mcp_tool_call" and item.get("tool") == "prd_answer_context":
            mcp_used = True
            mcp_succeeded |= item.get("status") == "completed" and item.get("result") is not None and not item.get("error")
        if event.get("type") == "tool_call":
            call = event.get("tool_call", {})
            read = call.get("readToolCall", {}).get("args", {}).get("path", "")
            if read:
                calls.append(read)
            shell = call.get("shellToolCall", {}).get("args", {}).get("command", "")
            if shell:
                calls.append(shell)
            mcp = call.get("mcpToolCall", {})
            if mcp.get("args", {}).get("toolName") == "prd_answer_context":
                mcp_used = True
                prd_calls.add(event.get("call_id"))
            if event.get("call_id") in prd_calls and event.get("subtype") == "completed" and mcp.get("result"):
                mcp_succeeded |= "success" in mcp["result"]
        if event.get("type") == "assistant":
            for content in event.get("message", {}).get("content", []):
                if content.get("type") == "tool_use":
                    calls.append(json.dumps(content))
                    if "prd_answer_context" in content.get("name", ""):
                        mcp_used = True
                        prd_calls.add(content.get("id"))
        if event.get("type") == "user":
            for content in event.get("message", {}).get("content", []):
                if content.get("type") == "tool_result" and content.get("tool_use_id") in prd_calls and not content.get("is_error") and "evidence" in str(content.get("content")):
                    mcp_succeeded = True
    evidence = '\n'.join(calls)
    skill_used = bool(re.search(r'prd-consult[/\\]SKILL\.md|"skill"\s*:\s*"(?:prd-context:)?prd-consult"', evidence))
    result = {"tool": tool, "id": case["id"], "exit_code": code, "seconds": round(time.monotonic()-started, 2),
              "mcp_observed": mcp_used, "mcp_succeeded": mcp_succeeded, "skill_observed": skill_used, "response": final}
    if "required" in case:
        result["answer_matches"] = all(term.lower() in final.lower() for term in case["required"])
        # Citation validator is deliberately exact for the fixture. Variants require manual review.
        expected = case.get("citation")
        normalized = final.replace("`", "").replace("prds/", "").replace("–", "-").replace("—", "-")
        if expected:
            source, lines = expected.split(":")
            alternate = re.search(re.escape(source) + r"(?:\*\*|`|\]|,|\s)*\s*(?:lines?\s*)?" + re.escape(lines), normalized, re.I)
            result["citation_matches"] = expected in normalized or bool(alternate)
        else:
            result["citation_matches"] = None
        result["refused"] = "not documented" in final.lower()
        result["verdict"] = "pass" if code == 0 and result["answer_matches"] and (not expected or result["citation_matches"]) and mcp_succeeded else "review"
        if code != 0 and "authenticate" in (final + stderr).lower():
            result["verdict"] = "blocked: authentication"
    print(name, "exit", code, "MCP", mcp_used, "skill", skill_used, flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["smoke", "golden", "trigger", "review", "all"], default="all")
    parser.add_argument("--tools", nargs="+", choices=TOOLS, default=["codex"],
                        help="Clients to evaluate (default: codex; other clients are optional)")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=180, help="Per-agent wall timeout in seconds")
    parser.add_argument("--cases", nargs="+", help="Golden case IDs to retry without re-running successful cases")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    golden = json.loads((ROOT / "evals/golden.json").read_text())
    jobs = []
    if args.stage in ("all", "smoke"):
        # Save the exact requested listing, including untrusted-project visibility limitations.
        listing = subprocess.run(["codex", "mcp", "list"], cwd=ROOT, capture_output=True, text=True)
        (OUT / "codex-mcp-list.txt").write_text(listing.stdout + listing.stderr)
        jobs += [(tool, {"id": "smoke", "question": "Using the prd tools, what are the acceptance criteria for REQ-AUTH-001? Cite the source."}) for tool in args.tools]
    if args.stage in ("all", "golden"):
        jobs += [(tool, case) for case in golden if not args.cases or case["id"] in args.cases for tool in args.tools]
    if args.stage in ("all", "trigger"):
        business = ["What are the login acceptance criteria for REQ-AUTH-001?", "What is the password policy under REQ-AUTH-002?", "What session inactivity limit does REQ-AUTH-003 require?", "Which administrators need MFA under REQ-AUTH-004?", "What is the approved refund policy for REQ-BILLING-001?"]
        refactor = ["Explain a behavior-preserving rename of local variable x to count. Do not modify files.", "Explain removing an unused import from Python while preserving behavior. Do not modify files.", "Explain formatting whitespace in a Python function without changing behavior. Do not modify files.", "Explain inlining a temporary variable in a pure arithmetic function without changing behavior. Do not modify files.", "Explain replacing a manual sum loop with sum(numbers) while preserving behavior. Do not modify files."]
        for use, prompts in ((True, business), (False, refactor)):
            for i, question in enumerate(prompts):
                jobs += [(tool, {"id": f"trigger-{'business' if use else 'refactor'}-{i+1}", "question": question}) for tool in args.tools]
    if args.stage in ("all", "review"):
        reviews = {"codex": "Review server/ read-only for concrete retrieval, locking/concurrency and prompt-injection issues. Cite files/lines. Do not edit files.",
                   "cursor": "Review ONLY scripts/hooks.py, scripts/hook_io.py, scripts/sync_adapters.py and their generated hook JSON. Read-only: do not edit files, scan .venv, or invoke installed review workflows. Report at most five concrete bugs with file/line evidence and finish promptly. Current docs: Cursor sessionStart additional_context, beforeSubmitPrompt continue/user_message only, preToolUse permission allow/deny with agent_message on denial, afterFileEdit file_path; Codex apply_patch tool_input.command; Claude Stop systemMessage is advisory. Check wrong event/payload mappings and portability."}
        for tool, prompt in reviews.items():
            if tool not in args.tools:
                continue
            if tool == "cursor":
                prompt = ("Assess the following code as an independent checker. This is pure adapter code, not a business-rule question. "
                          "Use ONLY the supplied code and documented field contracts below; no tools, web research, installed skills or extra exploration. "
                          "Return your final answer with at most five concrete bugs now. "
                          "Contracts: Cursor sessionStart supports additional_context; beforeSubmitPrompt supports continue/user_message only; "
                          "preToolUse permission allow/deny and agent_message on deny only; afterFileEdit uses file_path; stop uses followup_message. "
                          "Codex apply_patch sends tool_input.command. Claude Stop accepts systemMessage as user advisory. "
                          "All hook errors must fail open; prompt pointers must be <300ms. Code:\n" +
                          '\n'.join(f"FILE {file}\n" + (ROOT / file).read_text() for file in ("scripts/hooks.py", "scripts/hook_io.py", "scripts/sync_adapters.py")))
            jobs.append((tool, {"id": "review", "question": prompt}))
    if args.cases:
        jobs = [job for job in jobs if job[1]["id"] in args.cases]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda job: run(*job, timeout=args.timeout), jobs))
    target = OUT / f"{args.stage}-results.json"
    previous = json.loads(target.read_text()) if target.exists() else []
    merged = {(r["tool"], r["id"]): r for r in previous}
    merged.update({(r["tool"], r["id"]): r for r in results})
    results = list(merged.values())
    target.write_text(json.dumps(results, indent=2) + "\n")
    report = ["# Cross-agent results", "", "Synthetic fixture corpus. Machine checks are conservative; review citations and superseded-trap semantics in saved responses.", "", "| Question | Claude | Cursor | Codex | Correct citation? | Refused when required? |", "| --- | --- | --- | --- | --- | --- |"]
    for case in golden:
        group = {r["tool"]: r for r in results if r["id"] == case["id"]}
        if not group:
            continue
        cells = [group[t].get("verdict", "review") if t in group else "not run" for t in TOOLS]
        cites = "; ".join(t + ": " + str(r.get("citation_matches")) for t,r in group.items())
        refuses = "; ".join(t + ": " + str(r.get("refused")) for t,r in group.items()) if case.get("refuse") else "n/a"
        report.append('| ' + case["question"].replace('|','/') + ' | ' + ' | '.join(cells + [cites, refuses]) + ' |')
    if args.stage in ("all", "golden"):
        (OUT / "comparison.md").write_text('\n'.join(report) + '\n')
    if args.stage in ("all", "trigger"):
        lines = ["# Skill trigger observations", "", "Observed tool/skill-file traces, not agent self-report. Missing traces need manual review.", "", "| Tool | Case | Skill observed | Expected | MCP observed | Exit |", "| --- | --- | --- | --- | --- | --- |"]
        for r in results:
            if r["id"].startswith("trigger-"):
                lines.append(f"| {r['tool']} | {r['id']} | {r['skill_observed']} | {'business' in r['id']} | {r['mcp_observed']} | {r['exit_code']} |")
        (OUT / "triggers.md").write_text('\n'.join(lines) + '\n')


if __name__ == "__main__":
    main()
