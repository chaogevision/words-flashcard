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
The packaged files under `assets/grade_style_references/` come from the user's Single Word Flash Cards style references:
- `primary.png`
- `middle.png`
- `high.png`

Use them only to inform the scene illustration's character rendering, palette, texture, and mood. Ignore their typography, grade/topic headings, title bands, page borders, one-word card structure, sentence panels, and related-word footers. Never copy their teaching text into a new base illustration.

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
