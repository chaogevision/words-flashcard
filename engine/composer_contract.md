# Deterministic Composer Contract

Input:
- Stage 07 base asset + metadata;
- authoritative vocabulary records;
- `LayoutSpec`;
- `core/design_tokens.json`;
- active Adapter overrides that only tighten Core thresholds.

Output:
- final composed flashcard image;
- deterministic composition metadata sufficient for QA/provenance.

Hard invariants:
- English / IPA / Chinese come from curriculum data, never generated pixels or OCR;
- IPA font must cover all required IPA glyphs;
- CJK font must cover all Chinese glyphs;
- connector/no-connector behavior follows mapping policy;
- connector style is `connector.v3.light`;
- no red/orange/yellow anchor beads;
- the renderer must be repeatable for identical input data and layout.

If deterministic composition is unavailable, production approval is blocked with `COMPOSER_UNAVAILABLE`.
