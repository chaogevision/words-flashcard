# Source of Truth

## Authoritative fields
The supplied source is authoritative for:
- target-language spelling, exact source form, script, locale and phrase boundaries;
- a lemma or inflected form when identified by the source;
- IPA, kana reading, romanization or other pronunciation notation only when supplied;
- gloss text and its language;
- grammatical information only when supplied or independently verified and recorded;
- unit / page / lesson association and intended sense.

## Prohibited behavior
- Do not silently normalize spelling, accents, case, articles, spacing or “improve” source wording.
- NFC normalization is permitted only for rendering; retain the original code-point sequence in the source record and manifest.
- Do not invent a reading, IPA, transliteration, grammatical gender, article, inflection, or gloss to fill a missing field.
- Do not use image-model text as the source for Stage 08.
- Do not use OCR from a generated illustration to reconstruct curriculum text.
- Do not merge two repeated terms from different units/senses solely because the surface string matches.

## Identity key
Use a curriculum identity key that distinguishes language, locale and repeated senses, e.g.:
`target_language|locale|grade|book|unit|term|sense_id`.

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
