# Artifact Store Contract

The runtime may use any filesystem/object store, but must preserve stable logical artifacts per card:

- source vocabulary identity IDs;
- card plan item;
- scene brief;
- layout spec;
- compiled prompt;
- base illustration + base asset metadata;
- final composed image;
- QA report;
- repair actions when present;
- approved manifest entry.

Physical paths are Adapter/runtime details. Do not hard-code `/mnt/data` or platform-specific paths in Core schemas.
