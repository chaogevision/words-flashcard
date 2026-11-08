---
name: flashcard
description: "Create curriculum-faithful multiword scene flashcards in English, Japanese, French, German, Korean, and Spanish, with extensible language profiles."
metadata:
  version: "2.7.0"
  protocol: "agent-agnostic"
  contract_version: "1.2.0"
---

# Mission
Convert curriculum or user-supplied vocabulary into production-ready, visually consistent multiword scene flashcards while preserving exact source facts across primary, middle, and high school. The first multilingual profiles are Japanese, French, German, Korean, and Spanish; English remains backward compatible.

# Non-Negotiable Architecture
Separate:
- **Generative layer**: scene illustration, characters, environments, poses, props.
- **Deterministic layer**: exact target-language form, optional source-backed reading/pronunciation, gloss, label cards, connector graphics, IDs, manifests, status.

An image generator MUST NOT be the authoritative source for teaching text.

# Governing Documents
Read in this order:
1. `AGENT_CONTRACT.md`
2. `core/workflow.md`
3. `core/source_truth.md`
4. For a multilingual batch, exactly one matching `languages/<locale>/profile.json`
5. `core/grouping_rules.md`
6. `core/scene_brief_rules.md`
7. `core/visual_spec.md`
8. `core/connector_system_v3.md`
9. `core/design_tokens.json`
10. `core/qa_rules.md`
11. `engine/*.md`
12. `schemas/*.json`
13. `ADAPTER_ROUTING.md`

# Fixed Pipeline
`01 Parse -> 02 Validate -> 03 Group -> 03 Review Gate -> 04 Scene Brief -> 05 Layout -> 06 Prompt Compile -> 07 Base Illustration -> 08 Deterministic Compose -> 09 QA -> 10 Targeted Repair -> 11 Approved Export`

# Hard Rules
- Curriculum source is authoritative for target-language form, locale, supplied pronunciation/reading, gloss, unit and intended sense.
- Every non-English run must load exactly one matching `languages/<locale>/profile.json`; a `preview` profile can produce review samples but cannot be marked `APPROVED`.
- Every source term must be assigned or explicitly deferred with reason.
- Every visualized target must have a mapping mode.
- Not every word gets a connector.
- Base illustration must contain zero instructional typography and depict one connected scene. Never reserve a full-width label band or stripe; keep only small, irregular low-detail pockets for later label placement. Distribute targets naturally through the scene instead of placing them all in one row.
- Stage 08 must use authoritative vocabulary data, not OCR or generated text. Normalize to NFC only for rendering; preserve the original source value in data and provenance.
- Do not add topic titles, grade labels, top headers, banners, or decorative frames unless the user explicitly asks for them.
- Hard QA failure blocks `APPROVED`.
- Repair the smallest failing layer when possible.

# Active Visual System
- `Flashcard Visual Spec V2`
- `connector.v3.light`
- white/light-warm rounded label cards
- deep navy target-language form
- optional subordinate pronunciation/reading and gloss
- pale gray-blue connectors only when instructionally useful
- grade-appropriate illustration style comes from `core/visual_spec.md`; card structure stays the same across grades
- no extra topic/grade title or title chrome by default

## Grade-Appropriate Scene Style
Read `core/visual_spec.md` when the card grade is primary, middle, or high school. The Primary multiword scene-card format remains authoritative; grade cues change only the scene illustration. The bundled reference images are style references for illustration only, not card layout or text.

Before any Stage 07 generation, every Agent must select the matching `<band>_art.png` and attach that actual image file to the image-generation request. The illustration style is selected by learner audience, not target language. Style prose alone does not satisfy this requirement. If the Agent or image model cannot accept an image reference, stop before generation and report `STYLE_REFERENCE_UNAVAILABLE`; do not approve a prose-only substitute. Record the selected path, SHA-256, and actual attachment status for every generated card. Base-art prompts must prohibit instructional text in every script, including target forms, readings, translations, signs and labels.

# Completion
A batch is complete only when:
1. source coverage is complete;
2. all approved cards pass hard QA using a `validated` language profile;
3. every final card has provenance and manifest;
4. final filenames/IDs are unique;
5. outputs are checked against `assets/golden_set/` when a Golden reference is provided for the product line.

Preview cards generated with a `preview` language profile must be labelled `PREVIEW`, not `APPROVED`.


# Platform Adapters
- OpenAI: `adapters/openai/ADAPTER.md`
- Doubao Work: `adapters/doubao_work/ADAPTER.md`
- Qwen Office: `adapters/qwen_office/ADAPTER.md`
- WorkBuddy: `adapters/workbuddy/ADAPTER.md`

Platform adapters may tighten execution thresholds (for example label size and connector-length limits) but may not weaken Core hard gates.

# Reference Tools
- `tools/compose_cards.py` — target-first deterministic Stage 08 composer with a connector length ceiling.
- `tools/compose_multilingual_cards.py` — locale-profiled renderer with NFC normalization, script font checks and style-reference evidence.
- `tools/qa_check.py` — Stage 09 gate: data, mapping, geometry and asset checks.
- `tools/qa_multilingual_cards.py` — multilingual text/source coverage, target mapping, label collision and reference-attachment gate.
- `tools/validate_package.py` — package integrity check.


# Adapter Selection Rule
At run start, identify the actual execution platform and load exactly one active platform adapter in addition to Core.

Rule precedence:
`Agent Contract -> Core -> Active Platform Adapter -> Current Task`.

Do not indiscriminately merge corrective rules from other platforms. See `ADAPTER_ROUTING.md`.


# Package Integrity
Before execution, an Agent SHOULD run `python tools/validate_package.py . --strict`.
A failed package check blocks production because Core/Schema omissions can invalidate stage contracts.
