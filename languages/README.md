# Language Profiles

Each profile is a data contract for one target language and locale. Core grouping, scene illustration, label hierarchy, connectors, source coverage and the image-style-reference gate remain shared across languages.

The first preview profiles are Japanese (`ja-JP`), French (`fr-FR`), German (`de-DE`), Korean (`ko-KR`) and Spanish (`es-ES`). Their current status is `preview`: local demonstration cards are not a substitute for curriculum-backed language validation.

## Profile contract

- `language` and `locale` identify the language variant.
- `writing_system` declares script, direction, Unicode ranges and shaping class.
- `term_wrap` selects word wrapping for Latin text or grapheme-safe wrapping for scripts without spaces.
- `reading` describes whether a source-backed pronunciation or reading line may appear. Romanization is never invented by default.
- `gloss` records the default meaning language. Each vocabulary item still declares its actual gloss language and source.
- `morphology` and `display_rules` preserve language-specific facts without putting them into the universal renderer.
- `status: preview` allows local sample composition. Only `validated` profiles may produce a production-approved batch.

The renderer must fail closed when the runtime cannot shape the declared script or when its selected font lacks required glyphs. Profiles describe extensibility; they do not certify a script until an adapter/runtime has passed its image and text QA.

Adding a locale variant must not silently replace source spelling, article, pronunciation, or sense. Record the locale in every batch manifest and keep exact source forms in vocabulary entries.
