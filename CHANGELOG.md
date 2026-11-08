# Changelog

# 2.7.0 — Multilingual multiword cards
- Added Japanese, French, German, Korean and Spanish locale profiles with Unicode display, optional source-backed readings, locale-aware terminology and language-specific display rules.
- Generalized vocabulary, visual, agent, composer and QA contracts from English / IPA / Chinese to target form / optional reading / declared-language gloss while retaining legacy English inputs.
- Added a deterministic multilingual composer and QA gate. Missing fonts or unsupported script shaping fail closed.
- Preserved the hard actual-image reference rule for every agent: the audience-matched art-only sample, matching SHA-256 and per-card attachment evidence remain required for Stage 07 and QA.
- Added local preview status. Preview profiles can create review cards but cannot claim production approval until language and renderer validation is complete.
- Corrected a prompt conflict that reserved a horizontal label band and split the scene. Core, prompt compilation, WorkBuddy and the Japanese preview builder now require a connected full-frame scene with distributed targets and only small irregular label pockets. This supersedes the historical 2.6.0 calm-top-band recommendation below.

## 2.6.0 — Style prose vs style sample; labels off torsos; group-scene composition
- **Cross-Agent reference gate:** every Stage 07 request must attach the audience-matched art-only reference image. Compiled prompts, base-asset metadata, approved manifests and QA now require reference path/SHA-256 and per-card attachment evidence; missing or mismatched attachments block approval. OpenAI, Doubao, Qwen Office, WorkBuddy and generic routing all inherit this rule.
- Corrected the reference selection and WorkBuddy manifest examples to use `primary_art.png`, `middle_art.png` or `high_art.png`; the full card images are review references only.
- Tightened WorkBuddy QA to compare the recorded digest with the packaged asset and reject cards whose actual generation request did not include the reference. QA report output now matches the QAReport schema.
- **The prose was beating the attachment.** 2.5.0 attached `primary_art.png`, but the prompt still described "soft gouache and watercolour washes" while the sample is crisp ink linework with flat cel shading. A full 8-card batch came back as pale watercolour — the same result as attaching nothing. Rule added: describe the sample's real medium, add an explicit "do not render in watercolour/gouache/pastel" clause, and treat the reference as a ceiling on what the prose may claim.
- **Letterboxing had a second cause.** A 2:3 sample on a 2:3 canvas still produced a 12% paper margin on all four sides plus a drop shadow, because the model read the sample as framed artwork. A `FULL-BLEED` clause (no margin, no mat, no inset card, no drop shadow) removed it: 8 of 8 bases now trim to zero.
- **Historical composition rule, superseded by 2.7.0.** The earlier calm-top-band rule helped shorten connectors on a dense group card, but later caused split-scene artifacts when applied as a shared label lane. Current prompts keep connected scenes and use small, irregular local pockets instead.
- **Placement cost rebuilt with three measured terms**: a busy map (edge energy under the candidate box) so cards stop landing on torsos and sleeves, a crossing cost so an arrow never runs across another card or a face, and a body-zone charge for the neck/chest strip directly under a head. Body zone stays a cost, not a hard reject — as a hard rule the dense family cards lost their only legal spot and the worst connector rose to 0.42 W.
- **Variant selection was inverted.** The 0.34/0.28/0.24 retry ladder picked the layout with the shortest worst connector, which is often the layout that puts cards on people. It now ranks `(subject hits, geometry_limited, body-zone labels, hard fails, worst connector)`.
- **The ceiling is now checked on the straight reach.** An elbow that adds 4 px was being counted as a longer connector, triggering relocations that ended on chests. The report field `connector_norm` is the straight edge-to-anchor distance; QA reads the same value.
- Optional debug: `FLASHCARD_DEBUG=1` prints the top candidates per label plus the final placement with its cost components.
- Measured on the regenerated 8-card batch (1536x2304 bases, `quality: medium`, `primary_art.png` at `input_fidelity: high`): 8 of 8 cards APPROVED, 34 of 34 terms covered, worst connector 0.26 W (was 0.61 W in 2.3.0), zero labels on a face, zero `geometry_limited`, zero border trim.

## 2.5.0 — Style reference actually attached; labels may not cover people
- **Style reference was dead weight.** `assets/grade_style_references/primary.png`, `middle.png` and `high.png` shipped in 2.3.0 but no stage ever passed them to the image model; the look existed only as prose in the prompt, so batches drifted. `core/visual_spec.md`, `engine/prompt_compiler_contract.md` and the WorkBuddy adapter now require the band sample to be attached as `image1` with `input_fidelity: high`.
- Added `<band>_art.png` (640x960) per band: the reference card's illustration area only, cropped to a 2:3 window, with headings, IPA rows, word chips, example panels and the decorative frame removed. The full card risks the model painting the frame or letterboxing around it (observed on a 1536x2304 return: 380 px of flat white top and bottom).
- Added `trim_uniform_border()` to `tools/compose_cards.py`: flat near-white borders are trimmed automatically (cap 24% per side) and reported as `border_trim`. No-op on bases that already bleed to the edge (verified on all 8 reference bases).
- **Labels can no longer cover a person.** Cards declare `subjects` (normalised head/face boxes); the placer inflates them by 0.012 W, rejects any candidate overlapping more than 2% of the label area, and the QA gate fails on `subject_overlap > 2%` or on a card with anchors but no declared subjects.
- Placement rebuilt: candidates are now perimeter ladder + interior grid + a **ring around the label's own anchor** (8 directions x 5 distances); the pairwise-swap search was replaced by coordinate descent, which works with per-label candidates. Label-width retry ladder (0.34 → 0.28 → 0.24 W) shrinks the card instead of stretching the connector.
- Added the `geometry_limited` classification: when no subject-free candidate exists inside the ceiling, the label is reported for review instead of silently violating the ceiling.
- Measured on the reference batch: worst connector 0.13 W on the 5-person card (the card where `mother` used to sit on the adult's head), 0 head overlaps (was 2), 6 of 8 cards APPROVED, 2 flagged `geometry_limited` because five people fill the frame — a scene defect, not a layout defect.
- Style verification: attaching the sample moved a text-only generation from soft gouache to the sample's own line quality, saturation and cel shading.

## 2.4.0 — WorkBuddy Adapter + executable Stage 08/09 tools
- Added the WorkBuddy Adapter, built from a measured failure audit of a real 8-card batch: 22 of 30 connectors exceeded 0.30 × canvas width (worst 0.61), bases were generated at 1024×1536 and upscaled 2.0×, and the generator watermark band was left inside the frames.
- Root cause recorded: label-first layout pinned labels to fixed perimeter corners before target positions were known.
- Added `tools/compose_cards.py`: target-first slot scoring, hard connector ceiling (preferred 0.15 W, hard 0.26 W), elbow and margin routing, CJK character wrapping, warm-white label cards, PNG + JPEG export.
- Added `tools/qa_check.py`: Stage 09 gate covering curriculum text equality, connector ratio, label collisions and width, base resolution and upscale ratio; a hard fail blocks `APPROVED`.
- Tightened WorkBuddy asset policy: request 1536×2304 bases at `quality: medium` (the 5 MB transfer limit rejects `high` at that size), upscale ≤ 1.4×, forbid white halo / sticker outline, export an optimised PNG plus a JPEG q90 sharing copy (measured 8.98 MB → 7.70 MB PNG, 1.4 MB JPEG).
- Recorded the tuned placement constants (interior penalty 0.10 W, target protection 0.11 W, pairwise swap search) that took the worst connector from 0.61 W to 0.23 W on the reference batch.
- Registered the new adapter in the routing table, the Agent Contract and the conformance path.

## 2.3.0 — Flashcard rename and cross-grade scene style
- Renamed the skill slug to `flashcard` and its UI display name to `Flashcard`.
- Added primary, middle-school, and high-school illustration guidance while keeping the Primary multiword scene-card structure unchanged.
- Set no topic title, grade label, top header, banner, or decorative frame as the default card treatment.
- Bundled the three user-selected Single Word style references for illustration-only use.


## 2.2.2 — Completeness and contract-consistency hotfix
- Added the missing `engine/` interface layer promised by README architecture.
- Added `core/design_tokens.json`, required by deterministic Stage 08 composition.
- Added Stage 07 base-asset and Stage 10 repair-action schemas.
- Added array wrapper schemas for VocabularyMaster and CardPlanSet.
- Added an actual Golden Set reference and usage rules.
- Tightened manifest/run-state provenance requirements with platform identity.
- Required `mapping_mode` in LayoutSpec labels.
- Replaced the package validator with strict hash, meta-schema, reference, Engine and Golden Set checks.
- Corrected adapter version headings.


## 2.2.0
- Added Qwen Office / 千问办公 Adapter.
- Added Qwen observed-failure audit.
- Added adapter routing specification.
- Added Qwen card-type router and teaching-mechanism grouping gate.
- Added Qwen connector length, endpoint, context-proximity, cutaway, object-differentiation and density QA rules.
- Added adapter selection to Agent Contract and conformance checklist.
- Retained Doubao Work Adapter and Connector V3 unchanged.

## 2.1.0
- Added Doubao Work Adapter based on observed production failures.
- Tightened Doubao label scale, connector geometry, text contamination and style drift QA.
## 2.2.1 — Packaging hotfix
- Restored mandatory `core/` documents referenced by `SKILL.md`.
- Restored mandatory `schemas/` JSON Schemas referenced by `AGENT_CONTRACT.md`.
- Added `PACKAGE_MANIFEST.json`.
- Added `tools/validate_package.py` to fail fast on missing required files or invalid JSON schemas.
- Restored all supported platform adapters in the distributable folder.
- Root cause: V2.2 packaging assembled only root docs/adapters and omitted Core/Schema directories while the contract still referenced them.

