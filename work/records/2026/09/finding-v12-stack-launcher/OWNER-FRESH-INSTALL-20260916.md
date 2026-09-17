# W183883 — fresh installation starts with zero Jobs

Confirmed by Slawomir on 2026-09-16; recorded by baton.prompt.

## Observed problem and supersession

The current bootstrap requires jobs with job_id, work_id, line_declared_base,
canonical_target_id and source_worker_id before an instance can be installed.
This carries a preconfigured execution composition into the fresh installer.
The owner rejected this boundary: "Why are we asking for any job, this is a
fresh install" and confirmed the correction below.

This explicitly supersedes the mandatory preselected Job/input gate in
OWNER-READY-189577.md, the preceding PLAN current section, and any earlier ruling
or acceptance that requires Job-specific selections to bootstrap/start an instance.
Preserve earlier implementation/review evidence; it does not prove this corrected
fresh-install outcome. The standalone bundle, inferred source, independent storage,
version stamping and destination-local lifecycle requirements remain selected.

## Confirmed behavior

- Keep `just bootstrap <instance-json> <absolute-destination>`.
- Install the bundled application and initialize empty databases/configuration.
- Generate the instance authority identity once and persist it at the destination;
  subsequent lifecycle operations reuse it. Separate installs have separate IDs.
- Save instance-level settings and emit the destination-local justfile.
- `just start`, `just status`, `just monitor`, `just stop` work with zero Jobs.
  Start runs the real idle scheduler/publisher, with honest empty status, rather
  than a dummy success branch or a fabricated seed Job.
- Fresh inputs require no Job/Work IDs, Job base commits, target identities,
  per-Job worker assignments or Job-specific integration reference/observer.
  These are supplied and validated when creating/configuring actual Jobs.
- Do not create placeholder Work, Jobs or per-Work grants to satisfy the old
  composition validator. Preserve validation when real Jobs are later supplied.
- Source remains the checkout containing v12/justfile; installed operation is
  independent of that checkout. Keep instance repository preparation independent
  of future Job bindings; do not require a workload to install runtime/storage.

## Bounded delivery and verification

Implement the smallest bootstrap/runtime-composition correction that achieves
this boundary. Supply a complete runnable minimal instance-only JSON in the guide,
explaining any remaining genuine instance settings. Do not substitute another
placeholder-filled production worksheet. Explain the existing subsequent Job
creation/configuration path and any concrete missing capability honestly; do not
silently expand this correction into a generic scheduling or migration project.

Focused deterministic checks cover no-job input, no synthetic Work/Job records,
generated/persistent/distinct identity, real empty idle lifecycle, source-independent
installed commands, and retained rejection of invalid real Job bindings. Reuse
unchanged relevant evidence; no blanket suite rerun or live model/engine campaign.
Existing Git ownership and independent review rules apply. W183883 remains open;
implementation routes to baton.impl then baton.feat. W177936 stays parked and v11
remains the current coordination authority. No owner production run is requested
using the superseded preconfigured-Job bootstrap packet.
