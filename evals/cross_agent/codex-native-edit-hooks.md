# Native Codex lifecycle verification — 2026-10-08

Codex 0.160.1 was started through its native app-server with the existing trusted project configuration and workspace-write sandbox. No hook definitions or trust records were changed.

The check explicitly invoked prd-author and authorized one apply_patch change on a disposable approved synthetic PRD. Native hook-completed notifications confirmed SessionStart, UserPromptSubmit, PreToolUse, PostToolUse and Stop completed from this project's `.codex/hooks.json`. PreToolUse delivered the approved-edit warning. The indexed digest matched the patched file, and session state recorded `prd_edited: true`. The agent made no MCP query after the patch and did not run reindex itself.

Cleanup removed the fixture, refreshed the shared index and verified all original PRD files were byte-for-byte unchanged. This proves the tested Codex lifecycle; it does not qualify Claude or Cursor's edit hooks.

See [structured evidence](codex-native-edit-hooks.json). Repeat after project/hook trust with:

```sh
server/.venv/bin/python scripts/check_codex_hooks.py
```
