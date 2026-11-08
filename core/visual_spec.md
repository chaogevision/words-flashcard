# Flashcard Visual Spec V2

## Stable card structure
- Use the Primary English Flash Words multiword scene-card format at every grade: one coherent scene, related vocabulary targets, exact English/IPA/Chinese labels, and mapping-appropriate connectors.
- The illustration remains the visual focus; labels support it and connectors stay low-salience.
- Do not add a topic title, grade label, top header, banner, or decorative frame unless the user explicitly requests one. The default card consists of the scene illustration plus the vocabulary labels and useful connectors.
- Never import the Single Word Flash Cards one-word-per-card layout, example-sentence panel, related-word footer, or page chrome.

## Grade-appropriate scene illustration
Use curriculum grade or the user's stated audience to select age cues. Preserve one coherent educational illustration family across a batch; vary character age, setting, proportions, palette, and energy to fit the learner.

| Audience | Illustration direction |
|---|---|
| Primary / elementary | Bright, playful storybook illustration with rounded forms, clear silhouettes, warm or lively color accents, and school-age children. Keep objects and actions easy to identify; avoid making older primary pupils look like toddlers. |
| Middle school | Contemporary school or youth-life settings, adolescent proportions and expressions, and a more restrained, clean palette than primary. Keep the scene energetic and approachable without preschool styling. |
| High school | Older teenage proportions, more mature academic or everyday settings, refined educational illustration, and a balanced, quieter palette. Avoid childish proportions and decorative motifs that make the scene feel intended for much younger children. |

These are guidance, not rigid age stereotypes. Let the vocabulary group and teaching sense determine the scene. If the grade is unknown, keep the established batch style and ask only when age materially affects the scene.

## Style reference images
`assets/grade_style_references/` ships one full-scene art reference per school band:
`primary_art.png`, `middle_art.png`, and `high_art.png` (640x960). Each is a
standalone illustration with no flashcard labels or layout. They define the
matching band's rendering family: medium, linework, palette, character rendering,
light and level of detail.

**Attach only the matching `<band>_art.png` to the image model.** The complete
`primary.png`, `middle.png`, and `high.png` cards stay as approval references for
label hierarchy and layout; do not send them as generation references.

**The reference is an input, not a description.** Stage 07 MUST attach the
band-matching file as the image-model input (`image1`) and MUST ask the model to
match its rendering family. Describing the style in words only is not compliance:
a text-only prompt reproduces the wording, not the look, and the batch drifts.

Rules:
1. Select `primary_art.png` for primary, `middle_art.png` for middle school,
   and `high_art.png` for high school. Infer the band from the source textbook or
   the user's stated audience; if neither identifies it, clarify before
   generation. Attach the selected file as an actual image input to every Stage
   07 request. A prose-only description is not a substitute.
2. One reference per batch. Never mix bands inside a batch. If a platform cannot
   attach an image input, stop with `STYLE_REFERENCE_UNAVAILABLE`.
3. Record the relative path and SHA-256 in the CompiledPrompt, base-asset
   metadata and run manifest. Set `style_reference_attached: true` only after the
   actual generation request includes that file. Missing attachment evidence is
   a hard QA failure.
4. The reference governs rendering only. Ignore its typography, grade/topic
   headings, title bands, page borders, one-word card structure, sentence panels
   and related-word footers, and NEVER copy its teaching text into the base.
5. `assets/style_references/connector-light-01.png`, `connector-light-02.png` and
   `assets/golden_set/G3A-U01-C01-approved.png` are approval references for
   layout, label hierarchy and connector salience. They are for comparison at
   review time, not inputs to the image model.

## Label cards
- white / light-warm rounded rectangle;
- subtle shadow, no heavy border;
- English: dominant, bold, deep navy;
- IPA: secondary gray-blue;
- Chinese gloss: secondary dark neutral;
- sufficient internal padding and line spacing;
- long phrases enlarge/wrap the card rather than shrinking text excessively.

## Layout hierarchy
`illustration subject > vocabulary label > connector`.
Connector must never become the visual protagonist. Keep labels clear of faces, hands, actions, and target objects.

## Base illustration rule
Stage 07 contains no instructional English, IPA, Chinese, label cards, arrows, anchor dots or connector graphics. Do not bake in a card title, grade label, header, or decorative frame.

## Style consistency
Use one stable illustration/rendering family per batch, while applying the age cues above. Keep the active `connector.v3.light` token and all deterministic teaching-text rules unchanged.
