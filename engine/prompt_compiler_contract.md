# Prompt Compiler Contract

Input:
- validated `SceneBrief`;
- validated `LayoutSpec`;
- Core visual rules;
- active platform Adapter;
- current task configuration.

Output: `CompiledPrompt` conforming to `schemas/compiled_prompt.schema.json`.

Hard invariants:
1. request exactly one base illustration per card;
2. explicitly forbid English teaching text, IPA, Chinese gloss, label cards, arrows, connector lines and anchor dots;
3. preserve visual target requirements and forbidden constraints;
4. include layout-aware negative-space guidance;
5. record the active adapter ID;
6. select the audience-matched art-only reference (`primary_art.png`,
   `middle_art.png` or `high_art.png`), verify its file and SHA-256, and emit its
   path and hash on the `CompiledPrompt`;
7. map the recorded reference to an actual image input on every Stage 07 request
   and name the sample's rendering family in the prompt body. A prompt that only
   describes the style in prose is not a valid compilation;
8. if the active Agent or image model cannot accept the reference image, stop
   before generation with `STYLE_REFERENCE_UNAVAILABLE`.
