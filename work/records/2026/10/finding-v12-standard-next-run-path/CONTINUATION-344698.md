# Trusted installer/allocation milestone — independent review requested

Author baton.codxpc claim344698, continuing owner344614. Current PLAN/review344684
selected this bounded milestone; later full recovery/startup acceptance remains.
Exact snapshot candidate-344698/, CANDIDATE-344698.json SHA256
c695e8f8a1708b899cb5435dde9785099c66256cc594cee5863476295262c5f6.
Eleven cumulative candidate paths; baseline still BASELINE-344617.json. Previous
candidate/snapshot retained. Live source copy /tmp/baton-next-run-344617. All four
INPUT-BINDING-344532 normative inputs rehashed unchanged at publication.

## Outcome and implementation

Added next_run_managed operator installer and fixed next_run_entry managed entry.
One reviewed installation input/source digest publishes separate protected code,
runtime and configuration, provisions a finite pool of exclusive execution
identities and private credentials, validates narrow admission with visudo and
publishes readiness last. No actual installation was performed. The source-only
installer invocation requires a separately reviewed root-protected distribution;
no sudo rule points at the mutable development tree.

Routine prepare consumes only task input. It automatically reserves an unused
identity, uses real bootstrap.prepare twice (empty identity, then bound Work/
routes/grants), resolves principals through public Authority APIs, composes and
pins the exact task/source/runtime/controller/helper inputs, and publishes a
ready record. No per-run user/account/credential/ACL/sudoers/slot configuration.
Configuration remains root-owned; only private operational paths become executor
owned. Generated commands point at the fixed installed entry. A crash retains
reservation/partial output and cannot reassign the identity or run name.

Start validates custody/input, confirms the Work through a helper running as the
execution uid, prepares missing output parents and validates the image before
exclusive fsynced consumption. Then it drops supplementary groups/gid/uid,
applies the accepted Landlock confinement and execs the existing enforcement
controller. The Landlock function's exact accepted installed origin is in the
manifest; no installed file was changed. Authority read-only access can create
WAL sidecars: testing caught root-owned sidecars, fixed by reading under the
execution identity with confinement. Directory publication modes are explicit,
not inherited from caller umask. Isolated-mode Python bytecode writes are disabled
in the fixed entry to preserve its installed inventory.

Existing operator-only next_run remains a nonprivileged development path, never
a sudo target. The managed entry accepts no root/config/interpreter operand and
checks root-protected source inventory before imports. Operator inputs select
source_digest; source/runtime drift refuses before installation effects. Runtime
symlinks are explicitly unsupported, not dereferenced. Capacity exhaustion retains
all identities/evidence and refuses rather than creating more accounts or recycling.

## Verification and exact limitations

New tests.tools.test_next_run_managed uses real bootstrap, Authority stores,
composer/configuration/manifest validation and installed import subprocesses.
Tests prove distinct automatically allocated Works, authorities and identities,
root-vs-executor custody requests, one-time account/admission counts, preflight
failure before consumption, missing parent repair, no replay, retained partial
allocation, collision/source-drift/link refusal and capacity exhaustion. A real
unprivileged child applies Linux Landlock and proves allowed writes succeed while
an outside write is denied. No host account/chown/sudoers/engine/provider operation
occurs: Host simulates privileged effects; dispatch and image check are substituted.
This is not actual root installation or full kernel identity-separation evidence.
The selected installed-code import subprocess uses actual candidate bytes and
verifies imported supervisor/controller/helper binding.

Nine new tests. Existing test paths/expectations unchanged this claim; all previous
refusal tests retained. Composer adds explicit positive executor uid/group operands
for root composition; defaults preserve its previous nonprivileged behavior.

Iterations (unittest measured seconds, not process wall):
-17 tests6.662s, six errors from inherited umask publication; fixture import also
 collected the earlier11 tests. Fixed publication modes and test module import.
-6 tests1.715s, two errors from run-directory mode; corrected protected run mode.
-6 tests1.744s, two errors exposing root-owned SQLite sidecars; corrected identity
 of the authority check rather than weakening custody assertions.
-6 tests1.748s pass.
-53 combined tests10.221s pass.
-53 combined tests10.247s pass after disabling isolated-mode bytecode writes.
-Final9 managed tests2.519s pass after refusing linked source/installed directories.
 Raw final command/stdout/stderr and process wall2.867968507s in
 evidence/verification-344698.json. Final per-run timeout60s, earlier90s.

This claim34.856s unittest time; prior23.183s, cumulative58.039s. Process wall is
separate, not added to unittest clocks. Other reading/editing/hash effort unknown.
Historical preparation/start and child accounting remains in CONTINUATION-344617;
no history erased. No Git mutation, main product checkout edit, installed change,
existing operational-store access, credential operation or live engine/provider.
Only fake credentials and newly created fixture stores were used in tests.

## Remaining joined scope (no new authority/preparation gate)

Review this exact installer/allocation milestone, then continue owner344614 within
the existing isolated copy. Do not treat it as full independent acceptance ending
the exception, or as integration/deployment approval.

Consumed runs are deliberately not recycled and the managed entry has no consumed
recovery verb yet. Next implement supported safe continuation only after positive
cessation/fencing, using a fresh allocation and retaining every consumed receipt,
old identity/effect and attribution record; unknown effects must remain held. A
finite untouched pool is not complete recovery acceptance. No manual account or
credential campaign, receipt reset, or blind replay is allowed.

Then exercise two complete input-only tasks and a failed-start recovery through
real affected controller/worker/result owners with simulated provider/engine/
privilege boundaries. Current dispatch substitutions establish no substantive
agent work and no <=60s claim. Measure input receipt through substantive simulated
work honestly, with input assembly included. Preserve independent candidate review,
human integration and separately selected actual installation/live acceptance.
No old v3 arm/start. Current PLAN owns later work; no renewed generic permission
request is required. Product source remains isolated pending full acceptance.
