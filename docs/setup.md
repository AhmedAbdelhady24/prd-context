# PRD Context

A repo-shipped PRD convention built and verified primarily with Codex, with optional Cursor Agent and Claude Code adapters using the same context server and skills. Turn business context into a reviewable PRD, approve the rules, and carry them into implementation with requirement traceability. This is **v0.1 of a proposed convention**, not an established industry standard. Claude access is not required for the current Codex scope.

The bundled `prds/` documents are **synthetic evaluation fixtures**, not requirements for your product. Replace them before real use. Read [the PRD convention](../docs/prd-standard.md) and start from [the template](../core/PRD_TEMPLATE.md).

Explore the [architecture diagram](../docs/architecture/prd-context.html) by downloading it and opening it in a browser. GitHub displays HTML source rather than running the viewer. Its [JSON source](../docs/architecture/candidate.json) summarizes the shared core, adapters, hooks, MCP server and index; it is an overview of this checkout, not a commit-pinned source audit.

## Architecture diagrams with Archify

The official [Archify skill](https://github.com/tt-a1i/archify), version 3.0.1, is included in `.agents/skills/archify` for Codex project discovery. A fresh clone includes its renderer, schemas and references; start or restart Codex in the checkout to discover `$archify`. Node.js 18+ is required for diagram generation. Archify is optional and is separate from the five canonical PRD skills and their MCP dependency.

To install Archify in another repository, run from that repository:

```sh
npx --yes skills add tt-a1i/archify --skill archify --agent codex --copy --yes
```

Then ask Codex: `$archify Explain this repository's architecture using the README and relevant source files. Keep assumptions explicit.` For a PRD workflow, ask: `$archify Diagram how business notes become a draft PRD, owner-approved requirements, and implementation with REQ traceability.` Diagramming does not approve or change business rules.

If Archify is already installed globally, Codex may select that copy. To use the bundled version explicitly, ask: `Read .agents/skills/archify/SKILL.md and use its packaged renderer to diagram this repo.` Native discovery on the author's machine selected its existing global copy; clean-user project discovery has not been independently tested.

The vendored skill retains its upstream [MIT license](../.agents/skills/archify/LICENSE). [skills-lock.json](../skills-lock.json) records its source and content hash. The installation command fetches the upstream version available when run; the checked-in package is the version used here. Update it explicitly with the command above and review upstream changes before committing them. `sync_adapters.py` manages the PRD adapters and leaves this third-party skill untouched.

The bundled diagram passed all nine showcase artifact checks with zero errors or warnings, strict provenance checks and automated browser checks. Perceptual visual review was not requested. See the [diagram receipt](../docs/architecture/verification.md).

## Start locally

Requires Python 3.11+, uv and a POSIX host (macOS/Linux). The SQLite index and PRD files stay local; agent CLI evaluations use each provider's authenticated service.

```sh
git clone https://github.com/AhmedAbdelhady24/prd-context.git
cd prd-context
uv sync --directory server --frozen
python3 scripts/sync_adapters.py
PRD_DIR="$PWD/prds" PRD_DB="$PWD/.cache/prd_index.db" server/.venv/bin/prd-mcp reindex
PRD_DIR="$PWD/prds" PRD_DB="$PWD/.cache/prd_index.db" server/.venv/bin/prd-mcp search 'REQ-AUTH-001'
server/.venv/bin/python tests/check.py
```

Change corpus/index paths once in `core/config.json`, then regenerate adapters. Relative paths resolve from this checkout. All generated client configs point to the same PRD_DIR and PRD_DB. Standalone server launches honor environment variables and default to `~/.cache/prd-context/prd_index.db`; CLAUDE_PLUGIN_DATA does not select a separate per-agent index.

Start Codex in this checkout with `codex`. Trust the workspace, then review and trust its five project hooks through `/hooks`. Run `codex mcp list` to confirm `prd` is enabled. Start real authoring with `$prd-author Turn these business notes into a draft PRD: ...`; replace the bundled synthetic corpus before querying real product rules. The owner approves decisions, then `$prd-reindex` indexes the approved evidence. Use `$prd-implement` with the approved REQ IDs for authorized implementation. These steps use Codex's project configuration without requiring another agent.

## Business context → PRD → implementation

1. Explicitly invoke **prd-author** with stakeholder notes, existing evidence and the desired outcome: “Turn these business notes into a draft PRD using the repo convention. Separate facts, assumptions, conflicts and open questions.” It creates a draft with stable REQ IDs, measurable outcomes, edge cases and testable acceptance criteria.
2. Have the owner resolve decisions and approve the document. Only explicit authoring work writes PRDs; the MCP exposes no PRD-writing tool. The author skill never self-approves requirements.
3. Invoke **prd-reindex** to publish approved evidence. Drafts, superseded files and unknown statuses are excluded.
4. Ask business questions with **prd-consult** or explicitly use **prd-ask**. Answers cite the source and lines or say “not documented.” Pure refactors should skip consultation.
5. Explicitly invoke **prd-implement** for authorized implementation: query requirements, map REQ IDs to tasks and acceptance checks, implement, and return evidence of validation. Requirements gaps remain explicit rather than becoming invented business behavior.

Explicit invocation differs by client (Codex `$prd-author`, Cursor `/prd-author`, Claude plugin skill `prd-context:prd-author`). The skill bodies and MCP contracts are shared.

## Adapters and installation

`core/skills/` is canonical. `scripts/sync_adapters.py` generates all client wiring and records managed files in `.adapter-files.json`. Edit core content or generator mappings, then sync; do not hand-edit generated skill copies. `--check` fails on drift and is part of CI. It normalizes the previous checkout's absolute prefix for portable CI comparisons; regeneration renders runnable paths for the current machine.

| Surface | Project/native configuration | Plugin packaging |
| --- | --- | --- |
| Claude Code | `CLAUDE.md` imports `AGENTS.md` | `prd-context/` contains `.claude-plugin/plugin.json`, skills, oracle, hooks and `.mcp.json` |
| Cursor | `.agents/skills`, `.cursor/mcp.json`, rule, oracle and hooks | Root `.cursor-plugin/plugin.json` references that same shared skill directory plus rules/agents/hooks/MCP |
| Codex | `.agents/skills`, `.codex/config.toml`, hooks and read-only custom oracle | Root `.codex-plugin/plugin.json` bundles the same skills, MCP and hooks |

For Claude locally, run `claude --plugin-dir "$PWD/prd-context"`. For Cursor and Codex in this checkout, use the project configuration. Trust the workspace in each client. **Codex requires reviewing and trusting new or changed hooks via `/hooks`**; untrusted project configuration/hooks may be skipped. `codex mcp list` alone can therefore omit an untrusted project server.

Use either project discovery or plugin installation for a consumer workspace. Do not additionally install this same checkout as a Cursor/Codex plugin while its project skills are active. No `.claude/skills`, `.cursor/skills` or `.codex/skills` copies are emitted: Cursor and Codex share exactly one project discovery path, `.agents/skills`. Claude's packaging directory is separate from those compatibility paths.

The plugin wiring is local checkout packaging, not a published marketplace package. Keep the whole checkout together, run sync after relocation, and regenerate paths for the install destination. When incorporating this into an existing product repo, preserve its instructions and configuration: the generator preserves other AGENTS sections and adds the CLAUDE import, but its managed client JSON/TOML files are owned outputs. Merge their PRD entries into existing client configs when integrating; do not overwrite unrelated setup. A nested sidecar alone will not configure a parent product workspace.

Current documentation: [Cursor skills](https://cursor.com/docs/skills), [hooks](https://cursor.com/docs/hooks), [MCP](https://cursor.com/docs/context/mcp), [subagents](https://cursor.com/docs/agent/subagents), [plugins](https://cursor.com/docs/reference/plugins); [Codex skills](https://developers.openai.com/codex/skills), [MCP](https://developers.openai.com/codex/mcp), [hooks](https://learn.chatgpt.com/docs/hooks), [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [plugin packaging](https://developers.openai.com/plugins/build/plugins); [Claude hooks](https://code.claude.com/docs/en/hooks) and [plugin manifest](https://code.claude.com/docs/en/plugins-reference). Checked 2026-10-07. Codex lifecycle-hook plugins have public-directory restrictions; project installation is the portable default.

## Hook behavior and limits

Every behavior is implemented once in `scripts/hooks.py`; `hook_io.py` handles payload differences. Hooks call the shared `prd-mcp` CLI, take bounded stdin JSON, and fail open. They are advisory, not an edit permission system. The read-only MCP guarantees no PRD writes; authoring permissions in a client still depend on that client's sandbox and the repo instructions.

| Behavior | Claude | Cursor | Codex |
| --- | --- | --- | --- |
| Session freshness/context | SessionStart | sessionStart | SessionStart |
| ≤3 prompt pointers | UserPromptSubmit | beforeSubmitPrompt diagnostic only | UserPromptSubmit |
| Reindex PRD edits | PostToolUse Write/Edit | afterFileEdit | PostToolUse apply_patch/Write/Edit |
| Approved edit warning | PreToolUse Write/Edit | preToolUse Write/Delete diagnostic only | PreToolUse apply_patch/Write/Edit |
| REQ trace reminder | Stop user advisory | stop follow-up once for business work | Stop user advisory |

Cursor currently has no `beforeFileEdit` event. Its generic preToolUse covers edits. Its documented beforeSubmitPrompt schema provides no model-context injection field, and preToolUse messages are documented for denials; this implementation emits diagnostic pointers/warnings to stderr while allowing the operation. Those two behaviors are **not equivalent context injection** in Cursor. Session context and the alwaysApply rule carry the query/citation instruction. The oracle uses Cursor's `readonly: true` and Codex's read-only sandbox; Claude restricts oracle tools to read/PRD lookup.

Prompt lookup uses the installed `server/.venv/bin/prd-mcp`, a short lock deadline and a subprocess timeout rather than starting uv or downloading dependencies on every prompt. Startup/edit hooks refresh the index; MCP queries refresh automatically. Missing dependencies or timeouts skip hooks without blocking work. Stop hooks do not enforce completion or prove REQ coverage.

## Verification

```sh
python3 scripts/sync_adapters.py --check
server/.venv/bin/python tests/check.py
server/.venv/bin/python scripts/cross_agent_eval.py --stage all
```

The first two commands check the shared server, actual MCP protocol/tool schemas, approval exclusion, live freshness, exact/multiple REQ retrieval, citations, 8-process indexing, malformed payloads, hook timing and adapter consistency. CI runs them without authenticated agent calls.

`server/.venv/bin/python tests/review_checks.py` adds regression coverage for connection cleanup, evaluation exit status and native fixture safety; CI runs it too. Agent evaluations exit nonzero for failed or unverified checks in the current invocation. Saved results from optional clients do not change a new Codex-only run's exit status. The native edit-hook fixture check requires the default synthetic corpus/index settings, so run it in a separate fixture checkout when using real product paths.

The evaluation runner defaults to Codex: native smoke tests, ten [golden questions](../evals/golden.json), a server review, and five business/five refactor prompts. Select optional clients explicitly with `--tools codex cursor` or `--tools claude` when available. It saves raw transcripts, final responses and machine-check summaries under `evals/cross_agent/`. The runner launches no edit-capable authoring evaluation; the separate native hook check uses a disposable fixture. Codex evals use explicit MCP overrides to test without altering user configuration; they do not establish trust in project hooks. Cursor permits only the PRD lookup through its generated tool-specific allowlist. Claude uses restricted built-in tools and MCP lookup permissions.

See [comparison](../evals/cross_agent/comparison.md), [trigger observations](../evals/cross_agent/triggers.md) and [verification status](../evals/cross_agent/status.md). A tool listing is discovery evidence, not proof of a successful call; an agent statement that it used a skill is not counted as a skill read. Authentication failures, permission denials and missing traces are retained as limitations.

| Native CLI baseline | Version | Coverage |
| --- | --- | --- |
| Codex | 0.160.1 | Live MCP/golden/trigger checks and independent server review |
| Cursor Agent | 2026.10.01-e373342 | Live MCP/golden/trigger checks; adapter review status is recorded separately |
| Claude Code (optional) | 2.1.278 | Discovery checked; authenticated runtime not qualified |
| Python MCP SDK | 1.30.0 | Locked in server/uv.lock and exercised via stdio |

Codex project trust and all five hook definitions have now been verified in a fresh process; [saved evidence](../evals/cross_agent/codex-hook-trust.md) includes a normal PRD MCP lookup without configuration or trust bypasses. A [native lifecycle check](../evals/cross_agent/codex-native-edit-hooks.md) also verified the approved-edit warning and automatic index refresh. Repeat it with `server/.venv/bin/python scripts/check_codex_hooks.py` after trusting the project hooks. Recheck event/payload contracts when upgrading a CLI. Current release scope is Codex; Claude runtime and Cursor's full native hook lifecycle are deferred optional qualifications. Validate real product PRDs separately from the bundled synthetic fixtures.
