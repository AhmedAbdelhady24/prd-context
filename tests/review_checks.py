"""Regression checks for review findings; no authenticated CLI calls."""
import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "server"), str(ROOT / "scripts")]
from prd_context.index import reindex
import cross_agent_eval as evaluation
import check_codex_hooks as native


def main():
    opened = []
    original_connect = sqlite3.connect

    class TrackedConnection(sqlite3.Connection):
        def close(self):
            self.closed = True
            super().close()

    def connect(*args, **kwargs):
        conn = original_connect(*args, **kwargs, factory=TrackedConnection)
        conn.closed = False
        opened.append(conn)
        return conn

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        corpus = root / "prds"
        corpus.mkdir()
        (corpus / "test.md").write_text('---\nstatus: approved\n---\n## REQ-TEST-001\nA rule.\n')
        with patch.dict(os.environ, PRD_DIR=str(corpus), PRD_DB=str(root / "index.db")), \
                patch("sqlite3.connect", connect):
            reindex()
            assert opened[-1].closed
            with patch.dict(os.environ, PRD_DIR=str(root / "other")):
                try:
                    reindex()
                except ValueError:
                    pass
                else:
                    raise AssertionError("Corpus mismatch was accepted")
            assert opened[-1].closed, "Exceptional database exit leaked a connection"

        base = {"tool": "codex", "id": "g01", "exit_code": 0, "response": "answer",
                "verdict": "pass", "mcp_succeeded": True, "mcp_observed": True,
                "skill_observed": True}
        out = root / "evals"
        out.mkdir()
        # Preserve a failed optional-client record; it must not fail a new Codex-only run.
        (out / "golden-results.json").write_text(json.dumps([{**base, "tool": "claude", "exit_code": 1}]))
        for verdict, expected in (("review", 1), ("pass", 0)):
            with patch.object(evaluation, "OUT", out), patch.object(evaluation, "run", return_value={**base, "verdict": verdict}), \
                    patch.object(sys, "argv", ["eval", "--stage", "golden", "--cases", "g01"]), \
                    contextlib.redirect_stderr(io.StringIO()):
                assert evaluation.main() == expected
        assert evaluation.failed({**base, "exit_code": 124})
        smoke = {k: v for k, v in base.items() if k != "verdict"} | {"id": "smoke", "mcp_succeeded": False}
        assert evaluation.failed(smoke)
        assert evaluation.failed(smoke | {"id": "trigger-business-1"})
        assert evaluation.failed(smoke | {"id": "trigger-refactor-1"})
        assert not evaluation.failed(smoke | {"id": "trigger-refactor-1", "mcp_observed": False, "skill_observed": False})
        with patch.object(evaluation, "OUT", out), patch.object(evaluation, "command", return_value=[str(root / "missing")]), \
                contextlib.redirect_stdout(io.StringIO()):
            result = evaluation.run("codex", {"id": "smoke", "question": "test"})
            assert result["exit_code"] == 127 and evaluation.failed(result)

        # Custom corpus check must stop before creating or editing any PRD.
        (root / "core").mkdir()
        (root / "core/config.json").write_text(json.dumps({"PRD_DIR": "real-product", "PRD_DB": "product.db"}))
        with patch.object(native, "ROOT", root):
            try:
                native.main()
            except RuntimeError as exc:
                assert "default synthetic" in str(exc)
            else:
                raise AssertionError("Native fixture check accepted custom product settings")
        assert not (root / "real-product").exists()
    print("PASS: database handles close, evaluation failures propagate, optional history is isolated, custom native fixtures are refused")


if __name__ == "__main__":
    main()
