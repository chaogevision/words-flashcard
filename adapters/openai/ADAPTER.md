# OpenAI Adapter

## Role
Map the Agent Contract to an OpenAI-capable environment.

## Capability mapping
- structured reasoning -> ChatGPT model
- file read/write -> project/file tools + local runtime when available
- image generation/edit -> image generation capability
- style reference image -> `referenced_image_paths` on every Stage 07 image-generation request
- deterministic compose -> Python/PIL or equivalent deterministic renderer
- image inspect -> model vision + structured QA rules

## Execution rules
1. Read source files before planning.
2. Generate Stage 07 images one card at a time when batch image generation risks collage/grid behavior.
3. Attach the band-matched `<band>_art.png` from `assets/grade_style_references/` through `referenced_image_paths` on every Stage 07 request; record the path, SHA-256 and attachment status.
4. If the active image-generation tool cannot accept that reference image, stop before generation with `STYLE_REFERENCE_UNAVAILABLE`.
5. Explicitly request a **base illustration only** at Stage 07.
6. Never trust generated text for Stage 08.
7. Use deterministic rendering for English/IPA/Chinese and connector graphics.
8. Run QA after composition and repair only the failing layer where possible.

## Environment-specific paths
Do not encode `/mnt/data` or other runtime paths into core schemas. Paths belong in run manifests or adapter configuration.
