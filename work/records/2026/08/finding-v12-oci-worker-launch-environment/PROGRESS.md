# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-27 — claimed and implemented

Claimed W26291 at seq 27020. This is the [P0] I reported while holding W6636:
`run_vector` composed no `--env`, the reference worker requires four
`BATON_WORKER_*` values, and every execution container the reviewed adapter
started from the reviewed image exited 2 with empty stdout and stderr. Two
closed components that could not meet, and the defect existed only in the join.

Evidence: `evidence/w26291-2026-08-27-launch-environment.txt`.
Harness: `evidence/w26291-mutation-harness.py`.
No Git history or index was mutated.

### PLAN 1 — both ends, revalidated

The worker names exactly four values for **both** postures and refuses a
`BATON_WORKER_*` member outside the set. And the seam is **not** protocol state:
the frozen `runtimeStartBody` has `additionalProperties: false` and no
environment member, so this is the manager/adapter seam the finding says it is,
typed at the one boundary that composes the engine vector.

### PLAN 2–3 — the seam, and one fact with one owner

The caller supplies **three**. `BATON_WORKER_POSTURE` is deliberately absent
from the request: this adapter has owned `posture` since construction, and
taking it again per call would let the environment and the mount rules disagree
about what kind of container this is.

No arbitrary pass-through. An unexpected member refuses *here* rather than
failing inside the container after it started, where the manager can no longer
say why — the worker refuses an unknown `BATON_WORKER_*` anyway, so the choice
is between a diagnosable refusal and a container that died.

The manager carries the values across the seam and does **not** validate them:
the adapter does, because that is where the engine call is, and a value refused
after the vector was composed is a value that already reached a command line. A
second validator in the manager would be a second statement of one rule.

### PLAN 4 — the acceptance's positive regression

W6636's `test_the_adapter_starts_no_worker_that_can_run` asserted the defect.
Asserting that now would be asserting the defect, so it is **replaced** by
`test_the_adapter_starts_a_worker_that_actually_runs` — and that replacement is
authorized by this Work's own acceptance rather than being my judgement, which
is the difference from the one I had to flag on W26283.

**Exit 0 is the proof.** The difference from exit 2 is the whole finding: 2 was
"I was started without the four values and cannot correlate anything I say"; 0
is a worker that started, found its environment, read EOF on a closed stdin and
shut down cleanly.

Negative coverage: missing, malformed, over-wide, control-bearing, unexpected
and non-document environments all refuse before the engine. A case reads the
worker's own `ENVIRONMENT` literal **by AST** and holds it against the
adapter's set — the two exist in two places by necessity, since the worker
cannot import the manager, and a case that reads both is the only thing keeping
them one contract. That is the defect W6636 found, stated as a rule.

The leak clause was **checked rather than assumed**: §13 already walks the whole
start vector, so this needed no second rule, but nothing established that the
existing walk covers a channel that did not exist when it was written. A live
bearer in `BATON_WORKER_CONTRACT` refuses with `secret-leak`.

### One second mechanism removed, found by measurement

My first version sorted the environment items **and** rebuilt the document over
the fixed `LAUNCH_VALUES` tuple — two statements of one property. The
measurement showed it: removing the sort changed no verdict, because the tuple
had already decided the order. The sort is gone, and the mutation now points at
the real mechanism, which is caught.

### Gates

- **9 mutations, all caught**; source fingerprinted before and after
- full v12 tree — **1578 tests, 7 failures**, exactly the accepted baseline

## State

PLAN 1–5 done. Passed for independent review rather than closed.

### For review

- This Work does not decide **where** the three caller-supplied values come
  from in manager state. `request_runtime_start` carries them as an operand;
  which session, contract line and role a real delivery uses is the lifecycle's
  question, and the finding's boundary keeps it outside this Work. Flagged
  rather than assumed.

## 2026-08-28 — the live launch document, implemented end to end

Claimed W26291 at seq 28962 after `baton.prompt` reported the readiness bridge
had missed the level. Read the thread, then the whole record, then the tree.

### The review was right, and what it was right about

The [P0] said the submitted implementation was the design this dossier had
already superseded. It was: an `environment` operand on
`request_runtime_start`, four `--env` arguments in `run_vector`, a worker still
reading `BATON_WORKER_*`, and a positive Docker case proving only that the
retired transport made the old worker exit zero. Green tests for a retired
contract are not acceptance evidence for the live one.

**The whole of it is gone rather than deprecated.** `WORKER_ENVIRONMENT`,
`LAUNCH_VALUES`, `_launch_environment`, the `environment` operand at both the
manager and the adapter, the worker's `ENVIRONMENT` set and `posture_of`, and
every `--env` this Work ever composed. A compatibility path is exactly what the
supersession exists to end, and one left behind is the second live contract.

### What is there instead

`worker_manager/launch.py` authors the document, and authorship is the point:
it is rebuilt over `LAUNCH_MEMBERS` rather than copied from a caller's mapping,
so a caller supplies three VALUES and never a shape. Every value is bounded at
one private owner under one literal label; the encoded bytes are bounded
against the ceiling the WORKER reads under, because a document the worker would
refuse is not one this manager may write. §13 walks it before a byte is
written.

Then it is materialized: one regular file, `O_EXCL | O_NOFOLLOW`, at its final
mode, under an attempt-private root that refuses to be written into if it
already exists, and torn down whole if any of that fails.

**The mode is 0444, and that is the decision in this cut I would most want a
reviewer to look at.** A bind mount carries the host file's ownership and mode
through unchanged and the container runs as a fixed non-root uid, so an
owner-only document is one no worker can read — for a reason nothing in the
mount table would show. World-readable is only acceptable because §13 keeps
this document non-secret, and that is *driven* rather than asserted: a live
bearer in a contract line refuses before the root is created, and the case
checks the directory is empty afterwards.

The adapter holds the delivery from construction, like the credential delivery
and for the same reasons — attempt-scoped, manager-owned, not assignment
material. It composes exactly one read-only bind at
`/run/baton/launch.json`, and the target is this contract's constant rather
than the delivery's word.

**One thing I had to correct mid-cut, and the boundary layer is what caught
it.** I first crossed the capability inside the start REQUEST. That request is
a document boundary and `boundaries.document` refuses anything carrying
behaviour — correctly. Reducing the delivery to something that fits would have
made it a PATH, which is the caller-selected locator the fixed target exists to
remove. So it is held at construction and the pair it answers with reaches
`run_vector`, which is exactly the shape credentials already had.

### The worker

Opens the fixed path `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`, proves the
descriptor is regular, reads at most the ceiling plus one byte, and proves the
file is not writable for its own view — because a launch document this worker
could rewrite is one it could change between reading it and being asked what it
is. Then the closed member set, the schema BY EQUALITY, and every value's type
and bound, all before any agent execution.

The two failure kinds map onto the two the loop already had: unreadable or
no usable session is `Uncorrelated`, so nothing is written and the manager
settles the start it owns; readable-and-wrong is LATCHED and answered once
through the ordinary correlated fault.

### The posture, which is a decision and is recorded as one

Removing `posture` from the document removes the worker's only source for it.
There is no environment fallback, the image is forbidden a default, and the
ruling says there is no constant to transport — so the program no longer asks
what kind of container it is. `POSTURES`, `posture_of`, the posture-keyed
environment set and the posture-keyed operation set are gone; `describe`'s
answer loses `posture` and `environment` and gains `launch`.

**`consider` is KEPT**, as a known operation this runtime is not entitled to.
Deleting an operation from a ruled protocol is a larger decision than this Work
holds, and keeping it is what makes the entitlement refusal mean anything — an
unknown word refuses as a protocol error and proves nothing. The open question
of retiring the rest of the consent vocabulary is named in `FINDING.md` and
needs an owner.

### Existing expectations I replaced, and the mapping

The review required replacing the retired evidence. Every case below had a
SUBJECT that no longer exists, and each replacement asserts the property the
original was protecting:

| replaced | replacement |
| --- | --- |
| `test_a_consent_container_answers_describe_and_consider` | `test_a_real_container_describes_the_one_runtime_it_is` |
| `test_a_real_consent_container_is_not_asked_to_work` | `test_a_real_container_is_not_asked_to_consider` |
| `test_a_real_consent_container_mounts_neither_input_document` | `test_a_real_container_reads_its_launch_document_read_only` |
| `test_a_real_container_refuses_the_other_postures_session` | `test_a_real_container_refuses_another_containers_session` |
| `test_a_container_built_with_the_wrong_posture_latches_and_exits` | `test_a_container_whose_document_names_another_generation_latches` |
| `test_a_consent_container_carrying_assignment_material_latches` | `test_a_container_whose_document_carries_an_unknown_member_latches` |
| `test_an_invalid_posture_is_one_correlated_fault_and_a_non_zero_exit` | `test_a_document_from_another_generation_latches` |
| `test_a_container_built_with_the_wrong_material_latches_too` | `test_a_document_carrying_material_it_should_not_latches_too` |
| `test_consent_reads_neither_input_document` | `test_an_agent_never_runs_for_an_operation_this_runtime_refuses` |
| `ConsentCannotReachExecution` | `ThisRuntimeAnswersOnlyItsOwnOperations` |
| `test_consent_accepts_and_declines_deterministically` + `test_a_consent_answer_names_nothing_it_cannot_see` | `test_the_scripted_consider_is_deterministic_and_reads_the_document` |
| `test_the_two_postures_are_the_whole_set` | `test_the_operation_set_is_the_one_runtimes` |
| `TheLaunchEnvironmentIsFourValuesAndNoChannel` | `TheLaunchDocumentIsAMountAndNotAChannel` |

Three answer-shape cases lost their end-to-end vehicle rather than their
subject: they drove `consider`, whose answer comes straight from the agent, and
this runtime is not entitled to it. They now ask `check_answer` directly and
say so, because driving them end to end would assert the ENTITLEMENT refusal
three times under three names claiming to be about answer shape.

### What the measurement found that I had not

The first harness run caught 14 of 19 and I fixed all five gaps rather than
weakening the mutations. Two of them were real defects in cases I had just
written:

- **The FIFO case passed with `O_NONBLOCK` removed.** The alarm handler raised
  `TimeoutError`, which IS an `OSError` in Python — so `read_launch`'s own
  `except OSError` caught the alarm and turned a three-second BLOCK into the
  same `(2, [])` a prompt refusal produces. The handler now raises something
  that is deliberately not an `OSError`.
- **The read-bound case passed with the bound removed**, because the LENGTH
  check below the read refuses an over-wide document either way. A case that
  asserts only the refusal says nothing about the bound, so the new one COUNTS
  BYTES — the same correction W26283's re-review made one Work ago, which I
  should have carried over without being shown it twice.

The other three were uncovered guards: the exclusive no-follow create (driven
now by a link planted in the interval between the root being made and the file
being opened), the short-write rule (driven by a writer that accepts eight
bytes at a time), and the adapter's delivery-kind proof.

### Gates

- `test_launch` 25, `test_oci` 89, `test_worker_image` 103, `test_launch` +
  `test_oci` + `test_attempts` + `test_credentials` + `test_workspaces` +
  `test_sealing` 380 — all green
- the launch-document harness — **19 of 19 mutations caught**, across both
  trees and including the real-engine container suite
- `tools/parallel_test.py` — 1551 tests, **6 failures, all in
  `test_boundary_inventory`**, the accepted baseline; NONE of them names this
  Work. The launch module's owners, delegates and probes are registered, and
  the operand table gained `session`/`contract`/`role`/`launch_delivered` and
  lost the now-stale `environment`.
- `--phase serial` — 104 tests, 0 failures, including
  `test_worker_container` 50 and `test_lifecycle_composition` 26 against a real
  daemon. The positive case proves the reference worker starts, reads its
  document and exits 0, and that the vector carries no `--env` at all.

### Record cleanup the review asked for

The duplicate scratch harness `w26291_mutation.py` is removed from the record
root; it was byte-identical to `evidence/w26291-mutation-harness.py` (sha256
`0686a08c…`) and carried no unique evidence. That harness is KEPT exactly as
produced — I damaged it while prepending a supersession note and restored it
byte-for-byte, verified by digest — and the supersession lives beside it in
`evidence/w26291-mutation-harness-SUPERSEDED.md`, which also carries the
`check_input_pair` correction: W26296 owns it, the registration has landed, and
the accepted baseline is SIX.

No Git history or index was mutated. Awaiting independent review.

## 2026-08-28 - the re-reviewed findings, corrected

Reclaimed W26291 at seq 29918. All five findings are real. Reproduced the P0
before touching anything: the file mode under umask 077 was 0o400.

### [P0] The mode was requested, not established

A creation mode is filtered by the process umask. Under the ordinary service
umask 077 the manager authored a 0400 document, and the container's fixed uid
65532 cannot read that -- so the positive launch regresses to the unrunnable
worker this whole Work exists to fix, silently, and only on a host whose umask
happens to be restrictive. The case that existed observed the test process's
own umask and could not see it.

The file is now created at 0000 and chmoded to 0444 on the DESCRIPTOR that
wrote it, after the last byte. Exact under any umask; no writable interval at
any point; and no instant at which a half-written launch document is readable,
which is strictly better than what was there before. Two regressions: one sets
and restores 077/027/022/000, one proves the file is mode 0000 at every write.

### [P1] The canonical seam still permitted no document

The delivery defaulted to absent at construction AND at start, so the public
path could create exactly the unrunnable worker this Work exists to prevent --
with only the worker later refusing it, which is a container that died rather
than a delivery this manager declined.

It stays optional at CONSTRUCTION, because the adapter's runtime half -- list,
observe, stop, destroy, seal, collect -- is constructible without one exactly
as the declared outputs are. It is refused at START, before the engine is asked
anything, beside the authorized-root refusal and for the same reason: nothing
exists yet to settle.

That change reached further than the source. Every canonical start in
test_oci, test_credentials, test_oci_engine, test_credentials_engine,
test_lifecycle_composition and the boundary-inventory witness now carries a
materialized delivery. The lifecycle and engine fixtures mint one PER ADAPTER
rather than caching one per attempt -- because a settled delivery is now
discarded, and a cached one would hand a second adapter a document the first
already tore down. That is the new lifecycle working, and the fixture was what
had to change.

### [P1] The launch root had no ending at all

The discard operation existed and nothing production called it, so a refused
start and a destroyed runtime both left an attempt-private root and a
world-readable document behind for good. PROGRESS.md claimed the adapter owned
teardown; that claim was false.

It now has one ending, taken only on the evidence that no runtime can hold the
mount -- the same rule the credential root is held to, on the mount beside it.
An absence that cannot be proved leaves it unresolved rather than removed.

And it is reported BESIDE the credential ending rather than folded into it. My
first attempt did fold it in, and that was wrong for a reason worth recording:
a delivery with no credential still has a launch document, so making the launch
ending a dependent of the credential ending would have left it unended in
exactly the case where nothing else would notice. One listing, two named
endings.

### [P1] The describe answer contradicted the pin

I stripped the schema member and answered three, on the argument that the
version is the program's business. That is a plausible proposal and it is not
the recorded decision: the pinned finding says the sorted member names of the
validated DOCUMENT, and that document has four. The ruling wins over my
preference. An operator reading describe now also sees which generation the
container was launched under, which is worth having.

### [P2] Stale prose and dead test bodies

The module contract still said 0400 under 0500. And
test_lifecycle_composition carried a byte-identical duplicate of five method
definitions, so the later block silently replaced the earlier one -- which is
how my own edit to test_the_adapter_starts_a_worker_that_actually_runs landed
in both a live and a dead body without my noticing. The duplicate block is
gone and the file now has no repeated method name in any class, checked
structurally rather than by eye.

### Gates

- test_oci 99, test_launch 22, test_credentials 80, test_worker_image 103
- the launch-document harness -- **24 of 24 mutations caught**, five of them
  new: the requested-versus-established mode, a start permitted without a
  document, a launch root never ended, one discarded without proving absence,
  and a describe reporting fewer members than the document has
- tools/parallel_test.py -- 1555 tests, **6 failures, all in
  test_boundary_inventory**, the accepted baseline and none this Work's
- --phase serial -- 105 tests, 0 failures, including
  test_lifecycle_composition 26 and test_worker_container 50 on a real daemon

No version-control history or index was mutated.

## 2026-08-28 - the missing-launch refusal, corrected

Reclaimed W26291 at seq 30187. One finding, and it is a consequence of a
sentence I wrote in the previous correction.

### The comment that was true in isolation

I placed the missing-launch refusal above the attempt checks and wrote beside
it that nothing had been created yet, so there was nothing to settle. That is
true only when no OTHER provider has materialized anything. A canonical
adapter may already hold a credential delivery whose volatile root and live
registration exist before start is ever called -- so the refusal stranded a
bearer on a path with no runtime id for the ordinary destroy crossing to name,
which is exactly the W26284 invariant this manager was corrected for once
already. Reproduced on the tree before touching anything:

    refusal=policy/denied
    engine_calls=0
    credential_root_present=True
    bearer_live=True

### Where it goes instead, and why the placement is the decision

It refuses through the settlement now, and it sits AFTER both attempt checks.
That ordering is the whole content: the settlement asks which runtimes carry
THESE labels, so a delivery belonging to a different attempt has to refuse
above it -- an empty answer about attempt 2 says nothing about attempt 1's
runtime, and acting on it would be inferring absence from the wrong question.
A same-attempt delivery is settled; a mismatched one is refused untouched and
without asking the engine anything.

The property the first re-review asked for survives where it applies: an
adapter with neither delivery still reaches no engine, because the settlement
answers not-delivered for both without listing when there is nothing to
settle.

After the fix the reproduction reports engine_calls=1 -- the settlement's own
listing, which is a read rather than a create.

### Two things the measurement caught that I had not

The harness reported the settlement-bypass mutation as UNSEEN. Not because
the guard was unestablished, but because the cases covering it live in
test_credentials and the harness did not run that suite: the launch document
and the credential delivery settle together on a refused start, so the module
list was wrong. A mutation nothing runs is not measured.

It also reported the older missing-document mutation as a stale 0x anchor
rather than silently mutating something else, because the correction moved the
line it named. Both are fixed and the harness is 25 of 25.

Each of the three new regressions was run against the pre-fix placement before
being trusted, and all three fail there -- including the mismatch case, which
fails because the old placement refused for the missing document instead of
the mismatch.

### Gates

- focused test_launch, test_oci, test_credentials, test_worker_image -- 307
- the launch-document harness -- **25 of 25 mutations caught**
- tools/parallel_test.py -- 1563 tests, **6 failures, all in
  test_boundary_inventory**, the accepted baseline and none this Work's
- --phase serial -- 105 tests, 0 failures on a real daemon

One note on a gate I had to re-run: the first serial attempt failed three
cleanup-hygiene cases because I had left the mutation harness running against
the same daemon, and both build the same reference image tags. That was my
scheduling mistake rather than a defect; re-run alone, the serial phase is
clean.

No version-control history or index was mutated.

## 2026-08-28 - the listing-failure gap, closed

Reclaimed W26291 at seq 30394. One [P2], and it is a real distinction I had
collapsed.

### Two branches, and I had covered only one

The second review asked for combined missing-launch/credential regressions for
proved absence AND an uncertain listing. I added proved absence, attempt
mismatch, and a listing that SUCCEEDS and returns a surviving runtime -- and
called that the uncertain case. It is not. A successful listing with a row is
the adapter INFERRING possible use from something the engine really said. A
listing that fails is the adapter knowing nothing at all, and it reaches a
different branch: `_undelivered` catching a ContractRefusal from `self.list`.

The new case drives that branch in three spellings -- the engine refuses the
listing, the answer is not readable JSON, and the answer names no runtime this
manager can own. Each asserts the start refuses, the credential ending is
unresolved, the root remains and the bearer stays live. An inventory this
manager could not read is never proved absence, because tearing a credential
root down on it would be settling under a container nobody could rule out.

The surviving-runtime case stays beside it. Two branches, two cases.

### Measured before being trusted

With `why = refusal.message` changed to `why = None`, so an unusable listing
becomes proved absence, the new case fails in all three spellings. The harness
gained that exact mutation, which is one the existing `if not proved_absent`
mutation cannot reach -- it measures the common launch-ending branch, while
this one measures whether a failed listing arrives there at all.

### Gates

- test_credentials 84, focused set 308
- the launch-document harness -- **26 of 26 mutations caught**
- tools/parallel_test.py -- 1564 tests, **6 failures, all in
  test_boundary_inventory**, the accepted baseline and none this Work's
- --phase serial -- 105 tests, 0 failures on a real daemon

No version-control history or index was mutated.
