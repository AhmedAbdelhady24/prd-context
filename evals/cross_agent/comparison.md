# Cross-agent results

Synthetic fixture corpus. Machine checks are conservative; review citations and superseded-trap semantics in saved responses.

| Question | Claude | Cursor | Codex | Correct citation? | Refused when required? |
| --- | --- | --- | --- | --- | --- |
| What are the acceptance criteria for REQ-AUTH-001? Cite the source. | blocked: authentication | pass | pass | claude: False; cursor: True; codex: True | n/a |
| What is the minimum password length under REQ-AUTH-002? Cite the source. | blocked: authentication | pass | pass | claude: False; cursor: True; codex: True | n/a |
| When do password reset links expire in REQ-AUTH-002 and can they be reused? Cite the source. | blocked: authentication | pass | pass | claude: False; cursor: True; codex: True | n/a |
| What inactivity duration expires a session under REQ-AUTH-003? Cite the source. | blocked: authentication | pass | pass | claude: False; cursor: True; codex: True | n/a |
| What happens to the server-side session on logout under REQ-AUTH-003? Cite the source. | blocked: authentication | pass | pass | claude: False; cursor: True; codex: True | n/a |
| Which users must enable MFA under REQ-AUTH-004? Cite the source. | blocked: authentication | pass | pass | claude: False; cursor: True; codex: True | n/a |
| I heard REQ-AUTH-001 locks login after 3 attempts for 24 hours. Is that still current? Cite the current rule. | blocked: authentication | pass | pass | claude: False; cursor: True; codex: True | n/a |
| Is a 6-character password acceptable under current REQ-AUTH-002? Cite the current minimum. | blocked: authentication | pass | pass | claude: False; cursor: True; codex: True | n/a |
| What is the approved refund window under REQ-BILLING-001? Cite it or say not documented. | blocked: authentication | pass | pass | claude: None; cursor: None; codex: None | claude: False; cursor: True; codex: True |
| Which SSO provider is required by REQ-SSO-001? Cite it or say not documented. | blocked: authentication | pass | pass | claude: None; cursor: None; codex: None | claude: False; cursor: True; codex: True |
