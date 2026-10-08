# PRD cross-agent Phase 0 discovery

Date: 2026-10-07. Initial discovery found no existing PRD-context repository. The user subsequently authorized creating this new repository and clarified its purpose: a repo-shipped PRD convention and business-context-to-implementation workflow.

## Repository discovery

No PRD Python MCP server, prd-context skills, or golden-question corpus was found in the current workspace. A filename search across Desktop also found no matching PRD project. Existing projects here are jarvis, toolbox and personal-reading-digest. Toolbox's instructions describe a separate Next.js marketplace, not this server; no files in those projects were changed.

## Skill discovery

Read and applied the local find-skills instructions and checked the skills.sh directory. Ran each requested command successfully; each returned “No skills found”:

```sh
npx --yes skills find 'cursor plugin'
npx --yes skills find 'cursor hooks'
npx --yes skills find 'codex skills'
npx --yes skills find 'agents.md'
npx --yes skills find 'cross-agent'
```

Shortlist: [openai/skills skill-creator](https://github.com/openai/skills/tree/main/skills/.system/skill-creator). Its agents/openai.yaml guidance adds Codex-specific value for skill metadata and tool dependencies. Read its upstream SKILL.md; did not install anything. No community candidate was found or recommended.

## Current docs read

- [Cursor skills](https://cursor.com/docs/skills): discovers .agents/skills and compatibility directories, including .claude/skills. Use a single project discovery copy in .agents/skills; do not add .claude/skills or .cursor/skills duplicates. Plugin packaging needs separate activation checks.
- [Cursor hooks](https://cursor.com/docs/hooks): sessionStart exists; use it rather than skipping session freshness. preToolUse is documented and can cover the pre-edit warning with matching tool names. beforeFileEdit is not listed. Retain beforeSubmitPrompt, afterFileEdit and stop wiring.
- [Cursor MCP](https://cursor.com/docs/context/mcp), [subagents](https://cursor.com/docs/agent/subagents), [plugin help](https://cursor.com/help/customization/plugins), and [plugin docs](https://cursor.com/docs/plugins) were opened. Subagent frontmatter supports readonly: true; use it alongside read-only instructions, without inventing a tools field.
- [Codex skills](https://developers.openai.com/codex/skills): agents/openai.yaml supports policy.allow_implicit_invocation and MCP dependencies.
- [Codex MCP](https://developers.openai.com/codex/mcp) and [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) were opened.
- [Codex hooks](https://learn.chatgpt.com/docs/hooks): SessionStart, UserPromptSubmit, PreToolUse, PostToolUse and Stop are supported. apply_patch can match apply_patch, Edit or Write. New or changed hooks are skipped until their exact definitions are reviewed and trusted through /hooks. Project .codex layers also require workspace trust. Do not report untrusted hooks as runtime-verified.
- [Codex plugins](https://learn.chatgpt.com/docs/plugins): current hook docs explicitly support .codex-plugin/plugin.json with a hooks entry and default hooks/hooks.json. Re-read the manifest schema before generating packaging.

## Local CLI inventory (installed, not yet tested against PRD)

| Tool | Installed version |
| --- | --- |
| Codex | codex-cli 0.160.1 |
| Cursor Agent | 2026.10.01-e373342 |
| Claude Code | 2.1.278 |

uv is installed. codex exec --help confirms --json, --ephemeral, --sandbox read-only, -C, and exec review. cursor-agent --help identifies the CLI as agent and confirms -p, --output-format stream-json, --mode ask, --workspace and --plugin-dir. No agent evaluation was launched because no target repo or MCP exists at the supplied location.

## Discovery resolution

Because no prior schemas/corpus were available, this repository defines a new v0.1 contract and explicitly synthetic authentication fixtures with ten golden questions. They are not the user's product requirements. Live verification and limitations are recorded separately under evals/cross_agent; the initial CLI inventory above alone does not imply runtime verification.
