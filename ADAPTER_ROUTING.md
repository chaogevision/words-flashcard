# Platform Adapter Routing

## Purpose
The Skill uses one shared Core and multiple platform-specific Adapters. The active Adapter is selected by the actual execution environment.

## Rule stack
Effective production rules are resolved in this order:

1. **Agent Contract** — cross-agent hard contract
2. **Core Skill** — curriculum, workflow, visual, connector, QA standards
3. **Active Platform Adapter** — platform-specific corrections and thresholds
4. **Current Task Configuration** — grade, textbook, unit, card plan, batch settings

Later layers may tighten execution details but may not weaken earlier hard rules.

## Adapter selection

| Execution platform | Adapter |
|---|---|
| OpenAI / ChatGPT environment | `adapters/openai/ADAPTER.md` |
| Doubao Work / 豆包工作 | `adapters/doubao_work/ADAPTER.md` |
| Qwen Office / 千问办公 | `adapters/qwen_office/ADAPTER.md` |
| WorkBuddy | `adapters/workbuddy/ADAPTER.md` |
| Unknown/generic Agent | `adapters/generic/ADAPTER_TEMPLATE.md` until a tested adapter exists |

For a multilingual run, load exactly one locale-matched `languages/<locale>/profile.json` in addition to the platform Adapter. A language profile governs text/script facts; a platform Adapter governs tool and runtime mechanics. Neither may weaken the shared Core gates.

## Important behavior
Do NOT merge every platform's corrective rules into one giant prompt.

Example:
- Qwen Office should read Core + Qwen Office Adapter.
- Doubao Work should read Core + Doubao Work Adapter.
- Doubao-specific label oversizing rules do not automatically apply to Qwen if Qwen does not show that failure.

## Shared rules remain shared
All platforms still use:
- exact curriculum Source of Truth;
- Stage 01–11 pipeline;
- deterministic teaching text;
- the audience-matched `primary_art.png`, `middle_art.png` or `high_art.png` attached from `assets/grade_style_references/` as an actual Stage 07 image input for every card;
- a hard stop when the platform cannot attach that reference; prose-only style instructions cannot pass the gate;
- per-card reference path, SHA-256 and attachment status in generation metadata and QA;
- Flashcard Visual Spec V2;
- `connector.v3.light`;
- Core mapping modes;
- hard QA approval gate.

The style reference is selected by learner audience, never by target language. Every capable Agent must attach the actual matching `*_art.png` image on each Stage 07 request. If the platform cannot accept the image or render the declared script, stop before approval and record the exact capability error.

## Adapter identification
At the beginning of a production run, write the following into the run manifest:

```json
{
  "skill_version": "2.7.0",
  "target_language": "fr-FR",
  "language_profile": "languages/fr-FR/profile.json",
  "platform": "qwen_office",
  "adapter": "adapters/qwen_office/ADAPTER.md",
  "visual_spec": "Flashcard Visual Spec V2",
  "connector": "connector.v3.light",
  "style_reference": "assets/grade_style_references/middle_art.png",
  "style_reference_sha256": "<sha256 of middle_art.png>"
}
```

This makes platform-specific behavior auditable and reproducible.

Every Adapter must map the shared style-reference input to its platform's image-generation request. If no mapping is supported, return `STYLE_REFERENCE_UNAVAILABLE` and stop before Stage 07.
