# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — the ruling's premises revalidated; the pass not started

Claimed W6 at seq 33767. **No production code was edited.** No Git history or
index was mutated.

### The approver ruling holds on the tree

- the register at `…/finding-worker-runtime-conformance/evidence/cases.json`
  holds **136 cases, 135 applicable to `local-oci`**;
- all three superseded-topology cases are still present and still applicable;
- the register carries no `core` flag on any local-OCI case, so the original
  acceptance's derived core verdict has no field to derive from.

### Not started, and returned as one round rather than a fragment

Selecting the compatible subset means deciding, for each of 135 cases,
whether W6636's arc genuinely observes its `required_facts`. A partial
classification is the looks-complete-measures-less defect this campaign has
corrected repeatedly.

## 2026-08-28 — the ruled bounded capability pass, RUN

Claimed W6 at seq 33792. **No production source was changed by this round**;
the mutation harness rewrote four files in place and restored each one, and
"the tree is as it was found" below is the check. No Git history or index was
mutated.

### What was built

`evidence/w6-conformance-seal.py` — the seal and assessor harness. It

- imports the **frozen** `conformance_model.py` from its own dossier rather
  than carrying a copy, so the rules cannot be edited by the thing they judge;
- binds **16 files** by content digest: the register, obligations, model and
  schema; W6636's composition evidence, mutation harness and composition
  suite; the six manager modules the arc crosses; and the worker recipe,
  program and scripted agent;
- subclasses W6636's own `Composition` fixture, so the arc under measurement
  is the accepted one rather than a second fixture wearing its name;
- drives **ten probes against a real Docker daemon (29.1.3)** and emits
  MEASURED facts — no fact is written as a literal;
- refuses its own selection unless a case's exact `required_facts` and exact
  `deciding_evidence` purposes are all present, and
- derives every verdict with the frozen `assess`, never with its own
  judgement.

`evidence/w6-seal-mutations.py` — the same measurement W6636 was held to.
Eight guards removed one at a time from production source; each affected
verdict re-derived; each file restored and digest-checked.

### THE FORMAL RESULT

    VERDICT: not-certified
    2 portable core case(s) failed

    observed and passed   8
    observed and FAILED   2
    observed, undecidable 0
    NOT OBSERVED        125   — every one named in the transcript

Three of the 125 are named as conflicting with the approved direct
claim-to-one-container topology. **That set is derived rather than listed**: a
case conflicts when its expectation reads a fact only a consent runtime can
produce. The derivation independently returns exactly the three the finding
names, which is a check on the finding rather than a restatement of it.

### THREE COMPOSITION DEFECTS THIS PASS MEASURED, AND NO SUITE COULD SEE

Every one was found by reading and writing FROM INSIDE the started container.
W6636 inspects the daemon's account of the mounts; W6633's worker suite runs
without an `/input`; W19784 tests the documents as it writes them. Nobody
opens them as the worker.

**[P0] The worker cannot read either of its two `/input/` documents.**
Measured inside the execution container the manager composed:

    running as                    [65532, 65532]
    /input/assignment.json        mode 0o400  uid 1000  readable False
    /input/input.json             mode 0o400  uid 1000  readable False
    /run/baton/launch.json        mode 0o444  uid 1000  readable True

`workspaces.READ_ONLY_FILE` is `0o400`; `launch.READ_ONLY_FILE` is `0o444`.
The launch delivery got this right deliberately — `launch.py:36-51` says so in
prose, and a recorded [P0] review there fixed exactly this shape after a umask
turned a 0444 document into a 0400 one "the container's fixed uid could not
read". The same rule was never applied to the `/input` pair, and
`baton_worker.py:183-199` reads both of those documents.

**[P0] The worker cannot write its own workspace.** In the same container the
control write into `/workspace` — a bind the daemon reports read-write —
fails with `PermissionError` for the same reason: the root is the manager's
uid and the container is 65532.

**[P1] The conformance verdict already shows it.**
`A-assignment-manifest-delivered-read-only-beside-the-input` is derived
**FAILED**, because `input_pair_bindings_agree` is false, because the runtime
cannot read the pair to relate it. The failure is the defect, derived by the
frozen assessor from measured facts.

**These are not W6's to fix.** This Work's own boundary says it "does not
silently repair the implementations it certifies"; they belong to the owning
child as a bound finding.

### A SPECIFICATION CONFLICT, of the same class as the topology one

`C-decline-carrying-bearer-refused` is derived **FAILED**. The frozen suite
requires a decline that transmits the claim bearer to be refused
`integrity/schema` with the offer left un-terminated. v12's reviewed offer
boundary checks possession BEFORE branching on accept-or-decline
(`offers.py:484-498`), so a decline carrying the bearer **succeeds** and the
offer settles `declined`. Measured:

    refusal       = None
    offer_state   = 'declined'

Neither side is obviously wrong — single-use possession for every terminal
decision is a defensible rule — but they cannot both hold. Like the topology
conflict, this is a specification decision rather than a coding slip, and it
is not reviewer-owned.

### WHAT THE ASSESSMENT PATH ITSELF DOES, measured rather than assumed

`certify()` **refused this fixture before assessing any case**: it requires a
canary planted in every one of the ten named surfaces, and this pass plants
one (workspace) and says so. Behind that gate stands a second:
`MANDATORY_FAULTS_BY_PROFILE` requires all **21** fault capabilities for
`local-oci`. **The frozen suite admits no partial fixture at all.** A bounded
pass can either declare capabilities it does not have — the one move the
ruling forbids — or be refused at the door.

So the enumeration above is derived by calling the frozen `assess` and
`core_for` per case and applying §6's three-line disjunction to their output.
Every input to the verdict is the frozen assessor's; only the disjunction is
restated, and the transcript says so where it happens.

### MEASURED BY REMOVAL

    caught 5 of 8

    [caught] store: a reused operation id with another signature is not a collision
    [caught] output: the freeze does not hold the attempt to the live generation
    [caught] oci: `retain` does not keep the material
    [caught] oci: the canonical checkout is mounted into the runtime
    [caught] manager AND adapter: neither holds the mount to the proved root

    survives by design (a second guard refuses the same case; removing BOTH
    does flip the verdict):
      attempts: the declared plan is not held to the authorized root
      oci: the ADAPTER's own seam does not hold the mount to the proved root

    NOT CAUGHT:
      oci: the input root is mounted writable  (A-input-is-read-only)

**The survivor is a real limit and is recorded as one.** With `/input` mounted
WRITABLE the case still passes, because the write is then denied by ownership
(`EACCES`) instead of by the bind (`EROFS`). So in this composition that
verdict does not establish the read-only bind — it establishes only that the
write fails. The unmutated run's `input_write_denied_by` is `[Errno 30]
Read-only file system`, which is why the case is honestly `passed`; the
mutation is why it is not honestly evidence for the bind.

### Two probe defects the mutation harness caught, and both were mine

- `mounted_source_is_authorized` was written as the literal `False`. A fact
  the OBSERVER supplies is not an observation, and removing both production
  guards left the case passing. It is now derived by comparing the plan's
  declared `/input` source against the authorized root through
  `oci.canonical_source`.
- the stimulus mounted a directory outside the assignment entirely, which
  `oci._mounts` refuses by CONTAINMENT before either authorized-root guard is
  reached — a third rule deciding the case. The source is now a descendant of
  the assignment's own input root, so the guards under test are the ones that
  answer.

Two more were caught by printing values before pinning them: the authority
probe named `/tmp` (every image has one) and the decline probe declined an
already-accepted offer. Every correction is commented at the site.

### The tree is as it was found

    oci.py       4a8f1d05c19f67ce -> mutated -> 4a8f1d05c19f67ce
    attempts.py  ae8ce0e79d6c88db -> mutated -> ae8ce0e79d6c88db
    store.py     5ae622902a3ae2d6 -> mutated -> 5ae622902a3ae2d6
    output.py    a8eb2433dca2a543 -> mutated -> a8eb2433dca2a543

Asked of the engine afterwards: no container carries this composition's mark,
and this pass's image was removed by its own class cleanup. One
`baton-w6636-lifecycle` image from an earlier round, five hours older than
anything here, survives on the host; it is reported rather than removed,
because deleting another round's artefact is not this pass's call.

### Gates

- `evidence/w6-capability-pass-2026-08-28.txt` — the full transcript, 10
  probes green against Docker 29.1.3
- `evidence/w6-mutation-measurement-2026-08-28.txt` — the removal measurement
- `evidence/w6-seal/` — the sealed fixture, run, observations and every
  per-case artifact, each bound by content digest
- full v12 parallel source — **6 failures, every one in
  `test_boundary_inventory`**, which is the accepted baseline unchanged;
  checked by name and not only by count:
  `test_the_universe_sees_every_persisted_column_that_is_read`,
  `test_every_declared_probe_reaches_its_named_boundary`,
  `test_every_owned_entry_has_exactly_one_probe`,
  `test_the_missing_probe_check_can_actually_fail`,
  `test_every_boundary_call_belongs_to_an_entry_or_is_declared`,
  `test_every_receiving_entry_has_an_owning_validator`

## THE SEPARATE CONCLUSION THE RULING ASKS FOR

Stated apart from the verdict, and it is not a certification claim.

**The design is promising. The assessment path is promising with one named
structural defect.**

Promising, on this evidence: a frozen register the harness could not edit, a
fixture and run sealed by digest, and an assessor that took no verdict from
the observer derived — from facts measured on a real daemon — a
`not-certified` result, TWO failures nobody had reported, and a defect that
had survived three component suites and eleven review rounds. That is the
machinery working as intended: it found something against its own author's
interest, and it named it.

Not yet certifiable, and the reason is structural rather than incidental: the
suite is **all-or-nothing at the fixture door**. A fixture that cannot inject
all 21 faults and plant all 10 canaries cannot be assessed at all, however
many cases it could honestly decide. That makes incremental conformance
impossible and rewards a fixture that overstates itself — the one failure mode
a conformance suite must not reward. Admitting a fixture with declared
capabilities and deriving `unable` for cases beyond them (machinery
`faults_available` already has) would keep every guarantee and remove the
incentive.

## State

**Not integration signoff, and not a certification.** Passed back for
independent review with the ruled bounded pass complete: sealed, assessed,
published `not-certified` with all 125 unobserved cases named, and the
promising/not-promising conclusion stated separately.

Three findings need owners and none is W6's: the two ownership [P0]s on the
`/input` pair and the workspace, and the decline-carrying-bearer
specification conflict.

## 2026-08-28 — review 2026-08-28T20:28:19Z: revalidated, and one finding against myself

Claimed W6 at seq 34215. **No Git history or index was mutated.** The review
raised no finding against the pack and asked for W6 to be relinquished with its
stated Docker-gate limitation, so no implementation was started.

### The pinned decision, revalidated against the current tree

Docker 29.1.3 is reachable from this deployment, so the seal was re-run. **One
sealed input has moved since the reviewed run, and exactly one:**

    w6636:workspaces
      reviewed: 37299 bytes  sha256:16b48b6f…e07d580e
      now     : 39843 bytes  sha256:0e2e24ef…1fa8b07c

The other fifteen are byte-identical. That single move is `W33935`, which fixed
the unreadable `/input` pair this pass found.

### AND THE VERDICT MOVED WITH IT, which is the strongest evidence in the pack

Re-run against the current tree, the frozen assessor now derives:

    A-assignment-manifest-delivered-read-only-beside-the-input   PASSED
    (it was FAILED in the reviewed run)

    VERDICT: not-certified — 1 portable core case failed
    observed and passed 9, FAILED 1, undecidable 0, NOT OBSERVED 125

The remaining failure is `C-decline-carrying-bearer-refused`, the offer-contract
conflict parked as `W33937` and awaiting an approver decision. Nothing else
changed.

**This is the promising-design conclusion, measured rather than argued.** The
conformance machinery derived a failure from facts nobody had reported; the
failure became its own Work; the fix landed; and the same frozen assessor,
unedited, now derives the corrected verdict from a re-measured arc. That is the
loop working end to end.

### AN OPERATIONAL FINDING AGAINST MYSELF

**Re-running the harness overwrote the reviewed evidence pack in place.**
`evidence/w6-seal/` was a fixed path, so the second run replaced the report the
independent review had verified by digest:

    reviewed: 36491 bytes  sha256:6dea05a4…49c55ad5   (verified by the review)
    written : 36494 bytes  sha256:82fc922b…7f75d6fb   (the re-run)

**The earlier bytes are unrecoverable.** I looked: `/tmp/w6-review-rerun` holds
only the reviewer's own attempted rerun, which stopped at Docker fixture setup
and contains zero assessed cases, so it is not a restore source.

What survives is not nothing: the reviewed transcript
`evidence/w6-capability-pass-2026-08-28.txt` was written to a separate file and
is intact, and it records every artifact's byte count and SHA-256 — so the
reviewed pack remains fully DESCRIBED by digest and the review's own
verification of it stands. What is gone is the bytes.

**Retaining immutable evidence is this Work's own acceptance, and a harness
that can destroy its own retained evidence by being run twice does not retain
anything.** So the harness is corrected rather than the incident merely
reported:

- the pack is written under a run name — `w6-conformance-seal.py <run-name>` —
  and the name is an operand rather than a timestamp, because this module may
  not read a clock and a harness that silently invented a new directory every
  run would hide a caller who meant to reproduce an exact one;
- `artifact()` REFUSES rather than overwrites when a file of that name already
  holds different bytes, and the refusal names the remedy. Measured: re-running
  into `w6-seal-2026-08-28b` exits non-zero with
  `OPERATIONAL FINDING: … already holds a different run's bytes`.

The two runs are now separate and named: `evidence/w6-seal-2026-08-28b/` with
`evidence/w6-capability-pass-2026-08-28b.txt` is the re-run; the reviewed run's
transcript keeps its original name.

### The review's own limitation, unchanged and not mine to resolve

The independent reviewer is denied `/var/run/docker.sock` and standing
non-interactive policy forbids escalation, so no second end-to-end Docker
execution was performed by an independent party. This deployment CAN reach the
daemon, but a rerun by the implementer is not independent verification of the
implementer's own pack, and saying otherwise would be exactly the conflation
the review warns against.

## State

**Relinquished for approver disposition**, with the reviewer's limitation
raised on T6 as an obligation on `baton.decide`. W6 needs either an authorized
independent Docker verifier or a ruling that the sealed-pack validation the
review did perform is the disposition this vertical slice finishes on.

The bounded pass itself is complete and unchanged in substance; the re-run
strengthens it and is retained beside the original rather than in place of it.

## 2026-08-28 — the disposition, recorded

Claimed W6 at seq 34892. **No production source was changed this round.** No
Git history or index was mutated.

Approver M34887 ruled that the independent sealed-pack verification finishes
W6 without a second independent Docker execution. Four things the ruling
requires, each done and each verifiable:

**The result is recorded in the ruling's own terms** — a promising but formally
`not-certified` capability pass, never integration and never exhaustive
certification. `FINDING.md` says so in those words so a later reader cannot
take it for either.

**The reviewer's evidence is preserved as the substitute for the pack I
overwrote.** Their transcript is retained at
`evidence/w6-review-verification-2026-08-28.md` and their read-only verifier at
`evidence/w6-review-verifier.py`. Together with the reviewed run's own
transcript — which records every artifact's byte count and SHA-256 — the pack
is fully described by digest and independently verified. **Its bytes are
unrecoverable and I have not pretended otherwise.**

**The overwrite limitation is recorded explicitly**, with both digests named:
reviewed 36,491 bytes `sha256:6dea05a4…49c55ad5`, and a later run's bytes now
under that name.

**Named immutable packs are required, and the harness enforces it** —
re-validated this round: re-running into the reviewed pack exits non-zero with
the operational finding and the remedy named.

## State

**Disposition recorded. Passed back for independent review** rather than
closed, as the role requires. Independent Docker reproduction and exhaustive
current-register certification are later Work and are not claimed here.
