# Changelog

## 2.2.2 — Completeness and contract-consistency hotfix
- Added the missing `engine/` interface layer promised by README architecture.
- Added `core/design_tokens.json`, required by deterministic Stage 08 composition.
- Added Stage 07 base-asset and Stage 10 repair-action schemas.
- Added array wrapper schemas for VocabularyMaster and CardPlanSet.
- Added an actual Golden Set reference and usage rules.
- Tightened manifest/run-state provenance requirements with platform identity.
- Required `mapping_mode` in LayoutSpec labels.
- Replaced the package validator with strict hash, meta-schema, reference, Engine and Golden Set checks.
- Corrected adapter version headings.


## 2.2.0
- Added Qwen Office / 千问办公 Adapter.
- Added Qwen observed-failure audit.
- Added adapter routing specification.
- Added Qwen card-type router and teaching-mechanism grouping gate.
- Added Qwen connector length, endpoint, context-proximity, cutaway, object-differentiation and density QA rules.
- Added adapter selection to Agent Contract and conformance checklist.
- Retained Doubao Work Adapter and Connector V3 unchanged.

## 2.1.0
- Added Doubao Work Adapter based on observed production failures.
- Tightened Doubao label scale, connector geometry, text contamination and style drift QA.
## 2.2.1 — Packaging hotfix
- Restored mandatory `core/` documents referenced by `SKILL.md`.
- Restored mandatory `schemas/` JSON Schemas referenced by `AGENT_CONTRACT.md`.
- Added `PACKAGE_MANIFEST.json`.
- Added `tools/validate_package.py` to fail fast on missing required files or invalid JSON schemas.
- Restored all supported platform adapters in the distributable folder.
- Root cause: V2.2 packaging assembled only root docs/adapters and omitted Core/Schema directories while the contract still referenced them.

