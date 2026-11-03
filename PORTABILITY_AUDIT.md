# Portability Audit

## Agent-independent core
- curriculum source-of-truth rules
- grouping logic
- mapping modes
- Scene Brief semantics
- Layout Spec semantics
- Visual Spec
- audience-matched style-reference selection and actual image-input attachment
- Connector V3
- QA hard gates
- lifecycle and manifests

## Adapter-dependent concerns
- model/tool invocation syntax
- image generation API
- runtime filesystem paths
- deterministic renderer implementation
- connector/file upload semantics
- batch concurrency limits

## Portability assessment
This V2 package is designed so that core behavior does not depend on a particular Agent. A new Agent is production-compatible once it:
1. declares its capability mapping;
2. maps the required style image to its generation API or stops before Stage 07 if unsupported;
3. implements or delegates deterministic composition;
4. validates the provided schemas;
5. respects lifecycle and hard QA gates.

A text-only Agent can execute Stages 01–06 but cannot complete production approval without an image-generation and composition handoff.
