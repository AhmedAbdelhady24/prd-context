# New-user test — 2026-10-08

Cloned `AhmedAbdelhady24/prd-context` from GitHub at `7032228` into a disposable checkout. Installed frozen dependencies and regenerated adapters, then used Codex's native workspace and hook-trust onboarding. Normal `codex mcp list` showed the project `prd` server enabled.

| Test | Result |
| --- | --- |
| Fresh-clone local and review suites | passed |
| Native Codex draft authoring | draft created; existing evidence queried |
| Draft retrieval | excluded |
| Explicit synthetic-owner approval | recorded through prd-author; no production authority |
| Approved retrieval | cited evidence returned |
| Requirement heading priority | passed after correcting the issue below |
| Native prd-implement | created only fixture code/tests; queried PRD and cited source |
| Acceptance tests | all four specified boundaries passed |
| Independent implementation check | 301 valid inputs passed, including exact integer return type |
| Lookup/trap/abstention cases | g01, g07, g09, g10 all passed |
| Native hook lifecycle | all five hooks completed; warning and index refresh verified |
| Cleanup | fixture PRD and implementation removed; existing tracked files unchanged |

The initial generated PRD mentioned its REQ ID in several context sections before the requirement. Retrieval's default limit could return those references and omit the acceptance criteria. The server now ranks exact requirement headings first. A regression reproduces the case with four preceding reference sections. The complete author/approval/retrieval/implementation workflow was rerun successfully with the fix applied to the clone. [workflow-results.json](workflow-results.json) records the tested server hash; its base checkout commit predates this correction.

Evidence: [workflow](workflow-results.json), [implementation checks](workflow-implementation-tests.txt), [lookup cases](lookup-results.json), [native hooks](new-user-native-hooks.json). The live check is reproducible with [check_prd_workflow.py](../../scripts/check_prd_workflow.py); see [instructions](../../docs/testing.md). Mutating fixture checks should run sequentially.

Public evidence is sanitized: local paths, runtime/session identifiers, timestamps and raw lookup responses are omitted. Detailed raw traces stay in the disposable local checkout; `DISPOSABLE_CHECKOUT` in a handoff names the removed fixture location.

This is a fresh checkout on the author's authenticated machine, not a clean new account. No real product corpus, Claude runtime, full Cursor hook lifecycle, or marketplace installation is claimed. The ranking correction does not change tool schemas or trusted hook definitions.
