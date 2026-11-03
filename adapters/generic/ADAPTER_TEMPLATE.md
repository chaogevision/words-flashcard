# Generic Agent Adapter Template

Fill in the implementation for each contract capability.

```yaml
adapter_name: YOUR_AGENT
capabilities:
  structured_reasoning: IMPLEMENTATION
  read_files: IMPLEMENTATION
  write_files: IMPLEMENTATION
  image_generate: IMPLEMENTATION
  style_reference_input: IMPLEMENTATION_OR_UNAVAILABLE
  image_inspect: IMPLEMENTATION
  deterministic_compose: IMPLEMENTATION_OR_UNAVAILABLE
  image_edit: IMPLEMENTATION_OR_UNAVAILABLE
```

## Required behavior
- Respect all Stage 01–11 stage contracts.
- Return explicit errors; never silently skip hard gates.
- Attach the band-matched `assets/grade_style_references/<band>_art.png` to every Stage 07 image-generation request; record path, SHA-256 and actual per-card attachment status.
- If the platform cannot accept a reference image, stop with `STYLE_REFERENCE_UNAVAILABLE`; never substitute style prose.
- Use `connector.v3.light`.
- Never mark a generated-text mockup `APPROVED`.

## If deterministic_compose is unavailable
Stop after Stage 07 or hand off to a renderer. Set error `COMPOSER_UNAVAILABLE`.
