"""Live Codex workflow test in a marked disposable checkout, never a product repo.

Prerequisites: uv sync, sync_adapters.py, native workspace and /hooks trust.
Create .prd-workflow-test containing 'disposable fixture checkout', then run:
python3 scripts/check_prd_workflow.py --workspace /path/to/disposable/clone
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--reuse-draft", action="store_true", help="Resume a draft created by this synthetic test")
    args = parser.parse_args()
    root = args.workspace.resolve()
    marker = root / ".prd-workflow-test"
    if not marker.is_file() or marker.read_text().strip() != "disposable fixture checkout":
        parser.error("Workspace must be explicitly marked as a disposable fixture checkout")
    config = json.loads((root / "core/config.json").read_text())
    if config != {"PRD_DIR": "prds", "PRD_DB": ".cache/prd_index.db"}:
        parser.error("Only the default fixture corpus/index is supported")
    fixture = root / "prds/user-test.md"
    implementation = root / "demo"
    if implementation.exists() or (fixture.exists() and not args.reuse_draft):
        parser.error("Test output paths must be absent; --reuse-draft permits only the test draft")
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    original = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in tracked if name}
    out = root / "evals/cross_agent"
    out.mkdir(parents=True, exist_ok=True)
    env = os.environ | {"PRD_DIR": str(root / "prds"), "PRD_DB": str(root / ".cache/prd_index.db")}
    report = {"workspace": str(root), "commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "server_sha256": hashlib.sha256((root / "server/prd_context/index.py").read_bytes()).hexdigest(),
        "checks": {}}

    def agent(stage, prompt):
        result = subprocess.run(["codex", "exec", "--sandbox", "workspace-write", "--ephemeral",
            "--json", "--color", "never", "-o", str(out / f"workflow-{stage}.txt"), prompt],
            cwd=root, text=True, capture_output=True, timeout=240)
        (out / f"workflow-{stage}.jsonl").write_text(result.stdout)
        (out / f"workflow-{stage}.stderr").write_text(result.stderr)
        if result.returncode:
            raise RuntimeError(f"Codex {stage} failed ({result.returncode}); see saved stderr")
        events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
        calls = [e.get("item", {}) for e in events if e.get("type") == "item.completed"]
        if not any(i.get("type") == "mcp_tool_call" and i.get("tool") == "prd_answer_context"
                   and i.get("status") == "completed" and not i.get("error") for i in calls):
            raise RuntimeError(f"No successful native PRD lookup observed during {stage}")
        print(f"PASS: native Codex {stage}", flush=True)

    def documented():
        code = "import json; from prd_context.index import answer_context; print(json.dumps(answer_context('REQ-DEMO-001')))"
        result = subprocess.run([str(root / "server/.venv/bin/python"), "-c", code], cwd=root,
            env=env | {"PYTHONPATH": str(root / "server")}, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    try:
        if not args.reuse_draft:
            agent("author", "$prd-author Create only prds/user-test.md as a draft synthetic PRD. "
                "Owner Test Owner; ID REQ-DEMO-001. Pure shipping_fee(order_total) returns integer 0 "
                "for nonnegative integer totals >= 100, otherwise integer 10. Include Given/When/Then "
                "checks for 0, 99, 100, 101. Other input behavior, currency, tax and discounts are out "
                "of scope. Query existing approved evidence first. Do not approve or implement; no "
                "decision-critical questions for this bounded fixture. Edit no other file.")
        draft = fixture.read_text()
        if not draft.startswith("---\nstatus: draft\n") or "REQ-DEMO-001" not in draft:
            raise RuntimeError("Author did not preserve draft status and requirement ID")
        if documented()["documented"]:
            raise RuntimeError("Unapproved draft leaked into retrieval")
        report["checks"]["draft_excluded"] = True
        agent("approval", "$prd-author This is an explicit synthetic-owner approval for only "
            "prds/user-test.md. Test Owner approves REQ-DEMO-001 exactly as specified: nonnegative "
            "integer totals >=100 return integer 0, all other valid totals return integer 10. "
            "Read the draft and query existing context. Set its frontmatter and requirement status "
            "to approved, record this fixture-only approval in change history, and make current "
            "approval statements consistent. Keep the REQ ID and all four boundary criteria. "
            "Do not add business rules, implement code, or edit another file.")
        evidence = documented()
        if not evidence["documented"] or not any("user-test.md:" in e["citation"] for e in evidence["evidence"]):
            raise RuntimeError("Approved fixture not retrieved with a source citation")
        if not evidence["evidence"][0]["heading"].startswith("REQ-DEMO-001"):
            raise RuntimeError("Context cross-references crowded out the requirement's acceptance criteria")
        report["checks"]["approved_retrieved_with_citation"] = True
        report["checks"]["requirement_ranked_before_cross_references"] = True
        report["evidence"] = evidence
        agent("implement", "$prd-implement Implement approved REQ-DEMO-001 in only "
            "demo/shipping.py with pure shipping_fee(order_total), plus demo/test_shipping.py "
            "using standard-library unittest. Query the PRD tool first and cite it in your handoff. "
            "Cover totals 0, 99, 100, 101, checking exact integer return values. Run the tests. "
            "No extra invalid-input policy, dependencies, or PRD edits are authorized.")
        run = subprocess.run([str(root / "server/.venv/bin/python"), "-m", "unittest", "discover",
            "-s", "demo", "-v"], cwd=root, text=True, capture_output=True, check=True)
        (out / "workflow-implementation-tests.txt").write_text(run.stdout + run.stderr)
        check = "import sys;sys.path.insert(0,'demo');from shipping import shipping_fee;assert all(type(shipping_fee(n)) is int and shipping_fee(n)==(0 if n>=100 else 10) for n in range(301));print('301 independent boundary/range checks passed')"
        subprocess.run([str(root / "server/.venv/bin/python"), "-c", check], cwd=root, check=True)
        report["checks"]["implementation_tests"] = True
        report["checks"]["independent_301_inputs"] = True
    finally:
        fixture.unlink(missing_ok=True)
        if implementation.exists():
            # This directory was absent before the test and is owned by this fixture run.
            shutil.rmtree(implementation)
        subprocess.run([str(root / "server/.venv/bin/prd-mcp"), "reindex"], cwd=root, env=env,
            check=True, stdout=subprocess.DEVNULL)
        changed = [name for name, digest in original.items() if not (root / name).is_file()
                   or hashlib.sha256((root / name).read_bytes()).hexdigest() != digest]
        report["checks"]["original_tracked_files_unchanged"] = not changed
        report["unexpected_changes"] = changed
        (out / "workflow-results.json").write_text(json.dumps(report, indent=2) + "\n")
        if changed:
            raise RuntimeError(f"Agent changed existing tracked files: {changed}")
    print("PASS: draft → explicit fixture approval → retrieval → implementation → cleanup", flush=True)


if __name__ == "__main__":
    main()
