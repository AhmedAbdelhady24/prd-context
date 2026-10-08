# Live Codex workflow test

Run this in a disposable clone, with an authenticated Codex CLI. It calls the provider and may consume your normal agent usage. The test creates one synthetic PRD and implementation, verifies them, then removes them. It never approves real product requirements.

After cloning and following the README's dependency/setup commands, open `codex` once to trust this checkout and review its five project hooks through `/hooks`. Exit Codex, then run from that disposable checkout:

```sh
printf 'disposable fixture checkout\n' > .prd-workflow-test
server/.venv/bin/python scripts/check_prd_workflow.py --workspace "$PWD"
server/.venv/bin/python scripts/check_codex_hooks.py
```

Run the two checks sequentially: each takes a snapshot of the corpus or tracked files and should not overlap another edit-capable test.

The workflow check explicitly invokes prd-author to draft REQ-DEMO-001, verifies draft exclusion, records an explicit synthetic-owner approval, retrieves the requirement and source citation, then invokes prd-implement. Its shipping-fee fixture returns integer 10 below a total of 100 and integer 0 at or above 100, for nonnegative integer totals. Agent-written acceptance tests run, followed by 301 independent inputs. Requirement headings must rank ahead of sections that merely cross-reference the ID. Cleanup verifies that the checkout's existing tracked files are unchanged.

The marker, default fixture configuration and absent output-path checks prevent accidental use in an unmarked product checkout. Do not run concurrent agents editing the checkout during these tests. A failed integrity check preserves unexpected tracked edits for investigation.

Outputs are saved under `evals/cross_agent/workflow-*`; raw `.jsonl` and `.stderr` files are ignored by Git. The separate hook check captures native completed-hook notifications and verifies the approved-edit warning and automatic index refresh. Automated golden questions remain available through `scripts/cross_agent_eval.py`.
