# Owner ruling — routine task startup within 60 seconds

Recorded by baton.prompt, 2026-10-20, from the current owner conversation.

Slawomir: "baton/v12 is a failure if this isn't resolved. Tasks must run rapidly,
pick up a few files, read the input/description and off it goes. 60 sec or less"

Clarification: "we cannot be scripting anything, writing tests etc. None of that"

Further clarification: "agent itself can take 30 min to think and code but prep
time must be tiny"

Confirmed outcome: routine task startup takes at most 60 seconds, consuming the
task description and a small set of selected input files. The routine startup
path includes no script authoring, test writing or bespoke execution-packet
development. Producing a reusable preparer alone is insufficient acceptance if
each subsequent run still requires that work.

The 60-second requirement applies to preparation/startup, not the assigned
agent's substantive thinking, coding or task verification after it starts.
Thirty minutes of real task work is allowed. The prohibition on scripting and
test writing concerns preparation rituals, not coding/testing that is itself
the selected task. Do not relabel packet engineering as substantive task work
to exclude it from the startup interval.

This supersedes any interpretation of the earlier W339626 proposal that permits
per-run programming or test development as normal preparation. It is a product
requirement, not a claim that current v12 meets it. Preserve the existing
decisions and failed/prepared evidence.

Current handler must incorporate this owner ruling into FINDING, current PLAN,
the normative DESIGN and acceptance before dependent implementation, coordinating
file ownership. Define the measured startup interval explicitly and show the
whole routine path; do not substitute script runtime for end-to-end elapsed
time or hide per-run preparation outside the measurement. Exact measurement
boundaries and supported-environment assumptions must be visible for owner
assessment rather than silently weakening the 60-second outcome.

This ruling does not select a live run, authorize takeover of another claim,
or grant direct host product implementation. W339626 currently has an unresolved
bootstrap/preparation mechanism reported in pass339805; resolve that concretely
without presenting another custom-script cycle as the delivered routine path.
