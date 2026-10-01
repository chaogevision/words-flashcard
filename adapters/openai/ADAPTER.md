# OpenAI Adapter

## Role
Map the Agent Contract to an OpenAI-capable environment.

## Capability mapping
- structured reasoning -> ChatGPT model
- file read/write -> project/file tools + local runtime when available
- image generation/edit -> image generation capability
- deterministic compose -> Python/PIL or equivalent deterministic renderer
- image inspect -> model vision + structured QA rules

## Execution rules
1. Read source files before planning.
2. Generate Stage 07 images one card at a time when batch image generation risks collage/grid behavior.
3. Explicitly request a **base illustration only** at Stage 07.
4. Never trust generated text for Stage 08.
5. Use deterministic rendering for English/IPA/Chinese and connector graphics.
6. Run QA after composition and repair only the failing layer where possible.

## Environment-specific paths
Do not encode `/mnt/data` or other runtime paths into core schemas. Paths belong in run manifests or adapter configuration.
