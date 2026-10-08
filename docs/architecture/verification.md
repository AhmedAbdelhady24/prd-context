# Architecture diagram verification

Generated with the bundled Archify 3.0.1 skill on 2026-10-08. This is a conceptual overview of the local checkout, without commit-pinned repository evidence.

The renderer was run directly from the bundled project package. Native Codex skill listing selected an existing global Archify installation on this machine, so it does not prove clean-user project discovery. See [discovery evidence](codex-skill-discovery.json).

| Evidence | Result |
| --- | --- |
| Diagram type | architecture |
| Showcase artifact validation | 9/9; zero errors, zero warnings |
| Delivery and strict provenance check | passed |
| Automated native Chrome evidence | passed |
| Perceptual visual review | not requested |
| Specification SHA-256 | `69093d88ba889fe1cf0d0daee061da04cf32534f94a06a7cbe424a80cebb6b32` |
| HTML SHA-256 | `c09efd0d13e8b677fa058269b3ee14522be51c2554c1704f68096154303490e5` |

[Interactive HTML](prd-context.html), [specification](candidate.json), [finalizer receipt](prd-context.finalize-summary.json), [browser receipt](prd-context.browser-check.json).

To regenerate from the repo root:

```sh
node .agents/skills/archify/bin/archify.mjs finalize architecture docs/architecture/candidate.json docs/architecture/prd-context.html --quality showcase --json
```

For changed diagram content, use a fresh evidence directory with `--out-dir docs/architecture/review-2` so previous artifact-bound browser evidence is preserved.
