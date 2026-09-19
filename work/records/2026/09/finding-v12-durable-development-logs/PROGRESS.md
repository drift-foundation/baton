# Progress

Implementer-owned. Appended per claim; no prior author's account is rewritten.

## Claim 198698 — baton.claude — the startup diagnostics; capture NOT done

### Ownership, enumerated before editing, as the owner constraint requires

The constraint is "Claude cannot override files of Codex" and "never overwrite
newer bytes with an earlier candidate", so I established the actual state
rather than assuming it:

- **W194457** (shared workspace identity — `workspaces.py`, `oci.py`,
  `custody.py`, `review_cycles.py`, `single_worker.py` and five test paths) is
  **closed, outcome satisfying**. Its candidate is accepted, so those paths are
  no longer under review.
- **W197661** (worker launch version mismatch) is queued at `baton.bug` with
  codex. Its candidate paths are `baton_worker.py`, `test_worker_entry.py`,
  `test_exchange.py`, `test_worker_container.py` and
  `test_execution_limits.py`, and its remaining scope — the disposable-instance
  exercise — is dossier-only and edits no product source.
- `baton.home` shows **one** active Work in the whole team: this one.

**So I edited neither of those candidates.** The one place where that mattered
is recorded below, because it changed the design.

### What I implemented

`v12/worker/integration_entry.py` — **every refusal now says why.** This is
item 5 of the FINDING's required outcome and the gap the FINDING names
directly: *"W197661 exposed a second gap: an integration startup refusal emits
no diagnostic. Capturing output alone cannot recover a diagnostic that was
never emitted."* W197661's smoke measured it at the artefact — the integration
candidate given a launch generation it cannot read exits `2` with an **empty**
stderr while the provider candidate under the identical delivery exits `3` with
a bounded sentence. It does not hang; it just says nothing.

Five silent returns now write one bounded line each: an unreadable launch, an
unreadable assignment (naming the root it looked in), an unreadable result
namespace, an assignment this build cannot own, and a composed result it could
not publish.

**The three statuses are unchanged, deliberately.** They are this entry's
accepted contract with the manager, and a diagnostic is not a reason to move a
status a manager settles on. `_startup_refusal` answers `baton_worker`'s own
`3` and this entry **discards it**; a case pins that.

**The sanitizing rule has one owner and I did not copy it.** The line goes
through `baton_worker._startup_refusal`, which bounds it to one line of
printable ASCII — it quotes documents this runtime has just refused to trust.
Calling that function is a *use* of `baton_worker.py`, not an edit of it, which
matters because that file is W197661's candidate sitting in independent review.
A `WorkerFault` is built as the carrier for the sentence; nothing writes a
frame, a receipt or a terminal, and a case asserts a refusal leaves its
namespace byte-identical.

Six focused cases in `tests/manager/test_integration_worker.py`. A reversal
probe in a removed scratch copy silenced all five sites and reproduced the
measured behaviour exactly: **status 2, stderr `''`**.

### What I did NOT implement, and the design reason

The capture half — items 1 to 4 of the required outcome — is **not done**.
Enumerating the worker's writable surfaces settled why it cannot be done
worker-side alone:

| surface | why it cannot hold durable logs |
| --- | --- |
| `/output` (workspace) | the result surface; declared outputs are validated and frozen. Logs there stop being distinct from results, which the FINDING forbids. |
| `/run/baton/exchange/events` | protocol documents; the FINDING requires logs kept distinct from protocol. |
| `/tmp`, `/dev/shm` | tmpfs, 64 MiB and 16 MiB. Gone when the container ends, so nothing survives "termination and restart". |

There is **no durable, manager-owned, non-result, non-protocol writable mount**
today. "Create stable manager-owned attempt log locations before worker
startup" therefore needs a new delivery and a new mount in the manager —
`oci.py` plus the attempt lifecycle that creates the host directory — and then
the tee in `claude_agent.py`, and only then the locator and read/follow
surface. That is a coherent piece of work and it is not a piece I could land
honestly in what remained of this claim.

I did not start it and hand over something half-built. Four reviews of W197661
were spent correcting exactly that shape in my own evidence, and here the
subject is a capture path whose whole purpose is to be trustworthy when
something else has gone wrong.

### Verification

- `EveryIntegrationRefusalSAYSWHY` — 6 checks, 0.001 s, clean under
  `-W error::ResourceWarning`.
- The adjacent set — `tests.manager.test_integration_worker`,
  `tests.tools.test_integration_worker`, `tests.manager.test_integration_image`
  — **135 checks, 20.342 s unittest / 20.609 s wall, OK.** The existing refusal
  cases now print their diagnostics during the run, which is the evidence the
  owner asked for rather than noise to suppress.
- One reversal probe, in a scratch copy removed afterwards.

No live model, no image build, no container started, no production touch. About
41 seconds measured this claim.

### One honest note

My first version of `test_no_frame_no_receipt_and_no_result_is_written_by_a_refusal`
listed the namespace *before* the fixture wrote its own launch document into it
— all five fixed names are one disposable directory here — so it counted the
fixture's delivery as something the refusal wrote. I corrected the fixture, not
the assertion. That is the fourth claim running where a check caught my own
fixture rather than the thing under test.

### State

Returned for independent review with the capture half's exact remaining scope
in `EVIDENCE-198698.json`. Nothing in W197661's or W194457's candidates was
edited; the stopped production instance and its unresolved attempt are
untouched.

## Claim 198803 — baton.claude — the delivery and its mount

Ownership went into PLAN before any edit, as the owner constraint requires.
W197661 is queued at `baton.bug` and its candidate includes `baton_worker.py`,
which I did not touch; W194457 is closed and this builds on its accepted bytes
rather than restoring anything older.

### What I built

**`attempt_logs.py`** — the manager-owned log room, created before the runtime
starts, at its own fixed target `/run/baton/logs`. Six named streams, a native
corner for the provider's own session files, and a capture vocabulary whose
whole job is that **missing is not empty**: `absent`, `empty`, `captured`,
`truncated`, `partial`, `failed`. The writer's own word outranks the file for
the middle three, because a file cannot tell you it is a prefix.

It is a third namespace on purpose. An attempt already has a result surface
(`/output`, validated and frozen) and a protocol surface (the exchange, read as
receipts and terminals). A log under either would be read as the wrong kind of
thing by whatever owns that surface — that is the reason the module exists
rather than a preference.

`adopt` re-enters without destroying anything, which is what makes "partial
evidence survives termination and restart" true rather than aspirational. And
`LOG_DIR` is `workspaces.WORKSPACE_DIR` — the constant the establishing
function actually chmods to — so `adopt` cannot start refusing rooms this
module itself made.

**The mount**, `oci._log_mounts`, beside the exchange's and the credentials':
exactly one bind, writable, at the constant target, a real directory, refused
if any earlier family already holds or contains it.

**31 new checks** across the two suites, and 507 pass in the adjacent set.

### What the test suite caught, and why I changed my code instead

`test_dependencies` lists `offset` among the operands that are *bookkeeping by
nature*, beside `cursor` and `index`. My reader took `offset=`. That is the
suite catching a real API boundary, not a registry gap — so I renamed the
operand to `from_byte`, the way this package already spells `from_instant`,
rather than pushing the name past the rule.

Measured, not asserted: the registry had **57** failures before this claim and
has **57** after. Zero added. I established that with a scratch copy of `src/`
with this claim's manager changes reverted.

**One measurement I withdrew.** An earlier baseline comparison ran from the
wrong directory after a cwd reset and reported "0 pre-claim failures". That was
an artifact, not a measurement. I checked the test file was undamaged and
re-measured properly. The 57/57 above are the real numbers.

### What is left

The tee itself — provider stdout parsed *and* retained byte-identically, the
three streams off `DEVNULL`, native output retained — plus the wrapper's own
earliest output and the lifecycle wiring in `single_worker.py`. The wrapper half
needs `baton_worker.py`, which is W197661's candidate and wants the serial
coordination PLAN records.

I stopped at a boundary rather than leaving a half-written tee: the delivery and
its mount are the bricks everything else stands on, and a tee with nowhere
durable to write is not capture. About 62 seconds measured.

## Claim 198899 — baton.claude — R1 and R2 were defects in what I shipped

Both are corrected. R3 is not, and I say so plainly at the end.

### R1 — the capture state did not survive being looked at

Three shapes of the same mistake, all confirmed by the reviewer's probes and
all mine:

- A writer that declared `failed` with **no file** got back `absent` — "no log
  was created". A failure reported as a run that had nothing to say is exactly
  the sentence the required outcome forbids.
- A `stat` that raised `PermissionError` also became `absent`. "I could not
  ask" is not "there is nothing there".
- A stream declared `partial` in `locators` came back from `read` as
  `captured`, **"the whole stream was retained"** — because `read` had no way
  to be told anything and there was no persisted status at all.

And my own `test_locators_name_every_stream_with_its_honest_state` asserted the
first of those, so a green suite was endorsing the defect. The reviewer caught
a test that certified a bug.

The correction: the writer's word is **written down**, in the room, beside the
streams it is about, so it survives a restart and reaches every reader.
`failed` outranks an absent file. `absent` and `inaccessible` are separate
answers. And **bytes alone are never completeness** — a stream with content and
no declaration is `live`, and only a writer's `finished` reaches `captured`.
`at_end` is named that rather than `eof` for the same reason: a reader that has
caught up with a stream still being written is at its end for this instant only.

### R2 — the reader could leave the attempt's own room

A `worker.stdout.log` symlink inside one attempt, pointing at a sibling file,
was followed and returned as **this** attempt's captured output. `capture_state`
used a following `stat`, `read` an ordinary `open`, and the native listing
followed its path too.

Now the room is opened once, no-follow, and every entry is named relative to
that descriptor. A symlink or non-regular entry is `inaccessible` with the
reason; the open is `O_NONBLOCK` and the **descriptor** is checked with
`fstat`, because a path checked before an ordinary open is a different object
from the one that gets opened, and a FIFO must not wedge a reader that promised
to be bounded.

One judgement while fixing it: a room this manager cannot open at all is
**reported**, not raised. `locators` is the operator's whole picture, and one
unreadable room must not take the other five streams' answers away with it.

I also withdraw the description of `adopt` as a complete descriptor-relative
proof of the room's identity. It checks the final directory's mode and accepts
an existing native corner through a following `isdir`; that is less than the
sentence claimed.

### What the dependency suite caught again

`record_capture(..., why=)` — `why` is not a declared operand. Rather than
register a second spelling, I used `reason`, which this package already uses
for a caller-supplied note. Measured: 57 before, 58 with `why`, 57 with
`reason`. Zero added.

### R3 — not done, and not dressed up

No lifecycle creates or passes the delivery, no tee fills it, no native
retention is connected, and there is no operator **command** — Python functions
are not the command the outcome asks for. The reviewer is right that a coherent
internal boundary is not completion, and I am not going to call it one. What
this claim delivers is two correctness fixes to shipped code plus the seven new
cases that prove them; the end-to-end capture remains the outstanding work.

29 checks in the delivery suite, 514 across the adjacent set, all clean under
`-W error::ResourceWarning`. About 55 seconds measured.

## Claim 198977 — baton.claude — the sidecar was the same escape, one level over

Four findings. Three were defects I introduced *while fixing the previous
ones*, which is worth saying plainly: I confined the streams and left the
metadata about them unconfined.

### R1 — and one of these was a write outside the room

`_status` read `capture-status.json` with an ordinary `open`, so a symlink
there supplied **another attempt's word** and a prefix log was reported as
`captured` on somebody else's say-so. Worse, `record_capture` opened
`.staging` with an ordinary truncating `open`: a symlink at that name made it
**overwrite the file it pointed at**. That is an actual write outside the
attempt's room, and no acceptance of raw development content authorizes it.

Metadata now obeys the rules the streams already did: opened relative to the
held room, no-follow, regular-file, bounded read; staging created
`O_CREAT|O_EXCL|O_NOFOLLOW` and the replace anchored to that descriptor at both
ends; and on any failure the staging entry is removed and the stream's own log
is left untouched.

### R2 — atomic replacement is not an atomic update

`record_capture` loaded one shared document, changed one entry and replaced the
whole thing. The reviewer's probe let a second writer record `stderr=failed`
while the first was mid-update, and **the failure vanished**. Replacing a
document atomically says nothing about updating an entry in it atomically.

The correction is structural rather than a lock: **one sidecar per stream**. No
two writers touch one file, because a stream is written by the one thing that
writes that stream, and the staging name is per-stream too so overlapping
writes cannot collide on it. Two threads declaring `stdout=partial` and
`stderr=failed` concurrently now both survive, and both survive a restart.

### R3 — corrupt metadata must not take down the view

A valid JSON object whose entry was the integer `1` crashed `locators` with a
`TypeError` — the exact opposite of the readable operator picture this exists
for. Every member is checked now: shape, declared state, bounded reason,
bounded document. Anything else is `corrupt` — **reported, never raised, and
never silently turned into an assertion of completeness** — and the raw log
stays readable, which is what an operator came for. Nine malformed shapes are
covered, including a special file and a non-UTF-8 payload.

Every answer now carries a `declaration` field saying whether its metadata was
readable, so "we have no writer's word" and "the writer said nothing" are
distinguishable at a glance.

### One expectation I got wrong on the way

I wrote a case asserting that an oversized reason is *refused*. It is
truncated, the way every other bounded diagnostic in this package is, with
`MAX_STATUS` as the document backstop. That was my expectation rather than the
contract, and I corrected the case rather than the code. A second fixture of
mine declared `partial` for a stream with no file and expected `partial` back;
`partial` says *what is here* is a prefix, so with nothing there `absent` is
the honest answer and the fixture now writes the log first.

### R4 — still not done

No lifecycle passes the delivery, no tee fills it, no native retention, no
operator command. The reviewer is right that this must be integrated so the
concurrency, failure and shutdown contract can be reviewed together rather than
as primitives. That is the outstanding work and I am not calling this claim
more than it is: three confinement and honesty defects in code I shipped,
corrected, with nine new cases proving them.

38 checks in the delivery suite, 387 across the adjacent set, clean under
`-W error::ResourceWarning`; dependency baseline unchanged at 57. About 50
seconds measured.


## Claim 199021 — baton.claude — the same escape, a third time, in a third place

Three confirmed defects, all in code I shipped, and R1 is worth naming plainly:
**this is the third appearance of one mistake.** I confined the streams. Then I
confined the metadata about them. This time it was the public reader operands.

### R1 — the allowlist is the confinement, and almost nothing called it

`place` held the six declared stream names and nothing else went through it, so
`read(delivery, "../other")` returned a sibling's log from outside the attempt's
room — the reviewer reproduced that rather than predicting it — and
`capture_state`, `follow` and `status_name` did the same.

The reason I kept missing it is worth writing down: I had been treating
descriptor-relative no-follow opens as the confinement. They are not.
`O_NOFOLLOW` governs the final component only and `dir_fd` resolves `..`
exactly as any path does, so a parent-relative or absolute operand walks
straight out of a held room while every descriptor rule is satisfied. The
allowlist is what confines this package, and an allowlist one entry point
bypasses is not one.

So it is one `named()` function, applied at every public entry and at the two
internals that join a suffix, before a descriptor is opened or a room is held.
Eight cases: parent-relative, absolute, unknown, empty, non-text, and the
ordinary named streams still working.

### R2 — cleanup deleted the entry that proved it was not ours

The exclusive create is what refuses a staging name somebody else holds, and
the handler then unlinked that name anyway — on the failure of the very call
that establishes it is not this call's to touch. Creation ownership is tracked
now and nothing is removed that this call did not make.

The second half was the reviewer's too: the staging identity was `os.getpid()`,
which every thread in a process shares, and the tee this delivery exists for is
two threads draining two streams at once. It is per call now.

That fix had a consequence for the tests: an unguessable name cannot be
collided with from outside, so the collision cases patch the module's own
`_STAGING` seam rather than guessing. That is testing the rule the module
states, not reaching around it.

### R3 — a short write is not a successful declaration

One `os.write`, its count ignored. A writer that accepted four bytes published
a truncated sidecar — read back as `corrupt` with the stream reported `absent`
— and `record_capture` returned the full declaration as though it had been
recorded. A failure's own evidence lost while its writer was told it was kept.

Every byte is written before the replace; no progress is a failure rather than
a reason to ask forever; and nothing is published unless it was written whole,
so a declaration already recorded survives a failed attempt to replace it.

**Re-running the reviewer's own three probes:** the traversal read is refused,
the preexisting staging entry survives, and the short write no longer refuses —
it *succeeds correctly*, which is the right outcome. A writer that accepts four
bytes at a time is a legitimate writer; the defect was ignoring the count.

### R4 — still not done, and no longer a question

No lifecycle passes the delivery, no tee fills it, no native retention, no
operator command. What changed is that R4 is no longer an open design question:
PLAN now records both answers with enumerated paths — the host room lives at
`<launch_home>/logs/<attempt>/` and rides with the `LaunchDelivery` exactly as
the exchange does (measured against three candidates, two of which the tree
rules out in its own words), and the declaration format gets one owner that
travels into the image the way `source_profiles` does, because the worker may
not import the manager.

I did not start the wiring. Creating a log room on every launch changes what
four adjacent suites observe on disk and the shared writer means both image
recipes change and both images rebuild. A half-wired lifecycle with those
suites unverified would be worse than an unwired one with the decision written
down. The reviewer asked for a complete candidate or an operational refusal and
this is neither, which I am not going to dress up as either.

59 checks in the delivery suite, up from 38; 474 across the adjacent set, clean
under `-W error::ResourceWarning`; dependency baseline unchanged at 57.


## Claim 199285 — baton.claude — R4, wired end to end, and a container found a defect

The paths went into PLAN before any edit, with the two placeholders replaced by
exact names, and the provenance correction went into FINDING: canonical
work-events calls the previous episode **claim199159**, not 199021. The
mislabelled file keeps its name and bytes as history. So does its claim that the
per-call staging identity is "unguessable" — it is not; pid plus a counter is
per-call *naming*, and `O_EXCL` plus ownership tracking is what makes the act
safe. Corrected by appending.

### One format, two writers

`baton_v12/attempt_log_format.py` now owns the allowlist, the declarable states,
their prose, the sidecar name, the write and the validated read. It imports
nothing from `baton_v12`, so the manager reaches it as
`baton_v12.attempt_log_format` and the image carries the same bytes as a
top-level `attempt_log_format` — exactly how `source_profiles` travels, and for
the same reason: a worker that can import the manager is one bug away from
holding the manager's capabilities. `attempt_logs` delegates and keeps the
manager's own vocabulary; no rule moved, one owner replaced two.

### The lifecycle

The room lives at `<launch_home>/logs/<attempt>/` and rides on
`LaunchDelivery.logs` the way the exchange does. It is a **sibling** of the
attempt launch roots, which is what lets `launch.discard` tear a launch down and
leave the evidence — the required outcome, with a case proving the launch root
is gone and the log still readable. `adopt` recovers it on restart and a second
incarnation appends. `oci` passes `logs_delivered` at the one `run_vector` call
site, so `_log_mounts` finally has a composer.

### The two ends that were discarding

`baton_worker._WorkerCapture` tees `sys.stderr` from before the launch document
is read — before anything that can refuse it, which is exactly where the
reported incident happened. The real stream is written first, always. Stdout is
**not** teed: on the framed transport it is the protocol channel and its bytes
are exact.

`claude_agent` keeps all four streams. `provider.stdout` is retained
byte-identically beside being parsed and the returned record is unchanged;
`provider.stderr` and both verification streams go to the log's own descriptor,
so this process never holds those bytes — which preserves the exact property
W39357's discard was protecting. The owner's supersession is recorded at the
site, not in a commit message.

### What the container found that no unit case did

`write_declaration` created the sidecar `0600`. The worker writes it as the
image's fixed uid and the manager reads it as its own, sharing only the
workspace group — so the declaration was **one only its writer could see**, and
the manager reported the stream `live` with `declaration: corrupt`. A writer's
word lost to a file mode. It is `0640` now: group-readable like the log it
describes, never world-readable and never group-writable.

The smoke builds this Work's **own** fixture context — W197661's is retained
untouched, and no accepted image is rebuilt or re-attributed — starts one real
container under `oci.RESTRICTIONS`, and proves the refusal's own sentence is on
disk in the manager's room after the container is gone.

### Found in passing, and not claimed as mine

`claude_agent.work` faulted with a `TypeError` when `declared` was not a list
instead of refusing — at a function this claim does not touch or reach, with an
existing test asserting the refusal. Guarded.

### One fixture mistake of mine

The image-layout helper first evicted `claude_agent` and `baton_worker` from
`sys.modules` on cleanup, which broke three cases in *other* suites that still
held the old class objects. A fixture that tidies a shared import cache decides
what every later case is testing.

75 checks in the delivery suite (was 59), 11 in the new operator suite, 794
across the whole affected set clean under `-W error::ResourceWarning`, 8 in the
container smoke, dependency baseline unchanged at 57.


## Claim 199562 — baton.claude — "complete" was wrong, and one of the five was a defect

The completion claim on claim199285 is withdrawn in FINDING and the five exact
paths went into PLAN before any edit. `EVIDENCE-199285.json` keeps its bytes;
what was wrong was the label over them.

### The defect: a child that never started was reported as a whole capture

`_ran`'s `finally` called `declare()` with no operand, and no operand defaulted
to `finished`. So the reviewer's injected `FileNotFoundError` at the subprocess
boundary left **both** verification streams reported `captured`, zero bytes,
carrying *"the writer saw this stream to its end"*. That is the exact sentence
this vocabulary exists to forbid, and it is worse than the discard it replaced,
because an operator would have believed it.

`_Outcome` names the three cases that actually differ — never started,
interrupted, completed — and both boundaries declare from what happened rather
than from reaching a `finally`. `None` no longer means `finished`; it asserts
nothing. An exit status is still not an outcome: a child that exits 1 wrote what
it wrote and then stopped, and a case pins that a failing verification is a
whole capture.

### The integration startup, and stdout

Only the managed-apply branch reached the wrapper, so the five refusal
diagnostics this Work *added* could still vanish with their container — the half
of the incident that made it expensive. The ordinary branch is captured now. And
the wrapper tees stdout as well: omitting it was my narrowing, not the
contract's. The protocol bytes are untouched because `serve` frames on
`sys.stdout.buffer`, passed as an operand, so a text wrapper never sees a frame;
a case asserts the caller-visible bytes equal the persisted ones.

### The recipes, and the allowlist

Neither supported recipe carried the shared writer, so the fixture's green smoke
proved nothing about either production image. Both carry it now. The recipe test
named exactly one permitted path under `baton_v12`; it names two, and a new case
holds the property the allowlist is a proxy for — the admitted module imports
`itertools`, `json`, `os`, `stat` and nothing from `baton_v12`.

### Native retention, which was a constant and an empty directory

The provider's home is built under a scratch tree destroyed with the turn, and
nothing connected those files to anything durable. `_retain_native` copies them
into the native corner at the end of the turn — the one moment the bytes are
both complete and still there — proved with a fake provider that really writes
session files. **The credential symlink is never followed**: a case plants a
symlink to a secret and asserts it is neither copied nor read.

### The operator command

`baton-attempt-logs` was advertised and installed by nothing, and the examples
put the parent parser's operands after the subcommand, which the program itself
would have refused. It is `baton-v12-stack logs` now — the deployed bundle's own
subcommand, which is what an operator has after an incident — with the operand
order argparse accepts. The follow gap is documented as a gap rather than
described as delivery.

### Two expectations of mine that were wrong

Three older cases called `declare()` bare and relied on the default that *is*
the defect; they name the outcome now. And I expected a never-started child to
leave the native corner `absent` — `materialize` makes the corner before
anything runs, so `empty` is honest: "the room exists and the provider wrote
nothing in it" is a different sentence from "there is no corner".

87 checks in the delivery suite, 756 across the affected set, 122 in stack, 8 in
the container smoke on a rebuilt fixture; dependency baseline unchanged at 57.


## Claim 199683 — baton.claude — the tee was on the wrong layer

### R1 — the protocol buffer went straight past the capture

`_TeeStream.__getattr__` handed back the **real** buffer, and `main` passes
`sys.stdout.buffer` to `serve`. So every frame reached the caller
byte-identically and reached the log not at all — and the case I wrote to prove
stdout retention exercised the text layer, which is not the layer the protocol
uses. Preserving the bytes and retaining them are two requirements and I had met
only the first.

`_ByteTee` wraps the binary stream and `_TeeStream.buffer` returns it, so both
layers append to one handle and neither reorders, re-encodes, delays or splits a
frame. The reviewer's binary probe now shows the caller receiving the exact
sixteen bytes **and** `worker.stdout` holding them.

### R2 — four defects in one copy

*End-only*: it ran in `_ran_provider`'s `finally`, so a wrapper killed before
that copied nothing. It runs from the drain thread now, which already ticks
while the provider runs, and appends only what is new.

*Colliding names*: `a/b` and `a__b` both flattened to `a__b` — three files
counted retained, two present, one source overwritten. Components are escaped
*before* they are joined now. Picking a different literal separator would only
have moved the collision, since any character a separator can be is one a
component can contain.

*Silent truncation*: it read a ceiling's worth and counted the file retained.
Bytes stream in bounded chunks; the bound is on memory, not on the file.

*Skipped failures and a false confinement claim*: failures were skipped and the
count discarded, so an empty corner read as "the provider wrote nothing"; and
`islink`-then-`open` is a check on one object and an open of whatever the name
resolves to next, with every ancestor followed. Every component is opened
relative to the descriptor above it with `O_NOFOLLOW` now, so the credential
slot is excluded by the open failing rather than by a name check a swap could
outrun — and a retention failure is declared on `provider.stdout`, where a
reader will actually meet it.

### R3 — the follow loop

`follow` follows now, until the writer says the stream ended. The termination
rule is the delivery's own rather than one the command invents, silence is not
an ending, Ctrl-C prints the exact byte to resume from, and `--once` keeps the
slice-and-position form. Driven through the deployed `logs` subcommand, not only
the helper.

### One expectation of mine that was wrong

My earlier case expected `projects__one__session.jsonl` — that spelling *is* the
collision, so it expects the escaped form now.

96 checks in the delivery suite, 13 in the operator suite, 818 across the
affected set, 8 in the container smoke on a rebuilt fixture; dependency baseline
unchanged at 57.


## Claim 199781 — baton.claude — my tests threaded by hand what the caller threw away

### R1 — the drain discarded the offsets it needed

`_retain_native` returned a **new** offset map and the drain discarded it, so
every poll started at byte zero and appended the whole file again — seventeen
copies of `abc` in the reviewer's probe.

Every helper-level case I wrote passed, because each threaded the returned map
by hand. Nothing exercised the wiring that ignored it, which is exactly the
difference between a helper test and an actual-caller one. Five cases drive
`_ran_provider` now: many ticks over one file, an append between ticks, bytes
arriving after the last tick, an intermediate failure surviving a clean finish,
and a symlink at the root's own ancestor.

The caller's map is mutated in place — a caller that must remember something
across calls is given the thing to remember, not a copy. Failures live in that
same map and survive the turn. And root acquisition is confined properly:
`os.open(a/b/c, O_NOFOLLOW)` holds only `c`, so opening the composite
`scratch/home/.claude` path never made the claim in its docstring true.

### R2 — follow exited early and mistook absence for completion

A completed ten-byte stream at `--bound 3` printed `abc` and returned success.
`more_may_arrive` says the *writer* may append; it says nothing about whether
the slices already retained have been emitted. The follower drains what is here
before deciding anything.

Following an *absent* stream returned 0 at once, contradicting this command's
own promise — absence is exactly the state a follower started before its writer
is in. It waits now; `inaccessible` is still reported rather than sat on,
because absence, inaccessibility and completion are three different answers.

And a bounded read ending mid-sequence decoded with `replace`, destroying every
character that straddled a boundary while reporting the full byte count.
`_whole` holds back a trailing incomplete sequence so the next slice resumes at
the character boundary — except at true end of file, where a truncated sequence
is the writer's and waiting for it would mean never finishing.

101 checks in the delivery suite, 18 in the operator suite, 777 across the
affected set, 8 in the container smoke on a rebuilt fixture; dependency baseline
unchanged at 57.


## Claim 199842 — baton.claude — a correct rule applied where it cannot make progress

### R1 — withholding a split character can withhold everything

A completed log holding `€x`, followed at `--bound 1`, withheld the single lead
byte it had read, reported `bytes_read: 0`, and the command read that as
completion with nothing printed. My fix was half right: withholding a split
character is correct, and withholding it when it is *all there is* makes no
progress at all. A bound smaller than one character is an ordinary operand.

The reader tops up a split character instead. A bound is a bound on how much is
handed back at once, and reading the bytes that finish a character the caller
already paid for is not a second slice. After the top-up, a still-incomplete
tail means the file ends mid-character — and the two cases differ: a **live**
writer may append the rest, so it is held and the follower asks again; a
**finished** writer will not, so it is reported with replacement rather than
withheld forever.

**And the first version of that fix introduced its own defect**, which its own
test caught: the top-up read three bytes, and three bytes can carry the whole of
the *next* character's lead, so `→←↑↓` came back with a replacement character in
the middle. It reads exactly what is missing now.

### R2 — the offsets knew nothing about which source they had retained

*Restart*: offsets were per-call integers, so a fresh map over the same durable
room appended `abc` a second time. The resume position is the retained copy's
own size on disk now — what is already retained is a fact on disk, and asking
the disk makes restart work by construction rather than by remembering.

*Truncation and replacement*: truncating a retained source to `XY` left `abcdef`
retained with `failed` empty. The source's `(dev, ino)` and size are bound to
the retained copy now; a shorter or different source becomes a new generation
with its own name and a declared note, so an operator sees two files and an
explanation rather than one plausible lie.

*Absence versus inaccessibility*: `_descended` collapsed every `OSError` into
`None` and its caller called that an ordinary not-yet-created directory — so a
permission failure produced an empty corner reported as "the provider wrote
nothing". `ENOENT` stays silent; anything else is declared.

106 checks in the delivery suite, 22 in the operator suite, 786 across the
affected set, 8 in the container smoke on a rebuilt fixture; dependency baseline
unchanged at 57.


## Claim 199918 — baton.claude — a binding that outlives its process

Review `2026-09-18T03-48-00Z` was right about the shape of it: the
source-to-generation binding existed only in `kept["identities"]` and the chosen
generation filename only as a local variable, so every tick after a rotation
measured the original retained file again — `session`, `#2`, `#3` — and a fresh
map after a restart could prove nothing whatever.

**The record lives with the bytes it describes.** `.retention.json` inside the
native corner, replaced atomically through the corner's own directory
descriptor, holding for each source its identity, its destination, its offset
and a digest of its retained head. A binding that does not outlive its process
is not a binding, and this one is read back on the first tick of every
incarnation.

**The record decides, never the length.** In the review's own words: *after
restart never infer correspondence from length alone*. A destination that exists
with no record of which source filled it is not resumed — the old bytes stay
where they are, the new source starts its own generation, and the uncertainty is
declared. That also closes the second failure the review named, where a size
comparison changes its mind once the new source grows past the original retained
size and starts splicing two generations into one plausible file.

**The generation namespace is `%23`.** `_flat` emits only `%25` and `%2F`, so no
flattened source name can contain it. The old `#N` suffix could equal a real
provider filename, and a case now holds a provider file literally called
`session.jsonl#2` apart from a generation of `session.jsonl`.

### The probe found one more, and it was mine

Re-running the review's second probe honestly — change the source to `ZZ`, pass
a fresh map — showed that a source **rewritten in place at the same length** has
the same device, the same inode and the same size. Identity and length between
them see nothing, and the bytes were lost while the capture reported no failure.
The record keeps a digest of the head of what was actually retained, bounded at
4096 bytes, and a tick that finds different bytes there knows this is a
different stream wearing the same name. The bound is stated at the site rather
than hidden: a rewrite that preserves that head *and* does not shorten the file
is indistinguishable from an append and is treated as one.

Two smaller things fell out of it. The truncation, rewrite and unprovable-record
branches were split between `_appended` and its helper; they are in one place
now, because a split decision disagrees with itself the first time either half
changes. And the source is measured through the descriptor that will read it
rather than by name — a name measured and then opened is two objects whenever
anything moves in between.

**Exercised at the actual caller as well as the helper**, which the review asked
for by name and which is the distinction that hid the previous defect: the
rotation, append-after-rotation, restart and same-length-rewrite cases all run
through `ClaudeAgent._ran_provider` and its own shared map.

121 checks in the delivery suite, 143 with the operator surface, 548 across the
affected set, 837 across `job_manager`, 8 in the container smoke on a fresh
episode; dependency baseline unchanged at 57. The smoke was rebuilt because the
shared format module changed — it does **not** prove the native retention, since
the fixture image carries no `claude_agent.py`.


## Claim 200182 — baton.claude — a record is a document until something acts on it

Review `2026-09-18T04-07-54Z` found two defects and both were mine.

### The record was read as data and acted on as a decision

`_read_retention` returned any JSON object it could parse, and `_destination`
took the nested `destination`, `retained`, `identity` and `head` straight out of
it. A synthetic record naming `destination: "../escaped"` had the source's bytes
appended **outside** the native corner, with `failed` empty. `O_NOFOLLOW`
governs the final component only and `dir_fd` resolves `..` exactly as any path
does, so a descriptor-relative open is not confinement — the *name* is, and
`_believed` is now the one place a record's name becomes something that gets
opened.

It validates the whole document: every key a confined single component; every
entry a **closed** set of exactly `identity`, `destination`, `retained`, `head`;
identity a pair of integers; `retained` a non-negative integer; `head` empty or
one lower-case sha256; and the destination either the flattened source itself or
one of its own generations — so one entry cannot redirect another source's
bytes. A bad entry is dropped rather than taking the rest with it, because the
record describes many sources and one unreadable entry is not a reason to lose
the bindings that are provable. The descriptors are constrained too: the record
is refused unless `fstat` says a regular file, since `O_NOFOLLOW` says nothing
about a fifo that would block this drain forever. And the staging entry is
*created* with `O_EXCL` at a per-call name, with only what this call made ever
removed — the two lessons `attempt_log_format.write_declaration` already carries,
applied rather than restated differently. A fixed pid name opened `O_TRUNC` is
not an exclusively owned file when two threads drain two sources.

### The commit window, and a description of mine that was wrong

`_write_retention` could fail and `_appended` discarded the answer, so a record
that never reached disk was reported as no failure at all. A fresh map then
trusted the stale offset, seeked the source to 3, opened the destination
`O_APPEND`, and produced `abcdefdef`.

I had also called an atomic replace of the record a transaction over the
separately appended data. It is not, and the review is right to say so. What is
true is narrower, and it is what makes recovery possible at all: **the bytes go
down first and the record follows**, so the destination can only ever be *ahead*
of the record — and being ahead is a fact on disk this can read. The other order
would leave a record claiming bytes that are not there, which nothing can
reconstruct.

`_reconciled` believes "ahead" only when the retained file's head and **the
source's** agree over the whole reconciled length — a stronger statement than
the record's own stale digest, which by definition describes fewer bytes than
are there. Then retention resumes from what is on disk and the recovery is
declared, because an operator should know a record was rebuilt rather than
believed. Behind, unreadable, or disagreeing: the old bytes stay, a new
generation begins, and the uncertainty is declared. The bound is the same
`FINGERPRINT` as everywhere else here and it is stated at the site.

A short write now still records what *did* reach the room, so the next tick
continues instead of re-copying — and the data failure is said first, because it
is the one an operator is looking for.

19 new checks, 140 in the delivery suite, 568 across the affected set, 837 across
`job_manager`, 146 across W197661's two shared suites; dependency baseline
unchanged at 57. **No image input changed this claim** — `attempt_log_format.py`
and `baton_worker.py` are byte-identical to the copies in `fixture-199918`'s
context — so claim199918's container smoke still describes the current bytes and
was not re-run or re-attributed, and its stated limitation stands.


## claim200454 — validation that throws, and a record that cannot say what a file IS

Answering `review-2026-09-18T04-53-08Z.md`. Both findings were mine. Both
reproduced before anything was changed, with the reviewer's own shapes:
`/tmp/w198667-claim200454/probe_before.py` gives `ValueError: invalid literal
for int() with base 10: '²'`, `ValueError: Exceeds the limit (4300 digits)`, and
a child killed at two seconds with the retained fifo still in place.

### R1 — `isdigit` and `int()` are not the same question

`_generation_of` asked one and then acted on the other. `str.isdigit` is true of
the superscript `²` and of every non-ASCII decimal digit; `int()` accepts
neither, and refuses 4301 ASCII digits besides. Both documents are well under
`MAX_RETENTION`, so a bounded record that this capture is supposed to *discard*
threw instead — out of `_believed`, out of `_read_retention`, out of the whole
tick.

The shape is decided now without converting it: `_GENERATION` is a bounded ASCII
numeral, no leading zero, greater than one, no longer than any run of rotations
this corner could reach. Whatever it cannot recognise is FALSE — a malformed
entry, dropped and declared — rather than an exception thrown through a capture
whose entire purpose is to keep working when something else has already gone
wrong.

### And the sweep found a third of the same kind

The review asked me to check other parser and validation exceptions under the
same bounded-document contract, and the check found one the reviewer did not
name and that is mine: **a bound on bytes is not a bound on depth.** A record of
two hundred thousand open brackets is a fifth of `MAX_RETENTION` and exhausts
the decoder's stack, and the `RecursionError` it raises is not a `ValueError`.
The same escape existed at two more bounded decodes in this file — the review
report, whose malformed answer is "not a verdict", and the task document, whose
malformed answer is a `TaskRefusal`. Raising through a refusal vocabulary says
the adapter broke when the truth is that somebody handed it nonsense. All three
are closed; the fourth site already carried the lesson.

I am naming this as scope I added rather than burying it: it is the same defect
class in the same candidate file, found by the check the review asked for, and
leaving it while reporting the contract swept would have been a lie.

### R2 — every type check stood on a NAME

`_retained_size` accepted a fifo's size zero, `_reconciled` read that as an
ordinary matching offset, and `_appended` then opened the destination
`O_WRONLY` with no reader and waited. `_ran_provider` joins this drain and calls
retention again during finalization, so a logging failure could strand the
provider path — the thing this Work exists to prevent, caused by this Work's own
code.

Two layers, because the race is real and a stat cannot close it. `_retained_size`
answers `None` for anything that is not a regular file, and a destination nothing
can account for becomes a new generation with the reason declared — so the
source's bytes are KEPT rather than lost because the corner was tampered with.
And both data descriptors are acquired with `O_NONBLOCK` and refused unless
`fstat` says regular: the source, because `_walked` checks a name and this opens
it, and the destination, because `_retained_size` checks a name and this writes
to it. `O_NONBLOCK` alone answers only the fifo NOBODY is reading; a peer that
IS reading would otherwise be handed this attempt's log bytes, and only the
descriptor can refuse that.

### The reversal probe corrected a description of mine

I wrote that without `O_NONBLOCK` a source fifo makes the open itself wait.
Running the new cases against a scratch copy with all five corrections undone
shows that is only true when nothing holds the write end: with a writer
attached, the old code opened it at once, took it for a file, and failed at the
SEEK with "a native file could not be positioned (OSError)" — the symptom, not
the cause. The case is renamed and its docstring now says what actually happens.
Every one of the 12 new cases fails on that reversed copy: 3 bounded children
time out, 5 raise `ValueError` or `RecursionError`, 5 assert the old wrong
answer. The scratch copy is removed; the tree carries only the corrections.

### Verification

`test_attempt_logs` 152 (12 new); delivery plus operator 174 in 1.533s; the
affected set — attempt_logs, attempt_logs_command, claude_agent,
integration_worker, worker_entry, launch, oci, exchange — 832 in 25.877s OK;
`job_manager` 842 in 9.599s OK; W197661's `test_worker_container` and
`test_execution_limits` 79 in 31.086s OK; `test_dependencies` unchanged at 57
failures, zero added. All under `-W error::ResourceWarning`.

**No image input changed this claim.** `attempt_log_format.py`, `baton_worker.py`
and `scripted_agent.py` are byte-identical to `fixture-199918`'s context copies,
so claim199918's 8/8 container smoke still describes the current bytes and was
not re-run, rewritten or re-attributed — and its stated limitation stands: that
image carries no `claude_agent.py` and does not prove native capture.


## claim200870 — an alias is not a name, and a reserved name is not a skip

Answering `review-2026-09-18T05-32-05Z.md`. Both findings were mine, and both
reproduced against the reviewed bytes before anything was changed:
`/tmp/w198667-claim200870/probe_before.py` writes the provider's transcript to a
file outside the native directory with `failed` empty, and leaves the corner
empty for a source named `.retention.json` with `reached` true and `failed`
empty.

### R1 — a regular file at a confined name can still be somebody else's file

Three checks stood between this capture and a destination, and all three were
about the PATH: `O_NOFOLLOW` refuses a symlink at the final component,
`_confined` refuses a name that leaves the directory, and the descriptor check
added last claim proves `S_ISREG`. A hard link defeats all three at once,
because it is a second name for the **inode**: the reviewer created an empty
sibling outside the room, linked it at `native/s.jsonl`, and the capture
appended nineteen bytes to both names and reported success.

`_acquired` is the one owner of destination acquisition now, and it asks the
descriptor two questions rather than the path: is this a regular file, and does
this inode have exactly one link. A retained file this capture created and has
kept has one; anything else is a file somebody else also holds, and bytes
written into it leave the room by definition.

**And a new destination is CREATED rather than opened.** `O_CREAT` alone adopts
whatever is already at the name — which is precisely how the aliased file became
a destination. When this decides it is claiming a name nothing holds, `O_EXCL`
makes that true instead of assumed, and `EEXIST` means the answer changed
underneath it. A case observes the real open flags rather than asserting the
intent.

**A refusal keeps the bytes and moves on.** What is at that name is not touched,
the uncertainty is declared, and the source is retained as its own generation —
the same answer a truncation, an in-place rewrite and a fifo already get, because
from this capture's side they are one fact: the destination it was about to
write is not one it can account for. ONE rotation, because a corner whose fresh
name is also unusable is not one more attempt away from working, and a capture
that kept trying would be an unbounded loop inside the drain the provider's own
turn joins.

### R2 — the bookkeeping had reserved a filename the provider is allowed to use

`_walked` skipped a source called `.retention.json`, and the comment explaining
why says the reason it was wrong: *the bookkeeping lives in the DESTINATION*.
That walk is over the SOURCE tree, so the only file that can ever match is a
real one the provider wrote — and it was neither retained nor reported. The one
distinction this whole vocabulary exists to make is between a log that is
missing and a log that is empty, and here a present log became an absent one
silently.

The naming scheme answers it. `_flat` already escapes a literal per-cent to
`%25` before joining, which is what makes the mapping injective; a flattened
name that would collide with the record or its staging namespace now has its
leading `.` escaped in the same scheme. `.retention.json` is retained as
`%2Eretention.json`; `.retention.json.1` as `%2Eretention.json.1`; and a
provider file really called `%2Eretention.json` becomes `%252Eretention.json`,
so the two are held apart by a case rather than by hope.

That also closes a half of this the reviewer asked me to check and I had not:
`_confined` refuses `.retention.json` and `.retention.json.*` as record
DESTINATIONS. So before this, even the prefixed name that *was* retained could
never be resumed from its own record — every restart would drop its entry and
start a generation. A case now takes that source through two ticks and a fresh
map and finds one file, appended once.

### The reversal probe, and two expectations of mine it corrected

Ten of the eleven new cases fail against a scratch copy with both corrections
undone; the eleventh is the ordinary single-link append, which is the control
and passes both ways. The scratch copy is removed.

Two of my own expectations were wrong and the run said so. I asserted that a
destination aliased *after* it was created would leave only the appended tail in
the new generation — it holds the whole source, because a new generation is a
fresh copy exactly as a truncation or a rewrite produces, and nothing here can
prove the aliased file's bytes are this source's. And I called `locators` with a
root and an attempt id; it takes the delivery. Both are corrected in the cases
rather than worked around.

### Verification

`test_attempt_logs` 185 (11 new); delivery plus operator 185 in 1.562s; the
affected set — attempt_logs, attempt_logs_command, claude_agent,
integration_worker, worker_entry, launch, oci, exchange — 843 in 25.958s OK;
`job_manager` 849 in 9.663s OK; W197661's `test_proposing_fixture` and
`test_ending` 96 in 0.600s OK; `test_dependencies` unchanged at 57 failures,
zero added. All under `-W error::ResourceWarning`.

**No image input changed this claim.** `attempt_log_format.py`,
`baton_worker.py` and `scripted_agent.py` are byte-identical to
`fixture-199918`'s context copies, so claim199918's 8/8 container smoke still
describes the current bytes and was not re-run, rewritten or re-attributed —
and its stated limitation stands: that image carries no `claude_agent.py` and
does not prove native capture.


## claim201008 — the native corner's lessons, at the boundary all six streams use

Answering `review-2026-09-18T06-27-53Z.md`. Both findings were mine. Both
reproduced against the reviewed bytes before anything changed
(`/tmp/w198667-claim201008/probe_before.py`): the bounded child was killed at
two seconds on the fifo, `raw provider bytes` reached a file outside the room
while the capture declared `finished`, and a second writer's appends inherited
the first's `finished`.

### R1 — I corrected one opener and left the one everything uses

Last claim I taught `_acquired` three things: acquire nonblocking, ask the
DESCRIPTOR what it is, and ask the inode how many names it has. Then I left
`attempt_log_format.append_writer` — which all six streams, both tees and the
wrapper's earliest output go through — with none of them.

That is worse than it sounds. This open happens BEFORE the provider starts: a
fifo where `provider.stdout.log` belongs blocks the capture, and the capture is
what the startup diagnostic is written through. The thing that exists to record
a failure could cause one.

The three properties are at that boundary now, and a fourth that came with them:
a fresh entry is CREATED with `O_EXCL` rather than adopted, because `O_CREAT`
alone takes whatever is at the name. The refusal travels: `append_writer` takes
an optional list and appends one bounded sentence, and both `_Captured` and
`_TeeStream` put that sentence in the declaration a reader actually meets — so
`failed` says "this stream's log is also linked elsewhere" rather than the
generic prose that would let an operator believe bytes were lost in transit
when none were ever accepted.

**Restart still appends**, which is the required outcome and which the `O_EXCL`
could have broken: a case writes two incarnations and reads back both.

### R2 — a terminal word is about BYTES, not about a name

The first writer declares `finished` and that is true of the file as it was. It
is not true once somebody appends, and nothing was undoing it. The reviewer read
the consequence through the real reader: `captured`, "the writer saw this stream
to its end", `more_may_arrive: false`, over a growing file. A follower exits
there. And `declare(None)` — which exists precisely to say that nobody knows how
this ended — left the stale word alone, so the one call that asserts ignorance
published somebody else's certainty.

`clear_declaration` removes a declaration that no longer describes the bytes,
and `append_writer` calls it before it answers a handle. ABSENCE IS THE HONEST
INTERVENING STATE: the reader already calls a stream with bytes and no
declaration `live`, which is exactly "we do not know whether this is all of it".
The bytes are never touched — metadata only — and a clearing that FAILS refuses
the handle, because appending under a word that describes other bytes would
report somebody else's ending as this capture's.

**And it is not a pass obtained by declaring everything incomplete forever**: a
second writer that finishes normally still publishes `finished`, and the reader
then says `captured` with `more_may_arrive: false`. A case holds that line.

### The reversal probe, per case, because one of them hangs

Against a scratch copy with both corrections undone, nine of the fifteen cases
discriminate: eight fail, and `test_a_FIFO_stream_is_DECLARED_failed_and_says_why`
HANGS — it exits 124 under a fifteen-second bound, which is the defect itself
rather than a failed assertion. The other six are controls that pass both ways:
the ordinary stream, the restart append, the earlier bytes, a second writer that
finishes, clearing nothing, and a directory at the stream name (which the old
opener happened to refuse with `EISDIR`). The scratch copy is removed.

### The image evidence moved with the bytes

`attempt_log_format.py` and `baton_worker.py` both changed this claim, so
`fixture-199918`'s context copies no longer describe this tree and **its smoke
no longer describes these bytes** — it proves what it always proved, about the
bytes it was built from, and keeps its own attribution. `fixture-201008` is a
fresh episode carrying the current bytes: image `sha256:d1a9021c…`, built
`--pull=false --no-cache --network none`, and all eight container checks hold —
including the two this Work exists for, that the wrapper's earliest output was
retained in the room and that the container is gone and the evidence is not.

### Verification

`test_attempt_logs` 200 (15 new); delivery plus operator 200 in 1.602s; the
affected set 858 in 26.071s OK; `job_manager` 849 in 9.668s OK; W197661's
`test_w197661_verifier`, `test_proposing_fixture` and `test_ending` 127 in
0.609s OK; `test_bootstrap` 125 OK; `test_dependencies` unchanged at 57
failures, zero added. All under `-W error::ResourceWarning`. Plus one image
build and one container smoke, 8/8.


## claim201156 — a new success cannot prove an earlier missing tail

Answering `review-2026-09-18T06-53-11Z.md`. The finding is a consequence of my
own last correction, and it reproduced exactly
(`/tmp/w198667-claim201156/probe_before.py`): a capture that DETECTED its own
short write declared `failed`, a second capture appended cleanly and declared
`finished`, and that is what the sidecar said over `firstsecond-whole`.
`truncated` and `partial` went the same way.

### The two facts were one file, and they are different questions

The sidecar answers *what did the writer that published it see*. Clearing it
when somebody reopens the stream is right, and it is what keeps a reopened
stream honestly `live` rather than stale-finished — the correction this review
accepts. But the completeness of the BYTES IN THE FILE is a different question,
and those bytes include every earlier generation's. Clearing the only record of
an earlier loss answered the second question with the first one's answer.

`carry_declaration` moves a loss into a per-stream cumulative record before it
clears the sidecar, and `append_writer` hands the worst state any generation has
declared back to the caller. `_aggregate` — in both the provider capture and the
wrapper's tee, because both reopen — publishes the worse of that and its own
outcome, with a reason that names the earlier generation rather than leaving an
operator to look at the wrong writer.

**ONLY LOSS IS CARRIED**, which is what keeps the control honest: a `finished`
generation writes no record at all, so `finished → reopen → finished` still ends
`captured` with `more_may_arrive` false. And while the second writer is open
there is still no sidecar, so `follow` still reports the stream alive — the
accepted correction is not undone. The loss is durable on disk in the meantime,
so a writer killed before it declares does not take the earlier evidence with
it; a case drives exactly that and then a third writer, which still publishes
`failed`.

**An unreadable cumulative record is treated as the worst thing it could have
said.** It is not permission to claim completeness.

### The reversal probe

Eight of the thirteen new cases fail against a scratch copy that clears instead
of carrying. The other five are the controls — the all-successful restart, the
active writer keeping follow alive, a clean first capture writing no record, the
record not appearing as a stream, and the wrapper's all-successful restart —
which pass both ways, as controls must. The scratch copy is removed.

### Two fixture defects of mine, caught by running them

The bounded-write shim replaced the format module wholesale, which worked for
the provider capture (it opens in its constructor, before the swap) and broke
the wrapper's tee, which opens LAZILY and met a shim that had never heard of
`append_writer`. It delegates everything but the write now. And a `subTest` loop
rebuilt the room under a descriptor this case holds, so every later write failed
for a reason unrelated to the rule; it uses one stream per prior state instead.

### The image evidence moved with the bytes, again

All three image inputs changed, so `fixture-201008`'s smoke no longer describes
these bytes and keeps its own attribution. `fixture-201156` carries the current
bytes: image `sha256:23edb0ca2a9a7e93a4101908e1e6333d2cbe419fd7851f910077e095b145751e`,
built `--pull=false --no-cache --network none`, eight of eight checks holding.

### Verification

`test_attempt_logs` plus the operator suite 213 (13 new); the affected set 871 in
26.038s OK; `job_manager` 849 in 9.576s OK; W197661's `test_w197661_verifier` and
`test_proposing_fixture` 83 OK; `test_dependencies` unchanged at 57 failures,
zero added. All under `-W error::ResourceWarning`. Plus one image build and one
container smoke, 8/8.


## claim201274 — three ways an unvouched-for stream still read as complete

Answering `review-2026-09-18T07-09-49Z.md`. All three findings are in the
cumulative record I added last claim, and all three reproduced against the
reviewed bytes (`/tmp/w198667-claim201274/probe_before.py`): the unknown ending,
the ignored persistence failure and the inaccessible history each ended with
`follow` answering `captured`, `more_may_arrive: false`.

### R1 — carrying DECLARED loss is not carrying loss

`carry_declaration` carried what a previous writer SAID. A writer that said
nothing — `declare(None)`, which exists precisely to assert that nobody knows
how this ended — left no declaration, and so did a corrupt sidecar, which has no
`declared` member. Both reached the branch meaning "nothing to carry", so the
next clean append published `captured` over a prefix nobody vouched for. Review
201085 had already asked for unknown → successful-restart coverage and I did not
give it.

What makes a reopen `partial` is now BYTES WITH NO TRUSTWORTHY ENDING, and
`_has_bytes` is the distinction that keeps the ordinary capture free: an empty
new stream is still a clean start. It answers True when it cannot tell, because
bytes that cannot be counted are not bytes that can be assumed absent.

### R2 — the only evidence was deleted before the copy was known to exist

`carry_declaration` called `_write_carried`, discarded the answer, unlinked the
prior sidecar and returned success. An ordinary `OSError` in that helper
therefore destroyed the one record that bytes were already missing, and the next
successful writer published `captured` over three generations.

The sidecar is cleared only when the carry succeeded; otherwise the acquisition
REFUSES and the old evidence stays where it is. That keeps the failure inside
the logging: a refused handle leaves the stream on `DEVNULL` and declared
`failed`, so the provider runs exactly as it would have — a case asserts that
directly, and another asserts the refused writer's bytes reach no file at all.

### R3 — an inaccessible history is not an absent one

`read_carried` answered `None` for every open or read failure and for a record
that was not a regular file. Only malformed JSON was conservative, which is the
opposite of the rule the handoff stated. `ENOENT` is still `None` — the ordinary
first capture and clean restart — and everything else is `failed`, because a
history this capture cannot read cannot establish completeness.

### The reversal probe, and an expectation of mine it corrected

Nine of the thirteen new cases fail against a scratch copy with all three undone;
the rest are the controls. And one of my own assertions was wrong: I expected the
REFUSED writer to declare nothing, and it declares `failed` — correctly, because
its own bytes never reached a file. The prior sidecar is untouched and the new
word says the same thing about the same bytes, which is why the refusal is safe.
The case says that rather than asserting what I first assumed.

### Verification

`test_attempt_logs` plus the operator suite 226 (13 new); the affected set 884 in
26.035s OK; `job_manager` 849 in 9.618s OK; W197661's `test_w197661_verifier` and
`test_proposing_fixture` 100 OK; `test_dependencies` unchanged at 57 failures,
zero added. All under `-W error::ResourceWarning`. Plus one image build and one
container smoke, 8/8.

`attempt_log_format.py` changed, so `fixture-201156`'s smoke no longer describes
these bytes and keeps its own attribution; `fixture-201274` carries the current
ones at image `sha256:f62733c6f85d320c49e3096b6a85195aa4c2a572a9a03f93462ca0fef982253c`.


## claim201391 — a membership test on unvalidated JSON is not validation

Answering `review-2026-09-18T07-23-56Z.md`. The finding was mine and it
reproduced exactly (`/tmp/w198667-claim201391/probe_before.py`):
`{"declared": []}` and `{"declared": {}}` each raised `TypeError: unhashable
type` out of the real `_Captured` constructor, while the valid `"failed"` string
control worked.

### The same shape, in a different place

This campaign already corrected `_generation_of`, which asked `str.isdigit` and
then acted on `int()`. This is the same mistake with a different pair:
`read_carried` decoded a document and then asked `said in SEVERITY`, and
membership is a DICTIONARY LOOKUP that a list or an object cannot answer. What
was meant to be validation raised instead.

It matters where it happened. That read runs inside `append_writer`, which runs
inside `_Captured.__init__`, which runs BEFORE the provider starts — and the
wrapper's tee reaches the same opener before its own startup diagnostic. So a
malformed cumulative record did not make the capture conservative; it made the
capture fail, and a capture that cannot set itself up takes the workload with it.

`declared_state` is the one place that decides now. It answers a state only for
a string that is one, and `None` for every other JSON value — list, object,
number, boolean, null, or a string that is not a state. `read_carried` is total
over all of them and answers `failed`, because a history that cannot be read
cannot establish completeness. `worst` routes BOTH operands through it: the
review asked for that boundary to be checked and it had the identical
assumption, so `worst([], "failed")` raised too. And `carry_declaration`'s
severity lookup is guarded rather than trusting a caller's invariant.

### The cases, and the containment they hold

Every JSON value type through the real provider capture; the valid states still
reading as themselves, which is the control that keeps this from becoming a rule
that fails everything; a clean stream untouched; **the child still getting a
usable stream** and the earlier bytes still there, which is the containment
itself; no descriptor leaked by twenty malformed constructions; `worst` on either
side; `declared_state` directly; and both wrapper paths, including that the real
stream still receives its text — a tee that could break the thing it observes
would be worse than no tee.

### A fixture mistake I have now made twice

My first draft rebuilt the shared room inside a `subTest` while the case held its
DESCRIPTOR, so every later write failed for a reason unrelated to the rule. I made
exactly this mistake in claim201156 and fixed it there the same way. This suite
takes a FRESH delivery and its own room per case, and the helper says so at the
site rather than leaving the next person to rediscover it.

### Verification

`test_attempt_logs` plus the operator suite 235 (9 new); the affected set 893 in
26.162s OK; `job_manager` 849 in 9.776s OK; W197661's three suites 119 OK;
`test_dependencies` unchanged at 57 failures, zero added. All under
`-W error::ResourceWarning`. The reversal probe fails 10 of the new assertions
against a scratch copy with the three guards undone.

`attempt_log_format.py` changed, so `fixture-201274`'s smoke no longer describes
these bytes and keeps its own attribution; `fixture-201391` carries the current
ones at image
`sha256:f7bcc60319a23c84e069f58e6c4c48ecc2a4bad442d8421b34dd2c612861d341`, with
all eight container checks holding.
