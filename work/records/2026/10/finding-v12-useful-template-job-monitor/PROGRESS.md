# Implementation progress

## claim366970 — the operator packet, and the four command lines it caught

Answers the bound `FINDING.md`, `PLAN.md` and `USEFUL-JOB.md` under thread
366962. **Preparation only**: no build, install, start, Job, owner act or
cleanup was selected or run; no source byte, deployment or configuration
changed. What I wrote is `COMMANDS.md`, `verify_commands.py`,
`evidence/claim-366970/` and this file.

Prepared against `42bed8bb04a53380e565b1a63fb2bc702677f0d0` — the integration
commit, verified present and checked out, so the create command the packet uses
is canonical rather than a candidate.

### The bound dossier was absent at claim, and then appeared

At claim E366970 the bound path carried **no `FINDING.md`, `PLAN.md` or
`USEFUL-JOB.md`**. I checked the path, searched the whole `work/` tree for the
slug and read `git status`: nothing. The parent W321608 was still claimed by
`baton.rvpc` (claimed 17:16:31Z, state `working`, last contact 17:19:42Z), so
the reviewer was mid-turn — it had created this Work and routed it to me while
still authoring its records.

Rather than return an empty turn or invent the acceptance, I did the
preparation the thread message fully specifies, re-checked the path before
sealing evidence, and **found all three files present**. I then read them and
revalidated. That reread changed the deliverable materially, which is the whole
reason for doing it:

- **the proposed Job is the reviewer's, not mine.** My first draft proposed
  editing `v12/QUICKSTART.md` and `v12/STACK.md` to add the missing
  `manager create` entry. The FINDING forbids exactly that: QUICKSTART
  describes **instance 4 at `614668e0`** and "must remain truthful; this Job is
  not permission to relabel that deployment". The Job now writes a new file,
  `v12/TEMPLATE-JOBS.md`, with the reviewer's task name
  `template-job-guide-42bed8bb`, its statement and its five acceptance
  criteria reproduced verbatim in both the packet and the verifier so they
  cannot drift into two statements about one selection.
- **the template version is named explicitly** rather than defaulted, and
  `--source installed` is stated, per `USEFUL-JOB.md`.
- **no dummy UUID.** My draft used `0…0a` as a placeholder. The FINDING
  forbids presenting one as an installed identity and the PLAN requires
  deriving it by supported readback. The packet and the verifier now drive
  `<read-from-$DEST/authority-identity.json>`, which parses and could never be
  mistaken for an identity, and §4 reads the real one back after install.
- **the archived bundle's compatibility is verified rather than assumed**, and
  the stamp is disclosed rather than relabelled (below).
- **runtime cessation is separated from stopping**, with the check to run
  before cleanup or any retry.

### What the packet is

Twelve ordered operator commands across install → admit → start → observe →
diagnose → dispose → stop, with the one-time installation boundary stated
against OBS-0a, a fresh destination, every derived path taken from
`tools/instance.py`, the proposed live bounds (provider 3600s / verification
900s per invocation, two stages, `report-and-hold`, no integration stage, no
discretionary retry, a bounded ~20-minute observation window), and the four
distinctions the FINDING insists on kept apart: implementation completion,
independent technical verdict, held proposal, and human acceptance/Git
integration.

### The archived bundle: compatible, and not relabelled

The FINDING required compatibility to be established before reuse could be
proposed. It is, by two independent checks that must agree:

- all **23 product source members** (`src/`, `tools/`) of `candidate-366250` —
  the candidate the W366246 bundle was built from — are **byte-identical to
  `42bed8bb`**; **0 drifted**;
- the integration commit's own product diff is **17 paths**, and **every one of
  them is a member of that candidate** — so no file is unaccounted for.

Either check alone would leave a gap. Together they establish that every
product source file the bundle carries matches the integrated commit; the 12
remaining members are tests, which `packaging/stack.spec` does not bundle, and
`v12/justfile`, which is a recipe. **Its embedded stamp still records
`18e771f0, dirty`** and `identity`/`--version` will keep saying so — disclosed
in §2, not corrected. The fresh-build alternative is given with its exact
commands for separate owner selection.

### The verifier, and the four lines it caught

`verify_commands.py` establishes, with no engine, provider, build, install or
run: that each subcommand is one `stack_command.COMMANDS` serves; that the
operands **parse through the product's own parser with the packet's own argv**
(`parse_args` is wrapped so it parses normally and then raises, so the real
parser runs and nothing past parsing executes); that the dispatch in between is
the product's, exercising `_stack`'s `--instance` lifting; that the four store
paths are the ones `instance.layout` derives; the archive comparison above; and
the prepared commit plus the sha256 of all eight product files the command
surface comes from.

**Exit 0, 12 commands checked, 0 failures.**

It earned its keep immediately: **four of the twelve command lines in my first
draft were wrong** and it caught all four before anyone ran them —
`record read` and `disposition pending` need
`--authority-store`/`--authority-uuid` rather than `--root` alone, and `logs`
takes `--logs <dir> --attempt <id>` plus a verb, not `--instance`. Those are
precisely the operand mistakes the earlier pilot command records made twice,
which is why the FINDING asked for deterministic checks rather than prose.

Deliberate limits: it does not check that a bundle exists, that an instance is
installed, or that any command *succeeds*. `identity` is checked by membership
alone — it takes no operands and builds no parser, and invoking it would be
running a command rather than checking one. `just` recipes are checked by name
against the real justfile.

### What is not established

No live provider authentication, no container start, no real model output, no
live startup latency, and no claim that this documentation Job would pass its
own review. W361912's startup figures are simulated-engine timing; its workflow
evidence is deterministic control flow over synthetic proposal and verdict
content and includes no completed correction plus second review. The open live
question — does the installed create command deliver the selected task to
independent implementation and review runtimes and expose it in the monitor —
is answerable only by an owner-selected run and is not fabricated here.

### Cost

Reading the bound FINDING/PLAN/USEFUL-JOB (after they appeared), the parent
FINDING's owner ruling and integration sections, the parent PLAN, the W321608
events through E366949, `v12/justfile`, `tools/stack_command.py`,
`tools/stack.py`, `tools/bootstrap.py`, `tools/job_manager.py`'s create
operands, `tools/attempt_logs_command.py`, `tools/dossier_command.py`,
`tools/disposition_command.py`, `v12/QUICKSTART.md` and the W366246 bundle
archive records. Verifier runs: four (one exposing the four wrong command
lines, one exposing that `identity` has no parser to reach, two clean). No
build, install, deployment, engine, provider, live run or Git mutation.

### Boundaries

No Git mutation; the only version-control calls were `rev-parse`, `log`,
`status`, `diff` and `cat-file`, all reads, two of them inside the verifier and
labelled as reads there. Product source, existing deployments and every
immutable historical artifact are untouched — `git status` reports no change
under `v12`. Instances 1–4 and the pilot packet's artifacts are preserved. The
bound `FINDING.md`, `PLAN.md` and `USEFUL-JOB.md` are the reviewer's and are
unmodified.

## claim367071 — the corrections, and the gap that stops the chain

Answers `review-2026-10-27T17-32-12Z.md`. **All three findings were right**,
including one that exposed a coverage gap I had created. Preparation only: no
build, install, start, Job, owner act, deletion or product change; the
repository reports no change under `v12`. The previous section and
`evidence/claim-366970/` are preserved as history; the corrected packet,
verifier and `evidence/claim-367071/` are this claim's.

### R2 first, because it is the one I should have caught

The previous verifier **held its own copy of the command list**, so the
no-drift guarantee I claimed for it was unsupportable — it checked the copy. It
tested `monitor --ticks 40` while the packet published `400`, and it **omitted
`attempt-diagnostics` entirely** — the one published command whose argv was
wrong. `tools/attempt_diagnostics.py` takes exactly one positional file and
exits 2 for `--status FILE`, which is what I published in §8 and §10.

The verifier is rewritten to **read `COMMANDS.md`**: it extracts the fenced
`sh` blocks, resolves the packet's own assignments, pulls every
`baton-v12-stack <sub> …` invocation out with `shlex`, and checks that text.
There is no second copy to drift. It also now does what it could not before:

- **shell syntax** — every block through `bash -n` with the packet's
  assignments in scope, so an unquoted placeholder fails. The previous draft's
  `--attempt <attempt-id from §5/§7>` was not a pasteable command; it is now
  `"$ATTEMPT"`.
- **parserless commands** — against an inert supported status document the
  check writes itself. `attempt-diagnostics <file>` exits **0** and
  `--status <file>` exits **2**, so the correction is driven rather than
  asserted. `identity` has no operands and no parser and is deliberately not
  invoked.
- **15 published invocations** extracted and checked, 13 blocks parsed,
  **0 failures**.

Writing that check cost me two more of my own errors, both caught by running
it: I guessed the status schema as `/1` when the owner says
`baton.v12.job-status/7` (now read from `documents.STATUS_SCHEMA` rather than
written down), and I redirected stdout around `attempt_diagnostics.main`, whose
`stream=` default binds `sys.stdout` at definition time — so its report landed
on the real stdout and corrupted the verifier's own JSON. `stream=` is now
passed explicitly.

### R1 — and the answer is a gap, not a selection

The review is right that `/REPLACE` is not a concrete selection and that
`v12/instance-inputs.json` has no workers. I now give a **concrete destination,
a concrete artifact and the real source arrangement** — and I also correct a
claim I had no basis for: I said `--no-repositories` suited a documentation Job
"because it needs no clone". It does need the source, because it must read
current source and produce an independently reviewed candidate, so the
installation uses `--repository-source`.

**But capacity cannot be selected from supported interfaces, and that is the
finding.** Reproduced by the verifier rather than described:

1. a fresh `bootstrap` configures none — `DEFERRED == ("jobs", "workers")`;
2. `DeploymentDerivation.derived` **refuses** with "this instance configures no
   'implementation' worker …", so ordinary `create` cannot be reached;
3. both supported ways to configure a worker **consume** a
   `baton.v12.single-worker-deployment/4` document that nothing composes —
   the bootstrap input's `workers[]`, or `tools/pool.py admit --worker`;
4. that document's `input_manifest.work_ref.authority_uuid` must equal the
   instance's own, and the identity is *generated at install* with
   `authority_uuid` refused as an input member — so it cannot even be written
   before the install exists;
5. `pool` is **not** among the 14 subcommands the deployed bundle serves
   (asserted by the verifier), so on an installed deployment the only supported
   capacity path is re-running `bootstrap` with a hand-composed document.

Every existing instance got those documents from a bespoke packet script or a
test fixture. So, per the FINDING's own instruction — "if current supported
installation requires prohibited per-run provisioning, record that concrete gap;
do not silently normalize it or implement a workaround" — **§2 records the gap
and stops**, with three owner options stated and none recommended: reuse an
instance with capacity (but instance 4 is bound to `614668e0`, where
`manager create` did not exist, so reuse means reinstalling at `42bed8bb` and
lands back here); select a supported one-time installation composer as new
product work; or explicitly authorise reuse of the pilot's existing authored
composer for one install.

**So R1 is answered as a gap, not satisfied as a selection.** Sections 3–10 are
complete and checked so that whichever option the owner picks, nothing else is
outstanding.

### R3 — the finite selection and the cessation procedure

- **What bounds what, stated.** The configured ceilings (3600s provider turn,
  900s verification, per invocation) are the only enforcement. `--ticks 400`
  bounds the *watching*, not the work, and the monitor enforces no run ceiling.
- **The correction gap, named.** A `changes-requested` verdict makes the
  product open a correction round by itself, and **there is no supported
  operand that caps the number of rounds**. Stated for owner choice: accept the
  further invocation, or select beforehand that the run is abandoned at the
  first such verdict. No host-side protocol write is invented.
- **A table with an action per state** — attempt running (keep observing; no
  supported cancel, same gap), cleanup pending (keep ticking), window ended
  (nothing wrong), all terminal and settled (cessation confirmed), held result
  (that is `report-and-hold` working). `stop` is still distinguished from
  cessation, and now the missing action is supplied.
- **Nothing is deleted.** The previous draft's "remove `$DEST`" conflicted with
  preserving evidence and is gone. Retention is step 1, before anything else:
  the create answer, both projections and the attempt log locators, which carry
  the Job/attempt/result identities and the OBS-0 endpoints a later reader needs
  — with W361912's figures labelled as simulated-engine timing.

### Verification

    python3 work/records/2026/10/finding-v12-useful-template-job-monitor/verify_commands.py

Exit **0**; **15 published invocations, 15 checked, 0 failures**; 13 shell
blocks parsed; `attempt-diagnostics` 0/2 as documented; the no-capacity refusal
reproduced; `pool` confirmed unserved; archived bundle product-compatible with
`42bed8bb` (23 members compared, 0 drifted, 17 integration paths all
accounted for) with its `18e771f0` stamp disclosed and not relabelled; the
packet's own digest recorded in the result. Retained at
`evidence/claim-367071/verification.json`.

**Its limits, unchanged in kind:** it does not check that a bundle exists, that
an instance is installed, that **capacity is configured** — §2 says it cannot
be — or that any command succeeds. Passing means the published text is
syntactically and structurally sound, not that the sequence is runnable today.

### Cost

Reading the review and its four evidence files, `bootstrap.DEFERRED`/
`SUPERSEDED`/`_WORKER`, `creation_ports.DeploymentDerivation.derived`,
`tools/pool.py`, `tools/attempt_diagnostics.py`, `job_viewer.read_snapshot` and
`documents.STATUS_SCHEMA`. Verifier runs: five — one exposing the wrong status
schema, one the stdout binding, three clean. No build, install, deployment,
engine, provider, live run or version-control mutation.

### Boundaries

No version-control mutation; the only such calls were `rev-parse`, `log`,
`status` and `diff`, all reads, two inside the verifier and labelled there.
No secret, credential or token appears in the packet or in any output it
proposes. Product source, existing deployments and every historical artifact
are untouched. `FINDING.md`, `PLAN.md`, `USEFUL-JOB.md`, the review and
`PLAN-HISTORY-367054.md` are the reviewer's and are unmodified.

## claim367146 — three truthfulness corrections in; R1 reframed and unfinished

Answers `review-2026-10-27T17-42-27Z.md`. **The reviewer corrected my central
judgement and was right**: preparing actual one-time installation inputs is
already authorized by the bound FINDING and PLAN, so my "record the gap and
stop" answer to R1 was a conclusion drawn too early. Preparation only: no
build, install, start, Job, owner act, deletion or product change; the
repository reports no change under `v12`. Previous sections and
`evidence/claim-366970/`, `evidence/claim-367071/` are preserved; this claim
wrote the revised `COMMANDS.md`, the extended `verify_commands.py`,
`evidence/claim-367146/` and this section.

### What I got wrong, and withdrew

**R1.** §2 said ordinary `create` "cannot be reached from a supported fresh
installation" and offered three unevaluated owner options. The empty-worker
refusal I reproduced is real, but it proves the *empty sample* insufficient —
not that no one-time configuration can be prepared here. The FINDING and PLAN
authorize preparing actual installation inputs and commands; they forbid
product changes, actual installation and bespoke per-Job admission, and
adapting an existing reviewed composition is none of those. **The claim that a
composer must be new product work is withdrawn.** §2 also compounded the error
by calling sections 3–10 "complete" while the chain could not reach §5; that
sentence is gone.

**R3a.** §8 said the run could be "abandoned at the first `changes-requested`
verdict" through §10. **That was false.** The product opens the correction
round itself, and §10 only observes until attempts are terminal — by the time
an operator reads the verdict the next invocation may already be running.
Observing and waiting cannot enforce a round limit.

**R3b.** §10 claimed the retained outputs carry the OBS-0 endpoints. No field
supports it: `documents.STATUS_SCHEMA`'s `observed_at` is **query time**, and
worker visibility deliberately separates bytes-observed from progress and
query time from contact.

**R3c.** §9 taught a universal operand set for `approve`/`deny`/`integrated`/
`close`. The parsers contradict it.

### What this revision delivers

**§2 now recommends the shortest supported prepared path** and locates its
inputs precisely instead of deferring: `fresh5-361402/configure-inputs.json`
carries the phase-2 document with **both lanes** as complete
`baton.v12.single-worker-deployment/4` deployments; `fresh3-358443/fresh.py`
is the accepted preparer whose `_compose` rebinds `authority_uuid`,
`input_manifest` and `task_document` onto a minted identity and whose
`static_refusals`/`mint` already enforce a worker-less phase 1; `fresh5.py` is
the parameterised entry with a read-only preflight and a separate
`--owner-selected` apply. It states exactly what must be rebound — destination,
bundle, source commit `42bed8bb`, the Job/submission/task identities, the
per-worker derived paths and the credential references — and records that
**no concrete supported operation failed**.

**§8 states the unresolved execution decision instead of an unimplemented
control.** The per-invocation ceilings remain the only enforcement and the
monitor window still bounds only the watching. `Authority.cancel` is named
honestly from `v12/QUICKSTART.md` — it fences the assignment, leaves the Work
`open` with no outcome and leaves the runtime-quiescence gate surviving at the
cancelled assignment's own generation — together with the three reasons it is
not a prepared control here: it is not an installed subcommand, it cancels an
assignment rather than a correction policy, and any use needs execution
selection. The owner's two honest options are stated; no host-side protocol
write is invented.

**§10 labels the endpoints unknown.** The live OBS-0 interval is **not
measurable from this procedure and no live OBS-0 result is claimed**. What is
retained instead is raw timestamped evidence with its source association — the
shell transcript of the §5/§7 invocations, each projection with its own
`observed_at`, and the attempt log locators — plus the Job/attempt/result
identities, which the outputs really do carry.

**§9 carries the actual verb contracts**, as a table the verifier holds to the
parsers: `pending` requires nothing beyond the common operands; `approve`/
`deny` require the proposal, candidate digest, review, policy generation and
approval id; `integrated` requires a **different** set with no
`--expect-review`; and `close` requires only `--outcome` and `--rationale`,
with the candidate operands optional because a non-satisfying outcome needs
none of them.

### The verifier gained a contract check — and it caught my first cut

`disposition_contracts` drives each owner verb through its real parser and
reads the required operands out of argparse's own "the following arguments are
required" clause. My first cut regexed every `--option` out of the whole
message, so the **usage line's bracketed optionals** made `close` look as
though it required the candidate operands it does not — the exact error the
table was meant to correct. Caught by running it against the parsers.

### Verification

    python3 work/records/2026/10/finding-v12-useful-template-job-monitor/verify_commands.py

Exit **0**; **15 published invocations, 15 checked, 0 failures**; 13 shell
blocks parsed by `bash -n`; `attempt-diagnostics` 0 positional / 2 for
`--status`; the no-capacity refusal reproduced; `pool` confirmed unserved; the
five owner-verb contracts read from their parsers and held against §9; the
archived bundle product-compatible with `42bed8bb` with its `18e771f0` stamp
disclosed; the packet's own digest recorded. Retained at
`evidence/claim-367146/verification.json`.

### What remains — exact scope

**One piece of R1 is unfinished and is reported rather than papered over:** the
rebound phase-2 capacity document for this destination, and the inert
composition check that its emitted identity binding satisfies
`DeploymentDerivation.derived` for both lanes and the selected task. The path
is established (§2 above), the technique for the inert check is the reviewer's
own `__new__` + `held` stub from `evidence/review-367054/EMPTY-WORKERS.json`,
and the obstacle is only that `DeploymentDerivation` reads an *emitted*
`deployment.json` — which `bootstrap.prepare` writes and which this
preparation may not run — so the owned configuration has to be obtained through
`stage_execution.held_configuration` on a composed document instead. That is
the next turn's work and I ran out of turn budget before it could be done
correctly; a half-composed document presented as ready is the failure mode
this review has already corrected twice.

### Cost

Reading the review, `disposition_command`'s five verb parsers, `_close`'s
asymmetry, `attempt_diagnostics`, `fresh5.py`, `fresh3-358443/fresh.py`'s
`prepare`/`_compose`/`static_refusals`, the pilot's `configure-inputs.json` and
`install-inputs.json`, `creation_ports.DeploymentDerivation`, `tools/pool.py`
and QUICKSTART's cancellation section. Verifier runs: three — one exposing the
usage-line contamination, two clean. No build, install, deployment, engine,
provider, live run or version-control mutation.

### Boundaries

No version-control mutation; the only such calls were `rev-parse`, `log`,
`status` and `diff`, all reads, two inside the verifier and labelled there. No
secret, credential or token appears in the packet or in any output it proposes.
Product source, existing deployments and every historical artifact are
untouched; instances 1–4 and the pilot packet are preserved and were read
only. `FINDING.md`, `PLAN.md`, `USEFUL-JOB.md`, both reviews and the PLAN
history are the reviewer's and are unmodified.

## claim367196 — the §9 contract fixes, one measured ordering fact, and what is still owed

Answers `review-2026-10-27T17-49-13Z.md`. Preparation only: no build, install,
start, Job, owner act, deletion or product change; the repository reports no
change under `v12`, and the proposed destination was never touched. Previous
sections and `evidence/claim-366970/`, `claim-367071/`, `claim-367146/` are
preserved; this claim wrote the revised §4 and §9, the extended verifier,
`evidence/claim-367196/` and this section.

**The capacity composition is still not delivered.** That is the third turn in
which it is outstanding, and I am not going to dress that up.

### What is delivered

**§9's contract table is now right, and machine-checked.** The review caught
that my second draft fixed the operand sets but still put `--participant` and
`--operation-id` in a "shared requirements" heading while marking `pending`'s
participant optional — two statements about one contract. The table now gives
each verb exactly what its parser requires, with `pending` shown as needing
only `--authority-store --authority-uuid --work`, and the verifier **asserts**
that `pending` requires neither of the two operands the old heading implied.

**The closure vocabulary is now the product's own closed set**, read from
`authority.core.INTAKE_OUTCOMES` by the verifier rather than written down:
`satisfying`, `non-satisfying`, `rejected`, `cancelled`. Only `satisfying`
requires the acceptance chain. "Denied" and "abandoned" describe situations and
are **not** `--outcome` values — the verifier fails if the packet presents them
as such — and `--expect-assignment` carries the assignment identity a closure
ends where one is live, so assignment fencing still applies.

**One hard ordering fact, measured rather than assumed.** Taking up the
review's clarification that `bootstrap` against disposable private fixtures is
within verification scope, I drove phase 1 inertly against a disposable
`/var/tmp` destination. It refuses the **identity mint itself** without a
runtime:

    refused: installing into <destination> needs a built runtime; name it with
    --distro, or build one with `just build` from v12/.

So §3's artifact step **strictly precedes even the mint** — a procedure that
minted first and chose the bundle later would be refused at the first command.
§4 now states that with the exact message. Recorded at
`evidence/claim-367196/phase1-prerequisite.json` with the probe beside it; the
disposable destination was removed and nothing else was written.

### What is still owed, and the design is now settled rather than searched

The rebound two-lane capacity document and its connected inert composition
proof. What this turn established, so the next one does not re-derive it:

* the pilot's `configure-inputs.json` is a **pre-composition template**, not a
  finished document — `work_id` is literally `COMPOSED(<minted uuid[:8]>-W1)`
  and `input_manifest` is a placeholder string. So the adaptation is to drive
  the pinned composition, not to text-rewrite a document;
* `fresh3-358443/fresh.py:_compose(packet, destination, uuid, *, task=None,
  document=None)` is **already parameterised** on exactly the two things that
  must change: it accepts an overriding task and an overriding template
  document, seals the manifest through the pinned
  `post-install-357462/configure.py:sealed_manifest`, rebinds each worker's
  `authority_uuid`/`input_manifest`/`task_document`, fills the Work id from the
  minted uuid, refuses any unresolved `COMPOSED(` marker, and cross-binds
  document, manifest and submission. That is the seam to use;
* `fresh.py` imports cleanly from the packet directories (verified this turn);
* the proof shape is: materialize the artifact → phase-1 mint into a disposable
  `/var/tmp` destination → `_compose` with the rebound template and task →
  phase-2 `bootstrap.prepare` there → `DeploymentDerivation(root).derived(
  selection)` asserting both lanes bind the same minted authority, stay
  independent participants, and answer the selected task.

**The one prerequisite I did not satisfy this turn** is materializing the
artifact for that disposable run: the W366246 archive is a 15 MB tarball in
that Work's evidence, and extracting it is permitted (it is not a build), but I
reached the end of my turn budget at the phase-1 refusal above rather than
part-way through an unverified chain.

### Verification

    python3 work/records/2026/10/finding-v12-useful-template-job-monitor/verify_commands.py

Exit **0**; **15 published invocations, 15 checked, 0 failures**; 13 shell
blocks parsed; `attempt-diagnostics` 0 positional / 2 for `--status`; the
no-capacity refusal reproduced; `pool` confirmed unserved; the five owner-verb
contracts read from their parsers and held against §9; the closure vocabulary
read from `INTAKE_OUTCOMES` and held against the packet; the archived bundle
product-compatible with `42bed8bb` with its `18e771f0` stamp disclosed; the
packet's own digest recorded. Retained at
`evidence/claim-367196/verification.json`.

### Cost

Reading the review, `authority.core.INTAKE_OUTCOMES`, `disposition_command`'s
`_close`, the pilot's `configure-inputs.json` and `install-inputs.json`, and
`fresh.py`'s `_compose`/`composed`/`install_and_configure`. Runs: one inert
phase-1 probe (exit 2, the ordering fact) and two verifier runs. No build,
install of the proposed destination, deployment, engine, provider, live run or
version-control mutation.

### Boundaries

No version-control mutation; the only such calls were `rev-parse`, `log`,
`status` and `diff`, all reads, two inside the verifier and labelled there. No
secret, credential or token appears in the packet or in any output it proposes.
Product source, existing deployments and every historical artifact are
untouched; instances 1–4 and the pilot packet were read only. The disposable
`/var/tmp` destination created by the probe was removed. `FINDING.md`,
`PLAN.md`, `USEFUL-JOB.md`, all three reviews and the PLAN history are the
reviewer's and are unmodified.

## claim369970 — the packet consumes the accepted child; §§2–5 rewritten

Answers `review-2026-10-28T00-39-27Z.md`. W367232 closed **satisfying** at
owner E369951, the parent artifact freeze is lifted, and the one milestone is
to make this packet's published commands and dataflow coherent with the
accepted child instead of describing capacity as undelivered.

**Prerequisites re-verified at claim start, read-only** — nothing proceeds on a
digest I did not re-derive:

    HEAD                        42bed8bb04a53380e565b1a63fb2bc702677f0d0
    child binding               92d9962a…3765723   (claim-369373)
    selected default inventory  6ae52f7b…3284add
    selected task               c21e6b93…6bd98d7   proposed_format false
    8 delivered child artifacts  all SAME
    7 default-set members        all SAME

### §2 — the gap is closed, and the selection is cited rather than encoded

§2 used to report the capacity document as outstanding scope and recommend
adapting `fresh3-358443/fresh.py`. Both are gone. It now names what to consume
by digest: the child record, its accepted binding `92d9962a…`, and the three
entrypoints this packet actually invokes — `capacity.py preflight`,
`materialize`, `compose`. Its proofs are reused, not reconstructed.

The owner's ruling is quoted with its digests — inventory `6ae52f7b…`, task
`c21e6b93…`, formatting **not** selected — and **the bytes are left alone**.
All seven proposal files still read `status: "proposed-not-granted"` and
`authorized_by: null`, and §2 says in so many words why this packet does not
"fix" that: the selection record is the owner's FINDING entry, and a packet
that edited those files to look granted would be manufacturing the ruling it
is supposed to cite. `compose` keeps answering
`preparation_is_complete: false` for the same reason.

A new table separates **selected** (the configuration basis) from **still a
prerequisite** (the image on the host; the credential reference resolving),
**not demonstrated** (any egress restriction — naming `bridge` is not a
ruling), **covered by the ruling** (prompts disabled inside the worker
environment), and **not selected at all** (execution).

### §§3–4 — the sequence is now the one the child proved

    §3 materialize → §4 mint only → read back → compose + stage the task
       → ONE destination install → §5 ordinary input-only create

**Two outright corrections, both mine.**

1. §4 published a destination install and then a **second** `bootstrap` run to
   add workers. The second run is refused — a destination holding a runtime is
   not upgraded in place — so the shape is replaced with mint-only, readback,
   compose, one install.
2. §4 claimed the artifact "strictly precedes even the identity mint". That
   overgeneralized a **destination-install** refusal. `bootstrap --inputs
   <file>` alone takes no `--distro` and needs no runtime; the child's `_mint`
   does exactly that. §3 still comes first, but because step 4 needs
   `$DISTRO` — not because minting does.

§3 now extracts the runtime with `capacity.py materialize --into "$DISTRO"`,
which holds it to *both* pins and refuses a path it did not create. `$MINT`,
`$COMPOSE` and `$PHASE2` are declared **outside `$DEST`**, with the reason:
the mint writes the destination's own `install-inputs.json` slot and a staged
copy sitting there makes step 4 refuse.

**The dataflow is explicit.** A table maps each member of the compose answer
to the command it feeds — `document` → `$PHASE2`; `task_bytes` →
`installed_task.place`, written *before* the install because the installer
opens it; `work_id` → `$WORK`; `manifest_digest`/`document_digest` → the
installation's recorded identity — and §5 says what
`$DEST/deployment.json` supplies it: the two servable lanes, the one shared
input identity, and the installed task whose `task_id` is the `--task`
operand.

### The simulated-source boundary, kept where it belongs

The child installed with `--no-repositories` and two **empty** nominated
source directories, labelled as its one test substitution. §4 step 4 states
plainly that this is correct for an inert proof and **wrong for this Job** — a
documentation Job must read current source — so the packet publishes
`--repository-source /home/sl/src/baton`, and §12 records that a real source
tree is an *execution prerequisite* rather than something that proof
established. The verifier fails if `--no-repositories` ever appears on the
destination install.

### Five checks added to the verifier

`verify_commands.py` (schema `/3`) keeps its no-second-copy property — it
still reads `COMMANDS.md` — and gains:

| check | what fails it |
| --- | --- |
| child helpers parse | a published `capacity.py` operand its own parser does not serve. `$UUID` gets a **declared** stand-in, reported in the answer, because it exists only after the mint |
| install sequence | more than one mint, a mint carrying `--destination`/`--distro`, more than one destination install, a missing `--repository-source`, or `--no-repositories` on the install |
| owner selection | inventory/task digest mismatch, the formatted variant, digests the packet does not publish, drift from the child binding, **or any proposal file no longer saying it is ungranted** |
| two lanes | roles, participants or principals not distinct; more than one input identity; `compose` writing anything; `preparation_is_complete` not false |
| refusals | the mismatched-set binding or the occupied materialization target not refusing |

**Result: exit 0, 0 failures, 16 published invocations checked, 2 child-helper
invocations parsed.** The install sequence reads exactly one mint
(`--inputs <file>`) and one destination install with `--repository-source`. The
lanes read `{implementation: rview, review: owner}` with two participants, two
principals and one shared input digest. All seven proposals still
`proposed-not-granted`.

### Verification and cumulative spending

This claim: 4 verifier runs (the last recorded), one read-only prerequisite
re-hash of the child's 8 delivered artifacts and 7 selected members, and one
`bash -n` sweep while rewriting the blocks. **Reused rather than re-run**, as
the review directs: the child's `prove_capacity.py` (eleven steps),
`prove_custody.py` (13 public invocations, 3 refusals) and
`prove_guide_contract.py` (18 cases) — all byte-unchanged and bound by digest.
No `v12` test file was run or changed; no product source touched.

`evidence/claim-369970/BINDING.json` (sha256 `0dac3124…`) binds the two
delivered files, the owner input documents, the child record and its accepted
binding, the five child files, the owner selection with its digests, the
verification result, **and the six remaining unresolved execution choices**.
The packet digest the verifier saw and the delivered digest agree.

### Boundaries

Only `COMMANDS.md`, `verify_commands.py`, this file and
`evidence/claim-369970/` changed. **No child artifact was modified** — the
child record is a read-only input and its proposal bytes are re-verified, not
rewritten. Nothing was installed, built, cloned, started, admitted or deleted;
no engine, provider or credential was reached; `v12` is byte-unchanged.
`FINDING.md`, `PLAN.md`, `USEFUL-JOB.md` and every review are the reviewer's
and are unmodified.

**Not established:** nothing about live behaviour. No bundle exists on this
host from this claim, no instance at `$DEST`, no image or credential
verified, no OBS-0 interval measured. The open live question stays open, and
what now stands before it is the two prerequisites, §8's execution decision
and the owner's selection to run — not preparation.

## claim370050 — the mint document gets a producer, and every command gets a cwd

Answers `review-2026-10-28T00-49-31Z.md`. Two bounded blockers, both real and
both mine: `$MINT` had a consumer and no producer, and the published sequence
could not be pasted because `cd "$CHILD"` was checkout-relative and ran twice.

### `$MINT` now has a producer, and it is derived rather than restated

`mint_inputs.py` is new and §4 step 1 publishes it. One command, concrete
selected values, destination-derived paths, **no `workers`, no `jobs`, no
`authority_uuid`**.

**It is derived from the phase-2 composition, not written a second time.**
`capacity.compose` already builds this deployment's top-level members from
their named sources; phase 1 is that document **minus `workers` and `jobs`**,
plus the one member phase 1 has and phase 2 does not — `state_root`, because
the destination-form install takes `--destination` and the mint form takes no
destination operand. Restating a dozen values beside the install they precede
is exactly the drift this campaign keeps correcting, so they are not restated.

`compose` requires a 32-hex identity before it will build anything, and phase
1 exists because none has been minted. So a **declared throwaway** derives it
and the result is then *proved* to carry that throwaway nowhere — searched in
the serialized bytes — and `mint_inputs.py` **refuses** rather than emitting a
document with a fabricated identity. It also refuses a path that already
exists: an operator's existing mint input may be the one an instance was
installed from.

The concrete document is published in §4 step 1 with its digest
(`4888a4be…`, 943 bytes), and the verifier **re-derives that figure read-only
for the published destination** rather than trusting it.

### Every command now has an unambiguous working directory

`$CHILD` was checkout-relative and `cd "$CHILD"` was published twice — from
the checkout root the first succeeds and the second exits 1, because the
relative path resolves beneath the directory the first already entered. The
review reproduced it; it was real.

Fixed at the root: §3 now declares `REPO`, `PARENT` and `CHILD` as **absolute**
paths, so every `cd` is idempotent and the sequence can be pasted in order,
re-entered, or run one command at a time from anywhere. `cd v12` became
`cd "$REPO/v12"` for the optional build branch, and §11's own command became
`cd "$PARENT" && python3 verify_commands.py` — it had been published as a
checkout-relative path that only resolves from the root, which by that point
in the sequence is not where the operator is.

### Two verifier checks, because the green one proved neither of these

The review is precise about this: `install_sequence` counts forms and
`child_helpers` imports `capacity` directly, so neither could see a missing
file or a broken `cd`. Two new checks:

**`mint_production`** runs the producer into a disposable destination it
creates and retains, then:

* validates the output — schema, `state_root`, no `workers`/`jobs`/
  `authority_uuid`;
* compares **every remaining member** against the phase-2 composition it is
  derived from (`differing_members: []`);
* drives the overwrite refusal;
* and **runs `bootstrap --inputs <that file>` on it** — exit 0, identity
  `a6eddbe1…` **generated** rather than the throwaway, `configured_no_workers:
  true`. The published digest is separately re-derived read-only.

**`sequence_flow`** walks the published lines in order from the checkout root,
tracking the working directory through every `cd`: each target must exist,
each named script must be reachable from the directory the walk arrived at,
and `$MINT` must be **written by a published command before any published
command reads it**. 32 steps, 7 `cd`s all absolute and all resolving,
`mint_produced_before_consumed: true`, no faults.

It found two further defects while being written, both fixed: `CHILD=$PARENT/…`
needs **fixed-point** expansion (a single pass leaves `$PARENT` inside the
value, which is how the first run reported a `cd` into a directory literally
named `$PARENT`), and §11's relative verifier path above.

**Result: exit 0, 0 failures, 16 published invocations, schema `/4`.**

### Verification and cumulative spending

This claim: 6 verifier runs (the last recorded) — three of them failing and
each failure a real packet defect — plus 2 `mint_inputs.py --print` runs and
one `bash -n` sweep. The mint check performs **one real mint** per run into a
disposable destination it created under `/var/tmp/baton-w257624`; those are
retained, never removed. **Reused rather than re-run:** the child's
`prove_capacity.py`, `prove_custody.py` and `prove_guide_contract.py`, all
byte-unchanged and bound by digest.

`evidence/claim-370050/BINDING.json` (sha256 `29375db1…`) rebinds the three
delivered files, re-verifies the owner selection against the child binding,
records the mint document's provenance and its proof of minting, the sequence
flow result, and preserves `claim-369970`'s binding by digest. The packet
digest the verifier saw and the delivered digest agree.

### Boundaries

Changed: `COMMANDS.md`, `verify_commands.py`, this file,
`evidence/claim-370050/`. New: `mint_inputs.py`. **No child artifact was
modified** — the closed child record is a read-only input and its seven
proposal bytes are re-verified, still `proposed-not-granted`. Nothing was
installed into the proposed destination, built, cloned, started, admitted or
deleted; no engine, provider or credential was reached; `v12` is
byte-unchanged. `FINDING.md`, `PLAN.md`, `USEFUL-JOB.md` and every review are
the reviewer's and are unmodified.

**Not established:** the mints driven here are *disposable* — nothing was
installed at `$DEST`, no image or credential verified, no container started,
no model run, no OBS-0 interval measured. The two prerequisites, §8's
execution decision and the owner's selection to run remain exactly as
recorded.
