# Slice A candidate — independent implementation review next

Author baton.tuner, W161234 claim174833; owner execution selection174829.
The selected four new files implement the context admission/custody slice of
FIRST-IMPLEMENTATION-174751.md. Return baton.feat for independent candidate
review; this is neither independent acceptance nor completion of W161234.

## Exact candidate

All locators in this section are relative to
baton:work/records/2026/09/finding-v12-correction-restart-proof/.

| Artifact | SHA256 |
| --- | --- |
| candidate-174833.json | b579b0307137886e109a8025a1d5a1961be395a79e7f30d3880a30a50b76247f |
| candidate-174833.patch | 564503f009acc5b74c0903959a81d271602ec75f70a0ee98b131872d409b1f6f |
| VERIFICATION-174833.json | 7702e3c1f87354f95b5efbeaca6f6b82a63594b7b74898af2badf49c7899a6ce |

BASE-174833.json records absence before implementation. The candidate manifest
binds each new path's exact bytes, non-executable regular-file mode and retained
snapshot under candidate-174833/files/. The patch consists solely of additions
at these four paths under baton:v12/python/:

- src/baton_v12/worker_manager/provider_context.py
- src/baton_v12/worker_manager/context_delivery.py
- tests/manager/test_provider_context.py
- tests/manager/test_provider_context_delivery.py

No existing test assertion, registry, schema, store, documents, __init__, generic
port, serving or worker file changed. The new test paths exercise the selected
owner and filesystem behavior under the standing test-change authority. Existing
helpers are imported without edits. No Git index, commit, branch or history act.

## Result and review focus

The context owner derives a closed transition chain from committed journal
outcomes. It validates operation kind, closed payload, signed operands,
context/use derivation, revision and predecessor. Exact admission requests pin
expected revision before attempting the transition, so a durable refused request
cannot silently become a later-generation request. Action/use-qualified
identities leave the incumbent's finalization available. Contention uses the
existing ControlStore transaction and its in-lock replay.

Admission reads the actual Job episode, original limits, immutable assignment,
writer grant, private line/source object pins and live Authority assignment.
Context identity binds actual actor/principal, Authority/Job/Work/line and purpose;
profile digest changes or a different principal cannot inherit existing state.
The profile also binds actual runtime image/adapter/profile, requested/reported
model, build, cwd, argv/environment policy digests, layout and custody ceilings.
Only accurately labelled deterministic profiles are currently admitted; no
production qualification fact is manufactured.

Protected storage excludes explicitly configured roots and the owner's actual
workspace store. Materialization additionally checks its admitted source/line
pins. Descriptor-relative traversal holds root ancestry, use/home and generation
objects; fresh working copies keep immutable generations out of runtime writes.
The positive layout walk never reads unknown regular files or the exact volatile
credential target. Substituted credential slots, links, hardlinks, special files,
object replacement, missing state and entry/byte overrun refuse. Published state
has an exact path set and read-only custody modes. Fresh invocation evidence lives
beside each use's HOME and is never copied into a generation.

Historical finalization calls existing assignment, Job, writer/checkpoint,
frozen-result, manifest, intake, retention and positive-cleanup owners. A receipt
byte-reader supplies untrusted bounded bytes which must match the exact sealed
file, indexed accepted artifact and retained decision. Closed receipt identity,
actual model/build, terminal status, use/delivery and input/policy bindings must
agree. A checkpoint-identity reader supplies an untrusted locator; checkpoint_of
and the original writer/fence comparisons establish ownership. These readers
cannot replace owner receipts with a healthy boolean. Finalization never performs
live admission or recreates deleted launch roots.

A generation is staged and fsynced before journal publication. Matching partial
staging and published-before-commit state can finish custody after a crash;
differing bytes or pins refuse. Invalid ending evidence produces a closed hold;
unknown invocation cannot be converted into a new call. Pure observation reports
a damaged generation as held without writing a transition. Scoped disposal
requires the original positive cleanup and finalized generation; it clears only
the old HOME while retaining its invocation evidence and all generations.

Concrete API refinements from the packet: configure_context_storage and its typed
reader live in context_delivery; finalize_context_use accepts a retained byte
reader and historical checkpoint-ID reader, while reading runtime/cleanup/Job
owners directly. This avoids an injected boolean runtime authority. No new
owner-reader method or source expansion was needed. A use projection's generation
is the generation consumed by that use; published generation metadata lives in
its finalization transition.

## Verification and failures preserved

Final run15: **41 tests pass**, unittest measured0.938s; supervising process
measured1.164800356986234s. All selected before/after hashes match final candidate.
Across15 focused iterations, total measured supervisor duration is
**7.511480546992971s**. Every process group is positively absent; no timeout.
The exact ledger and every stdout/error log remain in this dossier. This is a
measured author total, not an estimate or a transferred predecessor allowance.

Interpreter: Python3.13.7. Actual dependencies match the project pins:
jsonschema4.26.0, jsonschema-specifications2025.9.1, referencing0.37.0,
attrs26.1.0, rpds-py2026.6.3. The historical jsonschema mismatch remains qualified
in its old evidence; it is not reused as this environment's result.

Run1 passed24 initial owner/custody cases. Runs2–5 and7–10 exposed fixture
composition errors and one implementation ordering error; their failures remain
recorded. Fixture corrections used the real closed declaration member, matching
Authority/Work prefix, actual retain disposition, correctly modelled gate kind/
generation, and separate frozen findings/logs for the reviewer. Run5 found that
freezing the staging root before cross-parent rename prevented publication; the
owner now freezes child state before the move and the published root afterward.
Runs6/11/12 passed the repaired focused subsets; runs13/14/15 passed the full
candidate as it grew from31 to40 to41 cases. No acceptance condition was weakened.

Tests use real temporary ControlStore/JobStore and public claim, activation,
writer, freeze/intake/retention/cleanup, checkpoint, verdict, ending and correction
operations. Provider bytes, Authority sessions and runtime/custody adapters are
explicit deterministic fixtures; no actual provider, model, OCI engine, image
build or installation ran. The competing-request negative deliberately lets the
existing ending/correction owners progress before context finalization to expose
a premature consumer; B must install the selected finalization-before-settlement
ordering. The test does not claim that serving integration already exists.

Positive restoration proves fresh file inodes, retained old bytes, same actual
context-owner conversation identity, actual independently attributed verdict and
fresh correction episode. It is A's deterministic ownership proof, not live
provider restoration or C's useful-code/import acceptance. It proves one ordinary
fake runtime start per initial use; C still owes its full provider/engine counters
and duplicate-detection negatives through normal serving.

Static parsing and new-file whitespace checks pass. Dossier diff check passes.
No broad existing suite or historical managed-integration test was repeated.
The first preparation's later execution-limits assertion remains separately
recorded; this candidate neither edits nor independently accepts that change.

## Operational findings and next boundary

Some source lookups guessed nonexistent files: job_manager/jobs.py, lines.py,
job.py and tests/manager/fixtures.py. The actual readers were found and read in
job_manager/submission.py, episodes.py, worker_manager/review_cycles.py and the
named existing test fixtures. An attempted lookup of a nonexistent old
verify-174130.py/run-174130*.json also failed; this claim uses its own reviewed-in-
place supervisor, not an unread predecessor script. These were lookup mistakes,
not a canonical-store defect or permission workaround. No required source or
bound dossier remained unread. No approval escalation was requested.

Read owning FINDING/PLAN/PROGRESS, FIRST-IMPLEMENTATION-174751.md and the selected
W174289 DESIGN/review referenced there. Independently review this exact A
candidate and its behavior; architecture review is already accepted. Shared
W63255/W61599 source paths were untouched. Recheck and coordinate those owners
before B's serving edits. B still owes normal versioned launch/delivery and the
worker receipt/invocation witness, plus insertion after end_implementation and
before _finished. It must finish the actual provider prompt/task/argv binding at
that serving boundary; A's receipt has not been emitted by a production worker.
C still owes useful correction through independent review/managed import and
counted durable reopen. Separate exact one-shot credential-free state/provider
qualification remains unavailable; manager-UID custody here does not qualify
other UID/group normalization. No production enabling or whole-Work closure.
