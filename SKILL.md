---
name: primary-school-english-scene-flashcards
version: 2.2.2
protocol: agent-agnostic
contract_version: 1.0.0
description: "Agent-independent production protocol for curriculum-faithful primary-school English scene flashcards."
---

# Mission
Convert a curriculum vocabulary source into a production-ready, visually consistent flashcard set while preserving exact curriculum facts.

# Non-Negotiable Architecture
Separate:
- **Generative layer**: scene illustration, characters, environments, poses, props.
- **Deterministic layer**: English, IPA, Chinese gloss, label cards, connector graphics, IDs, manifests, status.

An image generator MUST NOT be the authoritative source for teaching text.

# Governing Documents
Read in this order:
1. `AGENT_CONTRACT.md`
2. `core/workflow.md`
3. `core/source_truth.md`
4. `core/grouping_rules.md`
5. `core/scene_brief_rules.md`
6. `core/visual_spec.md`
7. `core/connector_system_v3.md`
8. `core/design_tokens.json`
9. `core/qa_rules.md`
10. `engine/*.md`
11. `schemas/*.json`
12. `ADAPTER_ROUTING.md`

# Fixed Pipeline
`01 Parse -> 02 Validate -> 03 Group -> 03 Review Gate -> 04 Scene Brief -> 05 Layout -> 06 Prompt Compile -> 07 Base Illustration -> 08 Deterministic Compose -> 09 QA -> 10 Targeted Repair -> 11 Approved Export`

# Hard Rules
- Curriculum source is authoritative for spelling, IPA, gloss, unit and intended sense.
- Every source term must be assigned or explicitly deferred with reason.
- Every visualized target must have a mapping mode.
- Not every word gets a connector.
- Base illustration must contain zero instructional typography.
- Stage 08 must use authoritative vocabulary data, not OCR or generated text.
- Hard QA failure blocks `APPROVED`.
- Repair the smallest failing layer when possible.

# Active Visual System
- `Flashcard Visual Spec V2`
- `connector.v3.light`
- white/light-warm rounded label cards
- deep navy English word
- subordinate IPA and Chinese
- pale gray-blue connectors only when instructionally useful

# Completion
A batch is complete only when:
1. source coverage is complete;
2. all approved cards pass hard QA;
3. every final card has provenance and manifest;
4. final filenames/IDs are unique;
5. outputs are checked against `assets/golden_set/` when a Golden reference is provided for the product line.


# Platform Adapters
- OpenAI: `adapters/openai/ADAPTER.md`
- Doubao Work: `adapters/doubao_work/ADAPTER.md`
- Qwen Office: `adapters/qwen_office/ADAPTER.md`

Platform adapters may tighten execution thresholds (for example label size and connector-length limits) but may not weaken Core hard gates.


# Adapter Selection Rule
At run start, identify the actual execution platform and load exactly one active platform adapter in addition to Core.

Rule precedence:
`Agent Contract -> Core -> Active Platform Adapter -> Current Task`.

Do not indiscriminately merge corrective rules from other platforms. See `ADAPTER_ROUTING.md`.


# Package Integrity
Before execution, an Agent SHOULD run `python tools/validate_package.py . --strict`.
A failed package check blocks production because Core/Schema omissions can invalidate stage contracts.
