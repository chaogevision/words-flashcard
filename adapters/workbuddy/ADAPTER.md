# WorkBuddy Adapter — compatible with Skill V2.6.0

## Purpose
Adapt the agent-agnostic flashcard protocol to the observed behavior of
**WorkBuddy** (image generation through the built-in `ImageGen` capability,
deterministic composition through a local Python/PIL renderer).

The Core Skill remains authoritative. This adapter may tighten layout,
connector, asset and QA thresholds, but MUST NOT weaken curriculum facts,
hard QA gates, lifecycle semantics or the active visual tokens.

---

## 1. Capability mapping

| Contract capability | WorkBuddy implementation |
|---|---|
| `structured_reasoning` | the driving model |
| `read_files` / `write_files` | local filesystem tools |
| `image_generate` | `ImageGen` (one call = one card) |
| `style_reference_input` | attach the band-matched `<band>_art.png` as `image1` on every Stage 07 call |
| `image_inspect` | vision read of the produced PNG |
| `deterministic_compose` | `tools/compose_cards.py` (PIL) |
| `image_edit` | `ImageGen` image-to-image, repair only |

`deterministic_compose` is available, so Stage 08 is mandatory and no card may
be approved from a generated mockup.

---

## 2. Observed failure audit (measured, not hypothetical)

Batch: PEP 2024 Grade 3A Unit 1–2, 8 cards / 34 terms, produced without this
adapter.

| Defect | Measurement | Root cause |
|---|---|---|
| connectors far too long | 22 of 30 connectors > 0.30 × canvas width, worst 0.61 × width | labels were assigned to fixed perimeter corners **before** the target position was known (label-first layout) |
| soft illustration | 1024×1536 base upscaled to 2048×2918 (2.0×) | default portrait size was requested, then enlarged twice |
| generator watermark | "AI生成" band in the bottom-right corner of every base asset | the watermark band was not cropped before compose |
| heavy deliverables | 7.0–8.2 MB per PNG | no export size policy |
| clipped gloss | multi-sense glosses overflowed the label card | Latin word-wrap applied to CJK text, which has no spaces |
| style drift | `assets/grade_style_references/primary.png` shipped with the package but was never passed to the model; the style existed only as prose in the prompt | Stage 07 had no rule to attach the reference, and the prompt compiler had no reference field |
| label on a head | `mother` covered the adult's head and hair on a 5-person card | placement protected anchor *points* only — nothing protected the people themselves |

Every rule below exists because one of those defects was observed.

---

## 3. Stage 07 — base illustration rules

1. Request **1536×2304 at `quality: medium`**: that is the largest portrait size the
   image capability returns inside its 5 MB transfer limit. `quality: high` at the
   same size is rejected for exceeding the limit; if a scene only reads well at
   high quality, fall back to 1024×1536 `high` and record the fallback in the
   manifest.
2. **Attach the packaged style sample as `image1`** —
   `assets/grade_style_references/primary_art.png` for primary,
   `middle_art.png` for middle school, or `high_art.png` for high school — with
   `input_fidelity: high`, and state in the prompt that the attachment is a
   **style sample only** (match medium, line quality, colour treatment, shading
   and facial rendering; copy nothing else).
   Never attach the full `primary.png` card: it carries typography, chips and a
   decorative frame, and the model then paints those or letterboxes around them.
   Never mix bands in a batch.
2b. **Describe the sample's actual medium in the prose, or the prose wins.**
   Measured failure: the sample is a modern cel-shaded illustration (crisp ink
   line, flat colour blocks, glossy highlights), but the prompt said "soft gouache
   and watercolour washes". The text overrode the attachment and the whole batch
   came back as pale watercolour — same as generating with no reference at all.
   Write the medium the sample really is, and add an explicit "do not render in
   watercolour / gouache / pastel" clause. The reference is a *ceiling* on what
   the prose may claim, never a replacement for it.
3. One `ImageGen` call produces exactly one card. Never batch several cards into
   one prompt.
4. The prompt MUST forbid English teaching text, IPA, Chinese, label cards,
   arrows, dots, frame and border, **and white halo / sticker outline / cutout
   fringe** (observed halo around hair and shoulders in an earlier batch).
5. The prompt MUST ask for the main subject inside the central ~60% of the frame,
   leaving the outer band visually quiet. Labels live in that band.
5b. **Reserve a calm band at the TOP, not only at the sides.** A connector's length
   is normalised by canvas width while vertical space costs 1.5x less per unit, so
   one clear stretch of wall above the heads is worth more than two narrow side
   strips. Ask for "the group in the lower two thirds, the top quarter calm empty
   wall". Measured: a 5-person row whose heads started at y=0.10 could not be
   labelled inside the ceiling at any label width; the same row starting at y=0.40
   placed all five labels in the wall with every connector under 0.26 W.
5c. **Five or more people need a staggered arrangement.** One flat row leaves no
   gap wide enough for a 0.24 W card. Ask for two staggered rows (adults behind,
   children in front, each standing in a gap) and for visible wall between heads.
5d. **Say it is full-bleed.** Attaching a 2:3 sample to a 2:3 canvas still produced
   a 12% paper margin on every side plus a drop shadow (the model read the sample as
   a framed artwork). Add: "the painting fills the whole canvas edge to edge; no
   white margin, no paper border, no mat, no inset card, no drop shadow". After that
   clause, 8 of 8 bases came back with zero border trim.
6. Reject a base whose subject intrudes into the perimeter band, or whose edges
   carry a white fringe: regenerate rather than patch at compose time.
7. **Crop the generator watermark band before compose** (`crop_bottom_px` in the
   run config, 116 px at 1536 width, 77 px at 1024 width). Never cover it with a
   label card.
8. **Reject a letterboxed base.** When a style sample is attached the model may
   paint inside a white band (measured: 380 px of flat white at the top *and*
   bottom of a 1536x2304 return). `tools/compose_cards.py` auto-trims flat near-white
   borders (`trim_border`, capped at 24% per side) and records `border_trim` in the
   report; a trim larger than 15% per side means the base must be regenerated, not
   shipped.
9. Record the base asset path, size, prompt, quality setting **and the style
   reference path plus its sha256** in the run manifest.

## 4. Stage 08 — deterministic compose rules

Canvas: `width × (cropped base height × width / base width)`, width 2048.
Upscale ratio must stay **≤ 1.4×** — above that the art visibly softens.

Typography (from `core/design_tokens.json`, scaled by `width / 1536`):

| role | preferred | hard minimum |
|---|---|---|
| English | 76 px | 54 px |
| IPA | 42 px | 28 px |
| Chinese | 42 px | 28 px |

Label cards: warm white `#FFFDF9` at 98%, radius 0.018 × width, hairline navy
outline at ~6% alpha, soft shadow, padding 0.024 / 0.016 × width, and a hard
width cap of **34% of canvas width**. Wrap Latin text on spaces and CJK text on
characters; never shrink below the hard minimum to force a fit.

### 4.1 Connector ceiling — hard requirement

Normalised by canvas width:

| band | value | action |
|---|---|---|
| preferred | ≤ 0.15 W | ship |
| warning | 0.15 – 0.26 W | ship only if the route hugs a margin |
| hard fail | > 0.26 W | relocate the label; if impossible, drop an `optional` connector and record it; a `required` connector fails the card |
| geometry-limited | any length | only when **no** subject-free candidate exists inside the ceiling — reported as `geometry_limited` and required to be reviewed; the scene is at fault, not the layout |

### 4.2 Target-first placement — the actual fix

Do **not** start from top-left / top-right / bottom-left / bottom-right slots.

1. Compute every label's box from its own text first.
2. Candidate set per label = perimeter ladder ∪ interior grid ∪ **ring around its
   own anchor** (8 directions × 5 distances, 0.04–0.26 W). The ring is what lets a
   card sit just above/beside a head, the way a person would label it.
3. **Subjects are hard obstacles.** Every card declares `subjects`: normalised
   boxes over **heads/faces only** (plus any prop the words point at, e.g. a framed
   photo). Do not list full bodies: measured on the 5-person card, body-height
   boxes pushed the worst connector to 0.94 W because people fill the frame — the
   remedy there is a quieter scene, not a longer line.
   The renderer inflates each box by 0.012 W and rejects any candidate that
   overlaps it by more than 2% of the label area. Covering a person is a defect,
   not a cost.
4. Score candidates by distance from the label edge to the anchor, plus penalties
   for covering another label, its own anchor, or approaching another label's
   anchor closer than 0.11 W. Three more terms are required, each measured:
   - **busy map** — mean edge energy under the candidate box, normalised
     (`BUSY_REF` 14, weight 0.16 W). Head boxes cannot catch a card lying on a
     torso or a sleeve; edge energy can, and it is style-independent.
   - **crossing cost** — sample the label-edge → anchor run; every sample that
     falls inside another card (+0.55 W) or inside a face (+0.75 W) is charged.
     This is what stops an arrow from being drawn across a cheek.
   - **body zone** — a card whose horizontal span overlaps a head box by >45% and
     sits within 0.16 H below it (or 0.05 H above it) is on a neck, a chest or a
     hair top. Charge 0.20 W / 0.12 W, scaled 0.6. Keep it as a cost, never as a
     hard reject: as a hard rule, dense family cards lost their only legal spot and
     the worst connector jumped to 0.42 W.
5. Assign hardest labels first (largest unavoidable distance, then `required`
   before `optional`). Then run coordinate descent: re-place one label at a time
   against the others until the total cost stops improving.
6. If a card still cannot fit (dense group scene, long CJK gloss), retry the whole
   card at label widths 0.28 W and 0.24 W and choose the variant by
   `(subject hits, geometry_limited, body-zone labels, hard fails, worst connector)`
   in that order. Ordering by connector length first is a trap: the layout with the
   shortest arrows is often the one that puts the cards on people.
7. Route: straight when short, two-segment elbow when not, margin-hugging
   corridor route as the last resort.
8. Re-check the ceiling **on the straight reach**, not on the routed polyline: an
   elbow that adds 4 px is not a longer reach, and treating it as one sent labels
   into a relocation spiral that ended on torsos. Then relocate once; then classify
   as `geometry_limited` or fail.

`tools/compose_cards.py` implements exactly this. Runs MUST use it (or an
equivalent that satisfies the same checks) instead of hand-placed slot maps.

### 4.3 Tuned constants (validated on the 8-card reference batch)

| constant | value | effect |
|---|---|---|
| perimeter ladder | 10 vertical steps per side + top/bottom centre | keeps labels at the frame edge where the art is quiet |
| interior grid | x ∈ 0.16…0.84 step 0.08, y ∈ 0.14…0.88 step ~0.08 | dense enough to nestle between people |
| interior penalty | 0.06 × W | perimeter still wins when the saving is small |
| anchor ring | 8 directions × distances 0.04 / 0.08 / 0.13 / 0.19 / 0.26 W | a card can sit right beside its target |
| subject clearance | box inflated 0.012 W; overlap > 2% rejected | no label may cover a head or face |
| target protection radius | 0.11 × W | no card may sit on any anchor |
| own-target penalty | 0.45 × W when within 0.03 × W | the card never hides the thing it names |
| label overlap penalty | 3 × overlap area (px²) | hard separation between cards |
| width retry ladder | 0.34 → 0.28 → 0.24 W | shrink the card instead of stretching the connector |

Measured on the reference batch: worst connector 0.61 W → 0.13 W on the 5-person
card, 0 labels overlapping a head (was 2), and 2 labels classified
`geometry_limited` on the dinner scene where five people fill the frame. That last
case is a **scene** defect: regenerate with a quieter perimeter or split the card,
do not relax the subject rule.

## 5. Stage 09 — QA overrides

Additive checks on top of `core/qa_rules.md`:

- connector `reach / canvas_width` ≤ 0.26 for `required` connectors (the report
  field is the straight distance from the card edge to the anchor);
- no label wider than 40% of canvas width;
- no label-rect overlap;
- no base asset narrower than 1536 px;
- no upscale above 1.4×;
- every rendered string equals the curriculum string byte for byte;
- watermarked base assets are rejected;
- base assets narrower than 1536 px fail the gate (the 8-card reference batch
  fails exactly here, by design — those bases were 1024 px);
- visible white halo, sticker outline or cutout fringe on a base fails style QA;
- any label whose `subject_overlap` exceeds 2% of its area fails the card;
- a card with people but no declared `subjects` boxes fails the card (the
  protection cannot be verified, so it is not assumed);
- the run must declare the selected art-only `style_reference` path and SHA-256;
  verify the file hash against the packaged asset;
- every card must record `style_reference_attached: true` only when its actual
  Stage 07 ImageGen request included that file; missing, false or mismatched
  attachment evidence marks the batch `style_unverified` and blocks approval.
- `tools/qa_check.py` verifies the reference path and SHA-256 and requires a
  per-card attachment attestation; setting the field from intent alone is not
  evidence that the image was sent.

Run `tools/qa_check.py`; a non-empty `hard_fail` list blocks `APPROVED`.

## 6. Stage 11 — export rules

- Master: PNG, `optimize=True`, opaque RGB.
- Sharing copy: JPEG quality 90, progressive, same dimensions.
- Measured on the reference batch: 2048×2918 PNG 8.98 MB → 7.70 MB after
  `optimize`; the JPEG q90 copy is 1.4 MB. Ship both.
- Target: PNG ≤ 8 MB, JPEG ≤ 1.5 MB. A PNG far above that means the canvas or the
  palette is wrong.

## 7. Repair ladder (cheapest first)

1. re-compose text only (data or typography changed);
2. re-place labels / re-route connectors (geometry changed);
3. regenerate the base illustration (scene or target is missing);
4. regroup or retemplate the card (the design itself is wrong).

Steps 1–2 never consume image credits; always try them before step 3.

## 8. Run manifest additions

```json
{
  "platform": "workbuddy",
  "adapter": "adapters/workbuddy/ADAPTER.md",
  "base_size": "1536x2304",
  "base_quality": "medium",
  "style_reference": "assets/grade_style_references/primary_art.png",
  "style_reference_sha256": "<sha256 of primary_art.png>",
  "input_fidelity": "high",
  "compose_canvas": "2048x2912",
  "upscale": 1.33,
  "connector_ceiling": {"soft": 0.15, "hard": 0.26},
  "exports": ["png", "jpg90"],
  "cards": [
    {
      "card_id": "G3A-U01-C01",
      "style_reference": "assets/grade_style_references/primary_art.png",
      "style_reference_sha256": "<sha256 of primary_art.png>",
      "style_reference_attached": true
    }
  ]
}
```
