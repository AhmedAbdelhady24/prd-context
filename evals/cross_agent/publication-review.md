# Publication review — 2026-10-08

Reviewed the complete first publication (`1613486`) and the follow-up corrections against the requested Codex-first scope. The GitHub main commit matched the local publication; the starting worktree was clean. PRDs remain synthetic fixtures, and approved business decisions were not changed.

## Findings corrected

| Finding | Correction | Regression evidence |
| --- | --- | --- |
| SQLite transaction context did not explicitly close connections | Close every connection after commit/rollback, including exceptional exits | Tracked connections close after success and corpus mismatch |
| Evaluation script returned success despite failed agent checks | Return nonzero for failed/unverified current checks; report missing CLIs; reject empty case selection | Failure, success, missing binary, smoke and trigger cases; historical optional-client failures do not fail a new Codex-only run |
| Native fixture check ignored custom PRD paths | Refuse custom corpus/index settings before writing a fixture | No product directory or fixture created on refusal |
| README promoted the diagramming skill and was too long | Embed exported overall-system SVG, shorten README to 43 lines, retain details in docs/setup.md | Local links resolve; SVG parses; no Archify promotion in README |

## Verification

- Fresh clone: locked `uv sync`, drift check, adapter regeneration and full local checks passed. Review fixes were then applied to this disposable clone and both suites passed again.
- Actual MCP stdio initialization, tools/schemas, retrieval exclusion and freshness, citations, incremental updates, eight-process lock contention, hook fail-open/latency, state concurrency, relocation and adapter consistency passed.
- New resource-lifecycle/evaluation/fixture regression suite passed and is included in CI.
- Live Codex smoke after the fixes: exit 0, successful PRD lookup and observed consultation skill read.
- Owned Python, JSON and TOML parse; core/Cursor line limits pass; Git whitespace check passes.
- Diagram SVG exported through the bundled viewer's canonical export, preserving the validated HTML. Earlier artifact/provenance/native Chrome gates passed; no new perceptual review is claimed.
- The five trusted Codex hook definitions were not changed by this review. The bundled third-party skill was not edited.

Claude runtime is deferred. Cursor's full native edit-hook lifecycle, plugin marketplace installation, clean-user Archify discovery, real business-corpus acceptance, and executing hostile PRD instructions through a model are not qualified by these checks. No claim of complete three-agent runtime coverage is made.

GitHub Actions was enabled and the workflow registered, but the initial publication had no run. The workflow now also allows manual dispatch; follow-up CI status must be checked separately.
