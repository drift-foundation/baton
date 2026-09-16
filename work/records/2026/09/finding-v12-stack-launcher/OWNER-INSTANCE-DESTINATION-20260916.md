# Owner ruling — explicit instance configuration and external destination

Work W183883. Recorded by baton.prompt, 2026-09-16T11:45Z.

## Confirmed conversation

Owner asks whether start should take the same JSON as bootstrap. Prompt proposed
one explicit instance JSON for start/status/monitor/stop, with paths derived from
that instance instead of manual environment exports; owner agrees and adds:
"ok we also need to isolate from the source/repo so bootstrapping ideally puts
it at a dest outside the repo".

## Current selected behavior

Prepare a persistent deployment at an explicitly named destination outside the
checkout, with a deployed runtime independent of subsequent source edits.
The intended command contract is:

```text
just setup
just bootstrap inputs.json /absolute/external/destination
just start /absolute/external/destination/instance.json
just status /absolute/external/destination/instance.json
just monitor /absolute/external/destination/instance.json
just stop /absolute/external/destination/instance.json
```

`inputs.json` supplies provisioning choices. Bootstrap emits the canonical
`instance.json` at the destination. That emitted file is the SAME operand for
every lifecycle command. Document this distinction plainly; no manual exports
or hidden global default should be required to select an instance.

The destination owns configuration, authority and runtime databases, process
records, logs, snapshots and the deployed runtime copy/package. Bootstrap must
not recursively copy checkout test scratch, dossiers, Git metadata or private
credential contents. Reuse explicit credential references and configured source
inputs. A nominated workload source remains an explicit workload input, separate
from importing the running scheduler's code out of this development checkout.

Current `stack.py` runs from DISTRIBUTION and adds checkout src/tools to child
PYTHONPATH. Storing only SQLite files elsewhere is therefore insufficient for
this selected isolation. Use a fixed installed runtime and an explicit compatible
Python environment, not an editable install or a symlink back to source. Reuse
the prepared venv where sound; if a per-destination runtime environment is needed,
make its preparation explicit and bounded. The source justfile may dispatch to
the installed entry point; changing checkout runtime modules after bootstrap
must not change the code an existing instance launches.

Two instances must have separate destination/authority/storage/process identity;
status/stop for one must address only that instance. Keep explicitly independent
writable workload/target paths. Do not silently turn distinct instance configs
into two managers on the same stores. Preserve existing corruption/identity
refusals. Repeat bootstrap preserves the deployed instance; changing code does
not implicitly upgrade an existing deployment. No automatic reset, migration,
live Job submission or live provider qualification is selected.

This explicitly supersedes the export-driven lifecycle interface, default shared
BATON_V12_STACK_ROOT selection as the normal UX, and checkout-bound execution in
the earlier W183883 implementation. Prior reviewed behavior/evidence remains
historical and reusable for unchanged boundaries. `just setup` stays the distinct
Python environment command; `just test-bootstrap` stays a focused verification
command. This is completion of the owner's usable side-by-side deployment
request; v11 remains the Work coordination authority.

## Execution and verification

Active implementer folds this ruling into PLAN and pins exact path ownership
before edits. Finish current tiny test-recipe addition without discarding its
evidence; keep remaining deployment work explicitly named. Use a focused slice
for instance selection and installed-runtime placement, with independent review.
Do not redesign scheduler/provider behavior or expand to a general installer.

Verify the changed paths with deterministic checks: bootstrap outside checkout;
launch/read/stop using the emitted JSON; source runtime edits do not affect the
installed instance; two separate instances cannot cross-control each other;
repeat/corrupt/mismatching instance behavior preserves state. Existing passing
owner suites need not be rerun merely for handoff. Any installed permissions
outside managed roots return as exact operator commands rather than managed
escalation requests. No Git mutation or v11 service modification.

## Superseded packaging choice — later owner confirmation 2026-09-16

Read OWNER-PYINSTALLER-20260916.md. PyInstaller one-folder now supplies Python
and dependencies in the deployed distribution. The earlier option to reuse a
shared/prepared runtime venv is superseded; setup prepares the build environment.
Owner also explicitly requires an independent deployed repository alongside
the distro and databases. External destination and common instance JSON remain.

## Later owner interface ruling — 2026-09-16

OWNER-STANDALONE-INTERFACE-20260916.md supersedes public lifecycle JSON arguments
and manual pre-clone steps as the normal user workflow: bootstrap INPUTS
DESTINATION creates the complete deployment, including repositories and its
own justfile; deployed just start/status/monitor/stop resolve local instance.json.
Git mutation remains owner-only through the finished operator-run command.
Earlier technical isolation requirements and evidence remain applicable.
