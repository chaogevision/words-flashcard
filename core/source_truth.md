# Source of Truth

## Authoritative fields
The curriculum source is authoritative for:
- English spelling and phrase boundaries;
- IPA when supplied;
- Chinese gloss;
- unit / page / lesson association;
- intended textbook sense.

## Prohibited behavior
- Do not silently normalize or “improve” textbook wording.
- Do not use image-model text as the source for Stage 08.
- Do not use OCR from a generated illustration to reconstruct curriculum text.
- Do not merge two repeated terms from different units/senses solely because the surface string matches.

## Identity key
Use a curriculum identity key that distinguishes repeated terms, e.g.:
`grade|book|unit|term|sense_id`.

## Ambiguity
If the source is unclear, emit `SOURCE_DATA_AMBIGUOUS` and require review.
A review correction must preserve the original source value in provenance.

## Provenance
Every approved card must record:
- source identifier;
- vocabulary identity keys;
- active Skill version;
- active platform Adapter;
- visual spec token;
- connector token;
- QA result.
