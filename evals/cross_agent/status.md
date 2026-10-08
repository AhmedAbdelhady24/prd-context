# Verification status — 2026-10-08

The repository was created from scratch with explicit user authorization. Its PRDs and ten golden questions are synthetic fixtures; real business context has not yet been supplied or validated.

Current delivery scope is Codex, per the owner's instruction on 2026-10-08. Claude access is unavailable and its runtime qualification is deferred; it is not a blocker for the Codex scope. Optional adapters continue to use the shared core. The evaluation runner defaults to Codex and requires explicit selection of other clients.

| Check | Claude Code 2.1.278 | Cursor Agent 2026.10.01-e373342 | Codex 0.160.1 |
| --- | --- | --- | --- |
| MCP/skill discovery | Init listed both PRD tools, connected MCP and all five plugin skills | MCP discovered and skill-file reads observed | MCP tools and skill-file reads observed |
| Native MCP smoke | Blocked: expired OAuth | Successful PRD lookup and citation | Successful PRD lookup and citation |
| Ten golden questions | All ten attempted; authentication failed | 10/10 pass | 10/10 pass |
| Two superseded traps | Not verified | Both rejected obsolete rules | Both rejected obsolete rules |
| Two not-documented cases | Not verified | Both abstained | Both abstained |
| Business-rule trigger prompts | Five attempted; authentication failed | 5/5 observed skill reads + MCP calls | 5/5 observed skill reads + MCP calls |
| Pure-refactor trigger prompts | Five attempted; authentication failed | 5/5 no skill read and no PRD call | 5/5 no skill read and no PRD call |
| Independent code review | Not requested | Completed; three fixes accepted and two platform/output proposals rejected or documented | Completed; all five findings accepted and fixed |
| Native lifecycle hooks | Authentication blocked | Not comprehensively triggered end-to-end | All five trusted project hooks completed natively; approved-edit warning delivered and patch automatically indexed |

See [comparison](comparison.md), [triggers](triggers.md), [review disposition](review-disposition.md), [Codex review](codex-review.txt), [Cursor review](cursor-review.txt), and [local check output](local-checks.txt). Raw stdout/stderr files remain in this directory; they are ignored by Git because native agent transcripts can contain environment-specific metadata. Final responses and summary JSON are retained.

Codex `mcp list` was saved, but its normal invocation did not list the PRD server in the untrusted project layer. The successful headless runs explicitly supplied the same MCP configuration through `-c` overrides. This proves server/skill interoperability, not project-layer trust or hook activation. Cursor initially denied MCP calls in ask mode; the documented per-tool project allowlist resolved lookup access without a broad permission bypass. Claude failed before model inference; no successful Claude behavior is claimed.

Local executable checks passed with Python 3.12.13 and MCP SDK 1.30.0: actual stdio initialization/tool schemas/calls, approval and superseded exclusion, missing/draft refusal, exact and multi-REQ retrieval, stale-hit replacement, corpus ownership, incremental/idempotent updates, deletion/symlink behavior, eight concurrent indexers, concurrent session-state reminders, patch/move payload normalization, startup/malformed-input fail-open, approved-edit warnings, edit reindexing, reminder loop guard, optimized generator validation, preservation of other AGENTS sections, adapter drift and relocation with spaces. Sample prompt hook measurements were approximately 50 ms (all below 300 ms); this is a small-corpus measurement, not a latency guarantee on arbitrary corpora or slow hosts.

The saved reviews describe pre-fix code. Fixes have local regression checks; reviewers were not asked to approve the final revision. Cursor review used the supplied code plus explicit documented field contracts after research-oriented attempts timed out. No native downstream execution of PRD prompt-injection text was demonstrated or claimed.

Codex trust was subsequently resolved through the native `/hooks` interface. A fresh API query verified the saved hashes of all five project hooks as enabled/trusted, and a normal read-only run used the project MCP without overrides. See [hook trust evidence](codex-hook-trust.md).

On 2026-10-08, the [native Codex lifecycle check](codex-native-edit-hooks.md) completed all five project hooks, delivered the approved-edit warning and verified that PostToolUse indexed the patch without a subsequent MCP query. The disposable fixture was removed and the existing PRD corpus stayed byte-for-byte unchanged. Native `claude auth status` still reports `loggedIn: false`.

Deferred optional qualification: when Claude becomes available, authenticate and rerun smoke/golden/trigger stages with `--tools claude`. Cursor's native edit-hook lifecycle and installed plugin packaging also remain separate qualifications. Future new/changed Codex hook definitions still require review via `/hooks`. Optional Claude commands:

```sh
server/.venv/bin/python scripts/cross_agent_eval.py --stage smoke --tools claude
server/.venv/bin/python scripts/cross_agent_eval.py --stage golden --tools claude
server/.venv/bin/python scripts/cross_agent_eval.py --stage trigger --tools claude
```

Project configuration is the verified default for Cursor/Codex. Packaging manifests were generated from current docs, but marketplace installation, distribution to another user's machine and full three-client plugin activation were not tested. No remote repo was created or published.
