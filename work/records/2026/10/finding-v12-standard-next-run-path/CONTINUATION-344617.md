# Partial implementation continuation — not integration acceptance

Author baton.codxpc claim344617; owner exception344614 remains the execution
selection. Read current TASK-344516, DESIGN OBS-0/0a and BOOTSTRAP-DECISION-344558.
This is concrete code progress, not another preparation/permission request.

Exact candidate: candidate-344617/ and CANDIDATE-344617.json SHA256
f3e5b57f1f708e99aede47c49a3b6190016bdfb3c9d4ab5b79de81d43d1bb16e.
Seven paths; baseline and source-copy provenance in BASELINE-344617.json.
Live development copy /tmp/baton-next-run-344617; no main checkout product edits.
The two product modules imported from historical dossier code are explicitly
identified in the manifest; this is not an asserted earlier integration. Original
dossier modules remain intact. Candidate is partial, not approved for import.

Implemented: product composer/supervisor modules; emitted enforced command;
verification limit shared by policy/submission; actual loaded controller and
shutdown helper binding; reusable input-only configuration capture/preparation;
exclusive run/slot reservations; input/runtime/source/manifest validation;
output/storage preflight before consumption; retained consumed uncertainty;
read-only status; supported release of never-consumed partial reservations with
old evidence and run identity preserved. No receipt reset or uncertain replay.

Test changes: new tests.tools.test_next_run (11 tests) cover real composition and
validation, two input tasks, failure recovery, stale/missing/linked/foreign input,
output parent creation, partial/collision behavior, retained uncertain dispatch,
helper binding and read-only status. Existing test_authoring_enforcement positive
binding fixture now supplies the required shutdown-helper hash and additionally
asserts its absence refuses. Existing negative controller cases remain.

Focused verification, PYTHONPATH naming only isolated python and src, bytecode
disabled, per-run timeout60s initially/90s combined:

1. 10 next-run tests, 2.810s: 7 fixture errors (Authority prefix mismatch), fixed.
2. 10 next-run tests, 4.818s: pass.
3. 44 combined tests, 7.808s: 1 positive fixture missing new helper binding, fixed.
4. 44 combined tests, 7.747s: pass, no skips reported.

Measured unittest total23.183s; process/tool overhead and editing elapsed unknown.
No provider/engine/Git mutation. Launcher tests replace image check and controller
call; existing guard tests use fake engine with real stores. This does NOT prove
substantive agent work, installed-root security or <=60-second end-to-end startup.
No timing target was weakened into an assertion over mocked dispatch.

## Exact remaining implementation and acceptance

The current configuration installer assumes preprovisioned slots. It does NOT
implement required one-time privileged account/credential/narrow-admission setup,
nor automatic public-API bootstrap of independently bound Work/store slots.
next_run.install captures configuration; it is not the trusted managed broker.
Its operator-owned Python/configuration must not receive sudo admission. An
untrusted caller able to change those bytes is outside this draft's boundary.
This is the concrete remaining install-once gap, not a new owner permission gate.

Continue the approved cohesive outcome by adding the trusted one-time installer
and routine isolated allocation/launch path, reusing bootstrap and accepted
custody code as appropriate. Preserve immutable source/input binding, no arbitrary
privileged execution, isolation and exclusive once-only effects. The current slot
reservation layer provides evidence/state transitions, not kernel isolation.
Consumed slots are intentionally held rather than recycled; supported safe
continuation must establish cessation/fencing and a fresh allocation without
clearing prior receipts. Do not turn manual operator setup or this finite pool
into accepted routine behavior.

Then exercise two complete input-only tasks and failed-start recovery after one
installation, at deterministic provider/privilege/engine boundaries with the real
bootstrap/controller/worker/result owners. Measure from input receipt to actual
substantive simulated work and label it simulated. Full acceptance remains owed.
Review this partial candidate and continue directly under owner344614; no generic
owner-return or renewed preparation permission is needed. Exception expires only
at independent candidate acceptance before integration/deployment. Do not accept
this partial snapshot as that event. No arm/start of old v3 or host install.

Historical accounting retained: parent author prep0.954673s; reviewer0.031483s
internal/0.2221s outer; failed starts0.2174s and0.262026465s process/0.417s call;
input-binding interval0.000245576s. Nested clocks not added. W339972/W343989
spending remains in their dossiers. Initial broad source-copy enumeration refused
a historical scratch symlink before importing it; baseline capture was narrowed
to enumerated src/tools/tests/docs, with no source edits before capture. No
unread required policy/dossier file is being bypassed.
