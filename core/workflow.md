# Core Workflow — Stage 01–11

This document defines the platform-independent production lifecycle.

## Stage 01 — Parse Vocabulary
Input: curriculum vocabulary source.
Output: `VocabularyMaster[]`.
Rules:
- preserve spelling, IPA, Chinese gloss, unit, page and intended sense;
- use a stable curriculum identity key, preferably `grade + book + unit + term`;
- never infer a corrected curriculum fact silently.

## Stage 02 — Validate Vocabulary
Check duplicates, OCR ambiguity, missing IPA/gloss, phrase boundaries, proper nouns and repeated terms with different senses.
Output validation flags. Do not rewrite the source silently.

## Stage 03 — Group Into Cards
Create `CardPlan[]` using semantic coherence and visual co-occurrence, not arbitrary fixed word counts.
Preferred card size: 3–5 terms, but 1–6 is allowed when pedagogically justified.

## Stage 03 Review Gate
Every source term must be assigned exactly once by curriculum identity key, or explicitly deferred with a reason.
Weak groups must be `SPLIT`, `RETEMPLATE`, or `DEFER` before Stage 04.

## Stage 04 — Scene Brief
Create one `target_spec` per term with an explicit mapping mode and connector policy.

## Stage 05 — Layout Spec
Define canvas, safe area, label zones, reading order, anchor targets and connector routing policy.
Layout must anticipate labels; it must not treat labels as a late overlay after the scene is fixed.

## Stage 06 — Prompt Compile
Compile scene + layout + visual rules into a base-illustration prompt.
Hard requirement: prompt explicitly forbids instructional English, IPA, Chinese, label cards and connector graphics.

## Stage 07 — Base Illustration
Generate exactly one base illustration per card.
Hard requirement: zero instructional typography and zero teaching connectors.
If the platform bakes labels or readable teaching text into the illustration, Stage 07 fails.

## Stage 08 — Deterministic Compose
Render authoritative English, IPA, Chinese gloss, label cards and connector graphics deterministically.
Generated pixels/OCR are never the authority for teaching text.

## Stage 09 — QA
Run data, semantic, mapping, layout, connector, style and provenance QA.
Any hard failure blocks approval.
Platform Adapter QA rules are additive and may tighten thresholds.

## Stage 10 — Targeted Repair
Repair the smallest failing layer:
- text-only recompose;
- connector reroute;
- label relocation;
- base illustration edit/regenerate;
- regroup/retemplate only when the design itself is invalid.

## Stage 11 — Approved Export
Export final PNG + manifest + scene brief + layout spec + QA report.
Only all-pass cards may become `APPROVED`.

## State Machine
`DRAFT -> PLANNED -> BRIEF_READY -> LAYOUT_READY -> PROMPT_READY -> GENERATED -> COMPOSED -> QA_FAILED -> REVISED -> APPROVED -> SUPERSEDED`

A card may move directly from `COMPOSED` to `APPROVED` only after Stage 09 passes; `QA_FAILED` is used when a repair cycle is required.
