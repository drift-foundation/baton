"""Append this claim's implementer note to PROGRESS.md."""
from pathlib import Path

HERE = Path("/home/sl/src/baton/work/records/2026/09/"
            "finding-v12-worker-launch-version-mismatch")

NOTE = """

## Claim 199021 — baton.claude — the lifecycle ran, and stopped somewhere new

Three corrections, then the exercise, then a finding the exercise produced that
I did not go looking for.

### R2 — one manifest per Job, not one per role

The reviewer reproduced this against the real check rather than predicting it:
`_SingleWorker._matches` compares the Job's `input_digest` with its own
deployment's `manifest_digest`, and three role-specific seals give the Job one
value to name and two workers to refuse. The manifest is a fact about the
**Job's input**. Role independence lives where `stage_execution._independent`
actually looks for it — distinct participants, principals, launch roles and
private homes — and all five of those are asserted now. The equality check is
untouched and nothing is spoofed.

### R1 — a deployment limitation, recorded as one

`tools/single_worker.py:344` calls `credentials.resolved_delivery`
unconditionally and `_authorized_slots` refuses an empty list, so this deployed
composition cannot express the no-credential path the adapter supports. That is
written down as a limitation. The stopgap the reviewer authorized is a private
disposable source **this run writes**: one slot, mode 0600, owned by this uid,
holding text that says `NOT-A-CREDENTIAL ... authorizes nothing`. No credential
file from any real deployment was read or reused and no authentication coverage
is claimed. A case asserts the product still refuses an empty delivery — if it
ever stops, the stopgap is what should be deleted.

### R3 — measured identities, and failing closed

The all-zero base is now the target repository's own `refs/heads/main`, read out
of its refs. The principals are the Authority's answers. The record binding
digests retained `record-snapshot/` bytes. The adapter digest measures the
adapter file **and says what it does not prove** — the frozen distribution was
built before W198667 edited that file, so this is the checkout's adapter and not
the running one. The toolchain digest measures the fixture build context rather
than rehashing the image's own identity. The policies name this destination.

`main` returns non-zero the moment any required validator refuses, and
completeness is the conjunction of a named required set, so a validator that
never ran is as absent as one that refused. Six cases drive a refusal at each
validator and assert rc=1 plus `INCOMPLETE` on stderr.

**A defect of mine that this round's own rule caught.** The first run validated
its in-memory documents, answered `complete: true`, and then its own output loop
rewrote `task.json` indented — so the bytes on disk were not the ones any
validator had seen, and the installed bootstrap refused them: *"the configured
task document is 665 bytes and this profile's human-contract artifact declares
635."* A composition is only as validated as the bytes it leaves behind, so the
configuration is held **again after every file is written**, and that extra
validation is required whenever this writes anything.

### What the lifecycle actually reached

Capacity is configured on the disposable instance: routes, `b0657dfa-W1`,
grants, three workers, one Job — through the installed command. A repeated
bootstrap **with** `--destination` is refused ("nothing here upgrades a
deployment in place"); without it, it is the prepare-only repeat that
`bootstrap.DEFERRED` describes, and that is the one that works.

Then: submitted through `manager submit`, started through `start`, and **a
container ran**. The fixture worker answered the whole exchange — describe and
work, terminal `completed`/`answered` — wrote a `baton.worker-manifest/completion`
with three present outputs and measured content manifests, and exited 0. Intake
and custody completed: the output axis reached `sealed`.

### The finding

The stage then sat at `answering` and will never leave it.

Two `serve --once` reconciles, 72 seconds apart, each owed `conclude` and each
**deferred** it with the identical `refused/precondition`:

> attempt '…' output is sealed; custody is taken of a FROZEN result, and no
> other state is one

`end_implementation` documents that every one of its nine steps replays and that
a death between any two re-enters and finishes. Step five does not:
`intake._collectable` refuses an output that is already `sealed`, which is the
state its own success leaves behind. So an ending that got past intake and
failed after it can never be completed. Its own W124784 comment describes this
outcome exactly — *"the stage stays `answering` and asks again forever"* — for a
different cut point, which got a branch; this one has none.

And the operator surface shows only `answering`. The stage's receipts are
`admit` and `claim` and nothing else; `status` reports a healthy manager, a
fresh snapshot, one observed Job. The deferral exists solely in the reconcile
report, which the serving loop does not persist. That is the reported incident's
shape again: a runtime that finished, a manager that looks well, and nothing
that says why.

**What I did not establish:** which step after intake failed the first time. The
fixture's scripted agent writes `result_metadata: {}` for its
`git-change-proposal`, so it carries no `baton.git-proposal/1` claim and
publication could not have succeeded — a fixture gap and a plausible cause, not
a measured one. No product change is proposed on a guess.

### Preserved

The unresolved attempt and its container are retained: the ending never
authorized cleanup, and removing the container would destroy the evidence of an
unfinished attempt. The manager and publisher this claim started are stopped.
Every earlier packet, the accepted images and the stopped production instance
are untouched.

27 composer checks (0.303s, clean under `-W error::ResourceWarning`) and 33
verifier checks, all true, with a fail-closed probe on each.
"""

place = HERE / "PROGRESS.md"
place.write_text(place.read_text() + NOTE)
print(place, place.stat().st_size)
