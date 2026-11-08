# Core Workflow — Stage 01–11

This document defines the platform-independent production lifecycle.

## Stage 01 — Parse Vocabulary
Input: curriculum vocabulary source and, for a multilingual run, exactly one target-locale Language Profile.
Output: `VocabularyMaster[]`.
Rules:
- preserve exact source spelling, script, locale, any supplied reading/pronunciation, gloss text/language, unit, page and intended sense;
- use a stable curriculum identity key including target language and locale;
- keep original Unicode source strings; NFC may be used only in the render layer;
- stop if a required font glyph or shaping capability is missing;
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
Layout must anticipate labels; it must not treat labels as a late overlay after the scene is fixed. Give every concrete target a scene-specific anchor and distribute label zones at varied heights; do not assign every anchor the same y-coordinate or line all labels into one row.
Use small, irregular local label pockets around target relationships. Never solve crowding by reserving a shared full-width horizontal or vertical band in the illustration.

## Stage 06 — Prompt Compile
Compile scene + layout + visual rules into a base-illustration request. Select the audience-matched art-only style image, verify its file and SHA-256, and include it as an image input in the compiled request.
Hard requirement: prompt explicitly forbids all instructional text, in every script, plus readings, glosses, label cards and connector graphics.
Hard requirement: a prose description without the actual style image input is an invalid compilation.

## Stage 07 — Base Illustration
Attach the selected style image to the actual generation request, then generate exactly one base illustration per card.
Hard requirement: zero instructional typography and zero teaching connectors.
If the platform bakes labels or readable teaching text into the illustration, Stage 07 fails.
If the image model cannot accept the style image, stop before generation. Record the reference path, SHA-256 and actual attachment status per card.

## Stage 08 — Deterministic Compose
Render the authoritative target-language form, source-backed optional reading/pronunciation, gloss in its declared language, label cards and connector graphics deterministically.
Generated pixels/OCR are never the authority for teaching text.
Inspect the generated full-size scene before composing: update target anchors and subject/target protection boxes to match the actual image, then check that separate labels do not overlap faces, actions or targets or align into a banner-like row.

## Stage 09 — QA
Run data, semantic, mapping, layout, connector, style and provenance QA.
Any hard failure blocks approval.
Verify the style reference path and file hash, and require per-card evidence that the matching image was attached to Stage 07. A missing, mismatched or unattached reference is a hard failure.
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
