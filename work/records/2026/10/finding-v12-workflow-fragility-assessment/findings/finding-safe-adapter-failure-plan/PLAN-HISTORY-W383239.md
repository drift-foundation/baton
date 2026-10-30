# Current milestone — deliver owner-selected fresh matched typed failures

Owner E376465 selects AMENDMENT-376531.md; DESIGN OBS-3a is pinned. The earlier owner-decision milestone is superseded; PROPOSAL remains historical except for narrow rules explicitly retained in the amendment.

- W376586: producer/current launch/terminal writer-reader source boundary.
- W376587: existing diagnostic/status/viewer/report propagation; depends on W376586.
- W376588: joined deterministic matched-boundary proof; depends on both.
- W371073 remains the joined acceptance consumer and open umbrella; W371076 remains dependent.

Reason for decomposition: wire production/validation and public diagnostic propagation have separate acceptance results; joined evidence prevents either source slice being mistaken for end-to-end or packaged qualification. Shared source changes are serial. W371296 qualification must consume final producer bytes; coordination through the existing endpoint is required. Installer W375516/W376246/W376254 retains its allocation; no installer schema change belongs to this amendment. Any single_worker.py overlap with W375445 is explicitly coordinated before edits.

Reviewer owns this FINDING/PLAN/amendment and append-only review; author owns child PROGRESS and actual source. No live/build/deploy/retained-instance action. Package gaps are reported precisely rather than fabricating qualification or expanding execution.
