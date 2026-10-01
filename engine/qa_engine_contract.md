# QA Engine Contract

Input:
- authoritative source records;
- SceneBrief;
- LayoutSpec;
- base asset metadata;
- composed final image;
- active Adapter and Skill version.

Output: `QAReport` conforming to `schemas/qa_report.schema.json`.

Required dimensions:
- Data QA
- Semantic QA
- Mapping QA
- Layout QA
- Connector QA
- Style QA
- Provenance QA

Core hard failures block approval. Adapter checks are additive. A repaired card must be rechecked before approval.
