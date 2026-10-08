# Repo PRD convention v0.1 (proposal)

This is a portable, version-controlled PRD convention intended for community adoption. It is not an established industry standard. The core template and skills turn business context into reviewable requirements and then into scoped implementation work.

Use one Markdown file per capability under PRD_DIR. UTF-8 files use explicit `status: draft`, `approved`, or `superseded` in a simple YAML frontmatter block. Only approved documents enter retrieval. Each requirement starts in a `## REQ-DOMAIN-NNN Name` section with a stable ID. Other `##` sections carry business context. Keep an approved document internally consistent: unresolved requirements stay in a separate draft, rather than mixing proposed rules into approved evidence. Do not reuse an ID for unrelated behavior.

Start with core/PRD_TEMPLATE.md. prd-author extracts facts and evidence, marks assumptions, exposes conflicts and asks only decision-critical questions. It writes a draft, never self-approves it. The human owner approves the business rules, then prd-reindex publishes the approved evidence. prd-implement queries those rules, prepares REQ-to-task/check traceability, and carries out explicitly authorized implementation. The MCP has no PRD-writing endpoint.

The parser deliberately supports plain unquoted status scalars, not arbitrary YAML. Missing, quoted, duplicated or unknown status values are excluded. Approved files without `##` sections provide no evidence. Retrieval is lexical evidence selection, not an automated requirements adjudicator: agents must assess whether evidence answers the question and abstain when it does not. Replace all synthetic fixture PRDs before using this for a real product.

One corpus uses one PRD_DB; mismatched PRD_DIR reuse is rejected. Concurrent readers/writers serialize with a POSIX flock plus SQLite transactions. The global lock is adequate for a small repo; split corpora or move to a service if indexing contention becomes material. PRD authors outside this process should save files atomically. Query-time live content hashes suppress stale evidence until reindex completes.
