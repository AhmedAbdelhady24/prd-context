# Codex project hook trust resolved

Date: 2026-10-07. Codex CLI 0.160.1.

Trusted the PRD project folder through Codex's native folder-access prompt, reviewed the project hook source, and saved trust through the native `/hooks` browser. Five new project hooks became active. Existing user/plugin hooks were not changed.

A fresh app-server `hooks/list` query confirmed all five entries from this project's `.codex/hooks.json` are enabled with `trustStatus: trusted`, recording their current hashes in [codex-hook-trust.json](codex-hook-trust.json): PreToolUse, PostToolUse, SessionStart, UserPromptSubmit and Stop.

A fresh, read-only `codex exec` run loaded the project MCP normally and answered REQ-AUTH-001 with the correct `prds/auth.md:7-11` citation. It used no MCP configuration override and no hook-trust or sandbox bypass. [Final answer](codex-trusted-hooks.txt), raw stdout/stderr and [normal MCP listing](codex-mcp-list-trusted.txt) were saved. Its shared hook state ended with `business: true` and `reminded: true`, confirming the prompt and stop behaviors executed. No PRD files were edited, so native edit-trigger lifecycle checks remain separate.

The native run also reported expired authentication for an unrelated existing Context7 MCP. The PRD MCP call completed successfully; no Context7 configuration was changed.

Trust is local to this machine and the current hook definitions. Future changes to their definitions require a new review through `/hooks`.
