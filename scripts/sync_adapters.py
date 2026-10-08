"""Generate thin adapters from core. --check compares without writing.

Absolute machine paths are rendered at sync time, normalized for CI drift checks.
"""
import argparse
import json
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def js(value):
    return json.dumps(value, indent=2) + "\n"


def portable(content, prefix):
    def normalize(value, key=""):
        if isinstance(value, dict):
            return {k: normalize(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [normalize(v) for v in value]
        if isinstance(value, str):
            if key == "command":
                return [part.replace(prefix, "<REPO_ROOT>") for part in shlex.split(value)]
            return value.replace(prefix, "<REPO_ROOT>")
        return value
    try:
        return normalize(json.loads(content))
    except ValueError:
        return content.replace(prefix, "<REPO_ROOT>")


def shared_instructions(context):
    target = ROOT / "AGENTS.md"
    existing = target.read_text() if target.exists() else ""
    lines = existing.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.strip() == "## PRD Context"), None)
    if start is None:
        return existing.rstrip() + ("\n\n" if existing.strip() else "") + context
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return ''.join(lines[:start]) + context + ("\n" if end < len(lines) else "") + ''.join(lines[end:])


def generated():
    out = {}
    config = json.loads((ROOT / "core/config.json").read_text())
    env = {key: str((ROOT / Path(config[key]).expanduser()).resolve()) for key in ("PRD_DIR", "PRD_DB")}
    mcp = {"command": "uv", "args": ["run", "--directory", str(ROOT / "server"), "prd-mcp"], "env": env}
    context = (ROOT / "core/PRD_CONTEXT.md").read_text()
    oracle = (ROOT / "core/agents/prd-oracle.md").read_text()
    rule = "---\ndescription: Query documented business rules\nalwaysApply: true\n---\n" + context
    if len(rule.splitlines()) > 15 or len(context.splitlines()) != 10:
        raise ValueError("PRD Context must have 10 lines; Cursor rule must have at most 15")
    out["AGENTS.md"] = shared_instructions(context)
    claude = (ROOT / "CLAUDE.md").read_text() if (ROOT / "CLAUDE.md").exists() else ""
    out["CLAUDE.md"] = claude if "@AGENTS.md" in claude.splitlines() else claude.rstrip() + ("\n\n" if claude.strip() else "") + "@AGENTS.md\n"
    out[".cursor/rules/prd-context.mdc"] = rule
    out["rules/prd-context.mdc"] = rule
    agent_header = "---\nname: prd-oracle\ndescription: Read-only PRD evidence and acceptance criteria oracle\n"
    out[".cursor/agents/prd-oracle.md"] = agent_header + "readonly: true\n---\n" + oracle
    out["agents/prd-oracle.md"] = out[".cursor/agents/prd-oracle.md"]
    out["prd-context/agents/prd-oracle.md"] = agent_header + "tools: Read, mcp__prd__prd_answer_context, mcp__plugin_prd-context_prd__prd_answer_context\n---\n" + oracle
    out[".codex/agents/prd-oracle.toml"] = ('name = "prd-oracle"\ndescription = "Read-only PRD evidence oracle"\n'
                                               'sandbox_mode = "read-only"\ndeveloper_instructions = ' + json.dumps(oracle) + "\n")
    for skill in sorted((ROOT / "core/skills").glob("*/SKILL.md")):
        name = skill.parent.name
        body = skill.read_text()
        out[f".agents/skills/{name}/SKILL.md"] = body
        out[f"prd-context/skills/{name}/SKILL.md"] = body
        implicit = "true" if name == "prd-consult" else "false"
        yaml = ('policy:\n  allow_implicit_invocation: ' + implicit + '\ndependencies:\n  tools:\n'
                '    - type: "mcp"\n      value: "prd"\n      description: "Read-only approved PRD evidence"\n')
        out[f".agents/skills/{name}/agents/openai.yaml"] = yaml
    out[".cursor/mcp.json"] = js({"mcpServers": {"prd": mcp}})
    out[".cursor/cli.json"] = js({"permissions": {"allow": ["Mcp(prd:prd_answer_context)"], "deny": []}})
    out["mcp.json"] = out[".cursor/mcp.json"]
    out["prd-context/.mcp.json"] = out[".cursor/mcp.json"]
    out[".codex/config.toml"] = ('# Generated: re-run scripts/sync_adapters.py after relocating.\n'
        '[mcp_servers.prd]\ncommand = "uv"\nargs = ' + json.dumps(mcp["args"]) + '\n'
        '[mcp_servers.prd.env]\n' + ''.join(k + ' = ' + json.dumps(v) + '\n' for k, v in env.items()))
    for tool, prefix in (("claude", "prd-context/hooks/hooks.json"), ("cursor", ".cursor/hooks.json"), ("codex", ".codex/hooks.json")):
        mapping = {"session": "SessionStart", "prompt": "UserPromptSubmit", "edit": "PostToolUse",
                   "warning": "PreToolUse", "stop": "Stop"}
        if tool == "cursor":
            mapping = dict(session="sessionStart", prompt="beforeSubmitPrompt", edit="afterFileEdit", warning="preToolUse", stop="stop")
        hooks = {}
        for behavior, event in mapping.items():
            cmd = ' '.join(k + '=' + shlex.quote(v) for k, v in env.items()) + ' python3 ' + shlex.quote(str(ROOT / "scripts/hooks.py")) + f" {tool} {behavior}"
            if tool == "cursor":
                handler = {"command": cmd}
                if behavior == "warning":
                    handler["matcher"] = "Write|Delete"
                hooks[event] = [handler]
            else:
                handler = {"type": "command", "command": cmd, "timeout": 10}
                entry = {"hooks": [handler]}
                if behavior in ("edit", "warning"):
                    entry["matcher"] = "Write|Edit" if tool == "claude" else "apply_patch|Write|Edit"
                hooks[event] = [entry]
        config = {"hooks": hooks}
        if tool == "cursor":
            config["version"] = 1
        out[prefix] = js(config)
    out["hooks/hooks.json"] = out[".cursor/hooks.json"]
    out["hooks/codex.json"] = out[".codex/hooks.json"]
    out["prd-context/.claude-plugin/plugin.json"] = js({"name": "prd-context", "version": "0.1.0", "description": "Repo-shipped PRD context and authoring workflows"})
    out[".cursor-plugin/plugin.json"] = js({"name": "prd-context", "version": "0.1.0", "description": "Repo-shipped PRD context", "skills": "./.agents/skills", "rules": "./rules", "agents": "./agents", "hooks": "./hooks/hooks.json", "mcpServers": "./mcp.json"})
    out[".codex-plugin/plugin.json"] = js({"name": "prd-context", "version": "0.1.0", "description": "Repo-shipped PRD context", "skills": "./.agents/skills", "mcpServers": "./mcp.json", "hooks": "./hooks/codex.json"})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = generated()
    manifest = ROOT / ".adapter-files.json"
    old = json.loads(manifest.read_text()) if manifest.exists() else []
    drift = []
    for rel, content in expected.items():
        target = ROOT / rel
        actual = target.read_text() if target.is_file() else None
        if args.check and actual != content:
            # Checked-in paths may originate from another checkout. Their suffixes still must match.
            previous_root = None
            cfg = ROOT / ".cursor/mcp.json"
            try:
                previous_root = str(Path(json.loads(cfg.read_text())["mcpServers"]["prd"]["args"][2]).parent)
            except (OSError, ValueError, KeyError, IndexError):
                pass
            if actual is None or not previous_root or portable(actual, previous_root) != portable(content, str(ROOT)):
                drift.append(rel)
        elif not args.check and actual != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    for rel in set(old) - expected.keys():
        drift.append(rel + " (obsolete)")
    if args.check:
        if sorted(old) != sorted(expected):
            drift.append(".adapter-files.json")
        if drift:
            print("Adapter drift: " + ", ".join(drift), file=sys.stderr)
            return 1
        print(f"Adapters match core ({len(expected)} files)")
    else:
        if set(old) - expected.keys():
            raise RuntimeError("Obsolete generated files require explicit cleanup: " + ', '.join(set(old) - expected.keys()))
        manifest.write_text(js(sorted(expected)))
        print(f"Generated {len(expected)} adapter files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
