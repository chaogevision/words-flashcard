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
- target-language form, source-backed optional reading/pronunciation, and gloss/language come from source data, never generated pixels or OCR;
- selected target, pronunciation and gloss fonts must cover every required glyph;
- preserve original source Unicode strings; apply NFC normalization only to rendered display text;
- unsupported script shaping or missing glyphs fail before approval;
- connector/no-connector behavior follows mapping policy;
- label panels avoid declared `subjects` and normalized `protected_regions`; a connector may still terminate inside its mapped target region;
- multiple label panels remain separate local overlays near their mapped targets; do not align all panels along one shared horizontal or vertical lane;
- connector style is `connector.v3.light`;
- no red/orange/yellow anchor beads;
- the renderer must be repeatable for identical input data and layout.

If deterministic composition is unavailable, production approval is blocked with `COMPOSER_UNAVAILABLE`.

`protected_regions` is an optional list of normalized `[x_min, y_min, x_max, y_max]` boxes on each card. Use it for important illustrated targets or additional visual subjects that the opaque label panels must not cover. The Stage 09 QA report must record target-region overlap; any overlap above 2% blocks the preview/approval gate.
