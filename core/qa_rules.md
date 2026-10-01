# Core QA Rules

## Hard QA dimensions
### Data QA
- exact English string;
- exact IPA when supplied;
- exact Chinese gloss;
- correct curriculum identity/sense;
- no duplicated/missing target.

### Semantic QA
- scene communicates intended textbook sense;
- target object/action/state is present and distinguishable;
- no misleading substitute.

### Mapping QA
- connector/no-connector behavior matches mapping mode;
- endpoint lands on the semantic target or relation/action zone;
- context words are not forced onto random objects.

### Layout QA
- labels readable and inside safe area;
- no label covers faces, hands, key actions or target objects;
- adequate padding and spacing;
- no avoidable long connector geometry;
- target count is appropriate for the layout template.

### Connector QA
- token is `connector.v3.light`;
- lines are pale, thin and low-salience;
- no red/orange/yellow beads;
- no avoidable crossings;
- platform-specific hard length thresholds pass.

### Style QA
- batch style is coherent;
- no pseudo-text/signage contamination;
- no rendering-family drift;
- no edge artifacts, blur blobs or unexplained shapes.

### Provenance QA
- Stage 08 teaching text came from authoritative data;
- active Skill version and Adapter recorded;
- final filename/card ID unique.

## Standard error codes
`SOURCE_DATA_AMBIGUOUS`
`COVERAGE_ERROR`
`SCENE_GROUP_WEAK`
`BASE_TEXT_CONTAMINATION`
`TARGET_MISSING`
`TEXT_ERROR`
`LINE_MAPPING_ERROR`
`LAYOUT_COLLISION`
`STYLE_FAIL_CONNECTOR_V3`
`STYLE_DRIFT`
`COMPOSER_UNAVAILABLE`

Platform Adapters may add codes but may not weaken these gates.
