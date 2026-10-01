# Installation / Codex Check

1. Unzip the package as one folder.
2. Keep the folder structure intact; do not copy only `SKILL.md`.
3. From the Skill folder run:

```bash
python tools/validate_package.py . --strict
```

Expected output (strict mode also verifies manifest hashes, JSON meta-schemas, package references and required Engine/Golden artifacts):

```text
PACKAGE VALIDATION: PASS
```

Required top-level directories include `core/`, `engine/`, `schemas/`, `adapters/`, `assets/`, and `tools/`.

Codex should read `SKILL.md`, then `AGENT_CONTRACT.md`, Core docs, JSON schemas, and exactly one active platform Adapter according to `ADAPTER_ROUTING.md`.
