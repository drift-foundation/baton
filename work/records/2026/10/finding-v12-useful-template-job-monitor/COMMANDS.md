# W366962 — one useful template Job and its monitor: the operator selection

**Preparation only. Nothing here is selected or run.** No bundle is built, no
instance is installed, no deployment changed, no engine or provider launched, no
Job admitted, no owner act taken, nothing deleted. Every command is *proposed*,
and every command **as published here** is checked by
[`verify_commands.py`](#11-the-verification) without being executed.

Authority: bound `FINDING.md` / `PLAN.md` / `USEFUL-JOB.md`, review
**2026-10-28T00-39-27Z**, owner selection **E369951**, W321608 FINDING
**2026-10-27T01:52:12Z**.

Prepared against `42bed8bb04a53380e565b1a63fb2bc702677f0d0`.
Consumes the accepted child W367232, binding
`92d9962a71b64b5d25142e22a3b5bd52a374093aa1a352c0c8594b2893765723`.

**Where this revision stands.** The capacity gap is **closed**. W367232
delivered the one-time composition, independent review accepted it, and owner
E369951 selected the default seven-policy set as its configuration basis — so
§2 no longer reports outstanding scope, and §§3–5 now publish the sequence the
child's own proof runs:

> §3 materialize → §4 **mint only** → read back → compose + stage the task →
> **ONE** destination install → §5 ordinary input-only `create`

Two things this revision corrects outright. §4 used to publish a destination
install followed by a *second* `bootstrap` run to add workers — that second run
is refused and the shape is replaced. And its claim that the artifact "strictly
precedes even the identity mint" overgeneralized a destination-install refusal:
`bootstrap --inputs <file>` alone mints with no runtime named.

Earlier accepted corrections remain in: the `attempt-diagnostics` argv (R2),
the verifier reading this file rather than a copy (R2), §8's unenforceable
round limit removed (R3), §9's per-verb operand contracts (R3), and §10 no
longer claiming these outputs carry the OBS-0 endpoints (R3).

---

## 1. The proposed Job — the reviewer's selection

| Operand | Value |
| --- | --- |
| `--task` | `template-job-guide-42bed8bb` |
| derived Job id | `job-template-job-guide-42bed8bb` |
| `--template` | `baton.v12.job-template.implementation-review/1` |
| `--source` | `installed` |
| `--work-scope` | `v12/TEMPLATE-JOBS.md` *(a new file)* |
| `--test-scope` | *(none)* |
| `--provider-turn-seconds` | `3600` |
| `--verification-command-seconds` | `900` |

The statement and five acceptance criteria are `USEFUL-JOB.md`'s, reproduced
verbatim in §5. The review clarified that preserving instance‑4 truth does not
forbid editing `QUICKSTART.md`/`STACK.md` inside a properly selected outcome;
the new guide remains the payload and the source references are evidence, not a
files-to-edit restriction on the eventual implementation.

---

## 2. Capacity — delivered, accepted, and selected

**This section used to say the capacity document was still to be composed, and
recommended adapting the old pilot preparer. Both are superseded.** W367232
delivered it, independent review accepted it, and the owner has selected its
configuration basis. What follows is what to consume, by digest.

### The accepted child preparation

Child record: `findings/finding-one-time-capacity-composition/`. Its exact
binding is `evidence/claim-369373/BINDING.json`, sha256
`92d9962a71b64b5d25142e22a3b5bd52a374093aa1a352c0c8594b2893765723`, accepted by
`review-2026-10-27T23-17-07Z.md` and closed **satisfying** by the owner.

Three of its eight delivered artifacts are the ones this packet invokes:

| artifact | what this packet uses it for |
| --- | --- |
| `capacity.py preflight` | read-only: the selection, the archive identity, the derived paths, and the operator grants it cannot resolve |
| `capacity.py materialize` | §3's artifact step — extracts the retained runtime into a directory **it** creates, holding it to *both* pins |
| `capacity.py compose` | §4's phase-2 document for the **minted** identity, two lanes, sealed after the readback |

`prove_capacity.py`, `prove_custody.py` and `prove_guide_contract.py` are its
proofs; §11 reuses them rather than reconstructing anything.

### The owner's selection, which lives in the child's record and not here

Owner E369951 — recorded in the child `FINDING.md` entry *"2026-10-28 — owner
selects default policy basis"* — selects the **default** seven-policy set as
the configuration basis:

    proposed-grants/INVENTORY.json   6ae52f7b2b796fe1bae8323155513fb8f751e182f4a48a0dffbb577243284add
    task digest                      c21e6b93bfe199ebb89b3ec7a75e70a5636c52f9986b1afa3709a381c6bd98d7
    optional formatting set          NOT selected

**The ruling is external to the bytes and stays that way.** The seven proposal
files still read `status: "proposed-not-granted"` and `authorized_by: null`,
and this packet does not rewrite them, re-publish them or flip that metadata to
encode the selection — the selection record is the owner's entry in the child
FINDING, and `compose` keeps answering `preparation_is_complete: false` because
that field reports what the *bytes* carry. A packet that edited them to look
granted would be manufacturing the ruling it is supposed to cite.

So §4 binds the set read-only with `--proposed-grants`, and **not**
`--proposed-format`: mixing the default set with the formatted task is refused
by design, and the child's `CLEAN-START.md` publishes that refusal.

### What the selection is, and what it is not

| | |
| --- | --- |
| **selected** | the configuration *basis* — which seven policy identities the manifest carries |
| **still a prerequisite** | that worker image `sha256:c862c055…` exists on the installing host. The toolchain artifact is the **build recipe** at `42bed8bb`, not an inspection of image contents. |
| **still a prerequisite** | that credential reference `w202663-development` resolves through `/home/sl/.baton/credential-sources.json`. Nothing here reads, resolves or writes a credential. |
| **not demonstrated** | any egress restriction. The network policy names `bridge`; naming a network is not a demonstrated egress ruling. |
| **covered by the ruling** | the selected tool policy includes the existing worker invocation with permission prompts disabled **inside the worker environment** — the owner's entry records that explicitly. |
| **not selected at all** | execution. §8 holds the remaining execution decision; nothing below is run. |

### Where capacity comes from now

`DeploymentDerivation.derived` still refuses an instance with no
implementation worker, and §11 still reproduces that refusal inertly — it is
why the order in §4 matters:

> `this instance configures no 'implementation' worker, and a Job with a
> implementation stage that no worker can serve would never run. Install one
> before creating a Job that owes that stage`

What has changed is that the document which satisfies it now exists and is
accepted. §4 produces it with one command.

---

## 3. The concrete selection

```sh
REPO=/home/sl/src/baton
PARENT=$REPO/work/records/2026/10/finding-v12-useful-template-job-monitor
CHILD=$PARENT/findings/finding-one-time-capacity-composition

DEST=/home/sl/baton-instances/useful-template-job-w366962
DISTRO=/home/sl/baton-instances/useful-template-job-w366962-distro
MINT=/home/sl/baton-instances/useful-template-job-w366962-mint.json
COMPOSE=/home/sl/baton-instances/useful-template-job-w366962-compose
PHASE2=/home/sl/baton-instances/useful-template-job-w366962-phase2.json
```

**Every path here is absolute, and that is a correction.** An earlier revision
made `$CHILD` checkout-relative and then published `cd "$CHILD"` twice — from
the checkout root the first succeeds and the second exits 1, because the
relative path resolves beneath the directory the first `cd` already entered.
Review 2026-10-28T00-49-31Z reproduced that. Absolute paths make every `cd`
below **idempotent**, so the sequence can be pasted in order, re-entered, or
run one command at a time from any starting directory.

`$MINT`, `$COMPOSE` and `$PHASE2` are **outside `$DEST`** on purpose; §4 step 1
says why. `$CHILD` is the accepted child record — the only place this packet
reads a helper from. `$PARENT` is this record.

A **fresh** destination, absolute and outside the checkout. No existing
instance is touched: instances 1–4 and every artifact under
`../finding-v12-native-pilot-instance-packet/` are preserved, and this packet
writes to none of them.

Every other path is **derived from `DEST` by `tools/instance.py`** and never
configured twice — the verifier checks each against `instance.layout(DEST)`:

```
$DEST/instance.json   $DEST/db/jobs.sqlite3   $DEST/db/control.sqlite3
$DEST/db/authority.sqlite3   $DEST/state/status.json
$DEST/state/launch/logs   $DEST/distro/baton-v12-stack
```

**The artifact.** The W366246 archive `verified-first-build.tar.gz`
(sha256 `1da85eed0a3a19a5da0b83253abbbb40ebeed01bfe90ee05a10055dec0057125`,
folder digest `0b7bc592…f88beefd`) is **verified product-compatible** with
`42bed8bb`: all 23 product source members of `candidate-366250` are
byte-identical to the tree (0 drifted), and the integration commit's own
17-path product diff contains nothing outside those members. Its embedded stamp
records `18e771f0, dirty` and `identity`/`--version` will keep saying so —
disclosed, **not relabelled**.

**Extract it with the accepted child's own materializer**, which holds it to
*both* pins — the tarball's sha256 *and*, through `instance.manifest`, the
extracted folder digest against `BUNDLE-ARCHIVE.json`. A tarball that matched
while its contents did not would be a pin that proved nothing:

```sh
cd "$CHILD" && python3 capacity.py materialize --into "$DISTRO"
```

It **creates** that directory and refuses a path that already exists; it never
reuses or removes one it did not create. Its answer reports `distro`, which is
`$DISTRO` below. A fresh build is the alternative:

```sh
cd "$REPO/v12" && just setup
cd "$REPO/v12" && just build /home/sl/baton-instances/useful-template-job-w366962-build
```

`just build` installs the pinned build tool with `--require-hashes` and runs
PyInstaller over `packaging/stack.spec`; the result is host-specific. W366246
proved this recipe and its bundle; **neither is re-run here.** Both recipes are
verified by name against the real justfile.

**There is no authority UUID yet and none is invented.** It is generated at
install and persisted at `$DEST/authority-identity.json`; §4 reads it back. No
secret, credential or token appears in this packet or in any output it proposes.

---

## 4. One-time installation — mint, read back, compose, install **once**

Everything here happens **once per deployment**. OBS-0a: privileged account,
credential, ACL, storage and narrow admission provisioning are one-time
installation; routine starts, failures and retries must not repeat them.

**An earlier revision of this section published a destination install, then a
second `bootstrap` run to add workers. That is wrong and is replaced.** The
second run is refused — a destination that already holds a runtime is not
upgraded in place — and the accepted child establishes the supported shape
instead: **mint only, read back, compose, then ONE destination install that
carries both lanes.** `prove_capacity.py` runs exactly this, end to end, and
§11 reuses that proof.

**And the claim that "the artifact strictly precedes even the identity mint"
was an overgeneralization.** The refusal it rested on —

    refused: installing into <destination> needs a built runtime; name it with
    --distro, or build one with `just build` from v12/.

— is the **destination-install** form's refusal. The mint form,
`bootstrap --inputs <file>` *alone*, takes no `--distro` and needs no runtime.
Measured by the child's `_mint`, which mints with no runtime named. §3 still
comes first in this packet, but because step 4 needs `$DISTRO`, not because
minting does.

### Step 1 — produce the mint document, then mint

**An earlier revision declared `$MINT` and consumed it and never produced
it**, pointing at `v12/STACK.md` and a differently-rooted example instead.
Review 2026-10-28T00-49-31Z is right that this left the operator
reconstructing an authorized preparation input. Here is the producer:

```sh
cd "$PARENT" && python3 mint_inputs.py --print
cd "$PARENT" && python3 mint_inputs.py --into "$MINT"
```

`--print` is read-only; `--into` writes once and **refuses a path that already
exists**, because an operator's existing mint input may be the one an instance
was installed from.

**It is derived from the phase-2 composition, not written a second time.**
`capacity.compose` already builds this deployment's top-level members from
their named sources, and phase 1 is that same document **minus `workers` and
`jobs`** — so the two phases cannot disagree about the deployment they
describe. `compose` needs a 32-hex identity before it will build anything and
phase 1 exists because none has been minted, so a **declared throwaway** is
used to derive it and the result is then *proved* to contain that throwaway
nowhere; `mint_inputs.py` refuses rather than emitting a document with a
fabricated identity in it.

What it produces, concretely — `sha256 4888a4be…`, 943 bytes, which the
verifier re-derives rather than trusting:

```json
{
 "schema": "baton.v12.stack-bootstrap/1",
 "state_root": "/home/sl/baton-instances/useful-template-job-w366962",
 "checkpoint_profile": "git",
 "integration_profile": {
  "profile_kind": "git",
  "profile_version": 1,
  "integrator_participant": "baton.integrator-w366962",
  "instructions_digest": "sha256:fafc35958002db5284b54f4d22cf59a7dccfb5ac05e15baa69db73fcff06d6f2"
 },
 "integration_target": "/home/sl/baton-instances/useful-template-job-w366962/repo/target.git",
 "integration_workspace": "/home/sl/baton-instances/useful-template-job-w366962/repo/workspace",
 "retention_policy_digest": "sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a",
 "retention_disposition": "retain",
 "pool_generation": 1,
 "policy_generation": 1,
 "owner_participant": "baton.slaw",
 "receipt_participants": {
  "verification": "baton.verifier-w366962",
  "review": "baton.reviewer-receipt-w366962",
  "approval": "baton.slaw"
 }
}
```

**No `workers`, no `jobs`, no `authority_uuid`** — `bootstrap.DEFERRED` is
exactly `("jobs", "workers")`, and an input naming an identity is refused
(`bootstrap.SUPERSEDED`). `state_root` is the one member phase 1 has that
phase 2 does not: the destination-form install takes `--destination`, the mint
form takes no destination operand, so the document names it.

**`$MINT` is written outside `$DEST`** on purpose. The mint writes the
destination's own `install-inputs.json` slot, and step 4's destination install
then refuses *"there is already an installer input document … Nothing here
replaces one"* if the staged copy sits in that slot. The child hit this; so
does this packet.

Now mint:

```sh
"$DISTRO/baton-v12-stack" identity

"$DISTRO/baton-v12-stack" bootstrap --inputs "$MINT"
```

`identity` must answer `frozen: true`, both frozen schema assets and a
`native_rpds` inside the bundle's own `_internal`; reusing the archive it will
also report the `18e771f0` stamp, as §3 disclosed. The destination install in
step 4 asks the command the same question and refuses a build that is not
genuinely frozen.

The emitted phase-1 configuration carries **no workers**, by design.

### Step 2 — read the minted identity back

Derived, never faked:

```sh
UUID="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["authority_uuid"])' "$DEST/authority-identity.json")"
WORK="${UUID:0:8}-W1"
```

### Step 3 — compose the two-lane document and stage the task

The composition must come **after** the readback and cannot come before it: a
worker's `input_manifest` is digest-sealed over the authority uuid, so it
cannot be written until that identity exists. This is the child's whole reason
for the mint-first order.

```sh
cd "$CHILD" && python3 capacity.py compose --minted-uuid "$UUID" --destination "$DEST" --distro "$DISTRO" --proposed-grants --evidence "$COMPOSE"
```

`--proposed-grants` binds §2's **selected default set, read-only**;
`--proposed-format` is **not** passed, and passing it with this set is refused.
`compose` writes nothing but the `--evidence` file it reports.

Its answer supplies the next command, and these are the members that matter:

| member of the compose answer | what it feeds |
| --- | --- |
| `document` | the bytes to write as `$PHASE2` — the `baton.v12.stack-bootstrap/1` input for step 4 |
| `task_bytes` | the installed task document; write it at `installed_task.place` **before** step 4, because the installer opens it |
| `installed_task.place` | `$DEST/state/task/template-job-guide-42bed8bb.json` |
| `installed_task.content_digest` | what the manifest's `human_contract` already digests — these are the same bytes |
| `work_id` | `$WORK`, the same value step 2 derived |
| `manifest_digest`, `document_digest` | what to record as this installation's identity |
| `provenance.members` | every manifest member with its source and kind — selected, inherited-contract, or proposed-grant |
| `preparation_is_complete: false` | **expected**, and §2 explains why: the bytes carry ungranted proposals; the ruling is the owner's record |

```sh
python3 -c 'import json,sys;a=json.load(open(sys.argv[1]));open(sys.argv[2],"w").write(json.dumps(a["document"],indent=1,sort_keys=True)+"\n")' "$COMPOSE/compose.json" "$PHASE2"
python3 -c 'import json,os,sys;a=json.load(open(sys.argv[1]));p=a["installed_task"]["place"];os.makedirs(os.path.dirname(p),exist_ok=True);open(p,"w").write(a["task_bytes"])' "$COMPOSE/compose.json"
```

### Step 4 — ONE destination install, carrying both lanes

```sh
"$DISTRO/baton-v12-stack" bootstrap --inputs "$PHASE2" --destination "$DEST" --distro "$DISTRO" --repository-source /home/sl/src/baton
```

This is the only install. It emits `$DEST/deployment.json` with **two
workers** — `implementation` → `baton.claude-w366962` and `review` →
`baton.reviewer-w366962`, distinct participants and distinct principals, which
the manager's own validator requires — each bound to `$UUID`, and that emitted
configuration is what `DeploymentDerivation` reads in §5.

**`--repository-source` rather than `--no-repositories`, and this is the one
place where the child's proof is a simulation rather than a recipe.** The child
ran `--no-repositories` and created the two nominated source directories
**empty**, labelling that as its single test substitution. That is correct for
an inert proof and **wrong for this Job**: a documentation Job must read the
current source and produce an independently reviewed candidate, so it needs the
source and workspace repositories the installer clones from
`--repository-source`. An empty nominated source would give the worker nothing
to read.

So: the child proved the *installation sequence* with empty sources; the
*readiness* of a real source tree is a prerequisite of execution and is not
established by that proof. §12 keeps that distinction.

---

## 5. Admit the Job — ordinary, input-only

```sh
"$DISTRO/baton-v12-stack" manager --store "$DEST/db/jobs.sqlite3" --incarnation operator-1 --authority-uuid "$UUID" create --instance "$DEST" --control "$DEST/db/control.sqlite3" --authority "$DEST/db/authority.sqlite3" --task template-job-guide-42bed8bb --template baton.v12.job-template.implementation-review/1 --source installed --provider-turn-seconds 3600 --verification-command-seconds 900 --statement "Write a reusable operator guide for ordinary v12 template Job creation and observation using the supported installed command. Explain the supplied task, source, scope and acceptance inputs, template version and limits, independent review and held results, failure/recovery boundary and human disposition. Verify all documented command examples against current supported parsers and behavior. Preserve the historical instance4 QUICKSTART facts; do not claim source features are installed there. Deliver documentation, not product redesign." --acceptance "Examples use supported manager create with input-only operands and the exact template version; they do not author admission manifests or replace owner APIs." --acceptance "Source/installed distinction, actual deployment identities, proposed versus executed operations and default/overridden limits remain explicit and truthful." --acceptance "Monitoring is read-only; query time is not worker contact; unknown activity is not success; ending the monitor does not stop scheduling." --acceptance "Implementation completion, independent verdict, held proposal, human acceptance and Git integration are distinguished. Failure/retry and runtime-cessation prerequisites are stated without silently retrying or claiming stop is cleanup." --acceptance "Semantic evidence checks command order/options and statements against owning implementations, not only headings/byte count. Review binds the actual candidate." --work-scope v12/TEMPLATE-JOBS.md
```

**Input-only.** No digest, manifest, submission document, launch packet or host
path is among the selections, and the argument list has nowhere to put one
(DESIGN SCH-1a). The input digest, policy digest, both stage profiles and the
Work are **derived by the deployment from the workers §4 step 4 installed** —
`DeploymentDerivation` reads `$DEST/deployment.json`, not anything passed here.
All per-Job admission stays inside the manager; nothing hand-composes a Work
authority, and §4 pre-composes **no submission**: the phase-2 document's
`jobs[]` entry names the Job and admitting it is the manager's own act.

**What `$DEST/deployment.json` supplies this command**, so the dataflow is
explicit rather than implied: the two servable lanes (`impl-w366962`,
`review-w366962`), the one input identity both share, and the installed task
document at `installed_task.place` whose `task_id` is the `--task` operand
below.

**Record the JSON answer.** It carries `job_id`, `work_id`, `submission_id`, the
resolved `template` with its origin, the derived `source` digests, the resolved
`execution_limits` (with `provider_turn` showing `origin: job`) and `servable`.
Those are the identities §7 observes by and §10 retains.

The identical command again replays the same answer; the same `--task` with a
different statement is refused as the different creation it is. The two
overrides above are the only ones this template permits.

---

## 6. Start the deployment

```sh
"$DISTRO/baton-v12-stack" start --instance "$DEST/instance.json"
```

It supervises the scheduler and the snapshot publisher and waits for a
published snapshot before reporting success. **`--instance` comes immediately
after the subcommand** on the installed command; `monitor --interval 3
--instance …` is rejected, and `--instance … monitor` is rejected as a
subcommand name. That lifting is `stack_command._stack`'s own and the verifier
exercises it from this published text.

---

## 7. Observe — the existing read-only monitor

```sh
"$DISTRO/baton-v12-stack" status --instance "$DEST/instance.json"
"$DISTRO/baton-v12-stack" monitor --instance "$DEST/instance.json" --interval 3 --ticks 400
```

`monitor` is the selected lightweight read-only list view over the **published
snapshot**: each stage's kind, state, elapsed, activity and reason.

**What it is not.** Viewing claims, renews, reconciles, acknowledges, retries
and deletes nothing (OBS-1). **Query time is not worker contact** — the
snapshot has an age, and refreshing over a stale snapshot says nothing new.
**Unknown activity is not success.** **Ending the monitor does not stop
scheduling.** And per R3: `--ticks 400` at `--interval 3` is roughly a
20-minute *observation* window — it **bounds the watching, not the work**. It
does not cap the 3600s provider turn and does not stop the deployment.

Observe by the identities §5 recorded, and expect the order W361912 proved
deterministically: implementation `waiting` with a running runtime, then
`completed`; the **independent review** stage starting its own container under
a different participant; then an accepted verdict or `changes-requested`.

Further read-only surfaces:

```sh
"$DISTRO/baton-v12-stack" view --status "$DEST/state/status.json" --ticks 1
"$DISTRO/baton-v12-stack" manager --store "$DEST/db/jobs.sqlite3" --incarnation operator-1 --authority-uuid "$UUID" status --control "$DEST/db/control.sqlite3" --observe tools.stage_execution:observing_factory
"$DISTRO/baton-v12-stack" record read --authority-store "$DEST/db/authority.sqlite3" --authority-uuid "$UUID" --work "$WORK"
```

W324214's `worker_visibility` projection reads a status file and is an
*optional existing* projection — not the installed terminal monitor. No
collector is invented and no broader telemetry work is a gate. **The deliverable
of watching is the list of questions this view could not answer**, which is the
input to the next monitor slice per the October 27 ruling; that list does not
exist yet and is not pre-judged.

---

## 8. Serving bounds, and the execution decision that is still open

**R3's correction.** The previous draft said finite correction turns "must be
selected before serving" without proposing the selection or saying what holds
it. Here it is, explicitly:

* **The configured ceilings are the only enforcement**: `provider_turn 3600s`
  and `verification_command 900s` **per invocation**, from §5. Nothing in the
  monitor, and nothing an operator can pass at start, caps total wall time.
* **One implementation turn and one review turn are what this selection
  wants — and nothing here enforces that.** An earlier draft said the run
  could be "abandoned at the first `changes-requested` verdict" by §10's
  procedure. **That was false** and review 2026-10-27T17-42-27Z was right to
  call it so: a `changes-requested` verdict makes the product open the
  correction round **itself**, and §10 only observes until attempts are
  terminal — by the time an operator reads the verdict the next invocation may
  already be running. Observing and waiting cannot enforce a round limit, and
  presenting stop-or-abandon as a control would be presenting an unimplemented
  one.

  **The exact unresolved execution decision, stated rather than dressed up.**
  There is no installed subcommand that caps correction rounds or cancels an
  in-flight provider turn. The Authority *does* have a cancellation API —
  `v12/QUICKSTART.md` documents `Authority.cancel`, which fences the
  assignment, leaves the **Work `open` with no outcome**, and leaves the
  **runtime-quiescence gate surviving** at the cancelled assignment's own
  generation. It is not among the 14 subcommands the bundle serves, it
  cancels an *assignment* rather than a Job's correction policy, and any
  proposed use must honour those boundaries and would itself need execution
  selection. **So the owner must decide, before serving, between two honest
  options:** accept that an automatically opened correction may consume a
  further 3600s invocation, or select a cancellation procedure through that
  API as part of the execution selection. This packet prepares neither as a
  control and invents no host-side protocol write.

* **No discretionary retry is proposed.** `fresh-attempt` repeats a Job *whose
  execution failed* and selecting one is a separate owner decision. Do not
  force a correction merely to spend a live run: retain the natural outcome.
* **Success is judged semantically**, not by completion: the candidate must
  satisfy §1's five criteria, which is the reviewer's judgement and then the
  owner's — not a stage reaching `completed`.

Diagnostics, with the argv this build actually takes:

```sh
"$DISTRO/baton-v12-stack" attempt-diagnostics "$DEST/state/status.json"
"$DISTRO/baton-v12-stack" logs --logs "$DEST/state/launch/logs" --attempt "$ATTEMPT" locators
```

**`attempt-diagnostics` takes exactly one positional file.** The previous draft
published `--status FILE`, which exits 2 — review R2 found it and the verifier
now drives both forms so the correction is proved. `$ATTEMPT` is an attempt id
from §5/§7; the previous draft's unquoted `<attempt-id from …>` was not a
pasteable command.

---

## 9. Disposition — the owner's own surface

```sh
"$DISTRO/baton-v12-stack" disposition pending --authority-store "$DEST/db/authority.sqlite3" --authority-uuid "$UUID" --work "$WORK" --root "$DEST"
```

`pending` is read-only: what owner act is due, and with `--root` the state of
the accepted integration record now.

**Four things stay distinct.** Implementation *completing* is not a verdict. The
reviewer's *technical verdict* is not an owner decision. A **held** proposal
under `report-and-hold` is retained, not accepted. **Git integration is
Slawomir's alone.**

**The owner verbs do not share one operand set, and two earlier drafts of this
file got that wrong.** The first taught a universal set; the second fixed the
table but still put `--participant` and `--operation-id` in a "shared"
heading while marking `pending`'s participant optional — two statements about
one contract. The operands below are read out of `disposition_command`'s own
parsers by the verifier, which fails if this table drifts from them:

| verb | exactly what it requires |
| --- | --- |
| `pending` *(read-only)* | `--authority-store --authority-uuid --work`. It takes **no `--participant` and no `--operation-id`**: both are optional additions, and `--root` is the optional one that also resolves the integration record. |
| `approve`, `deny` | the acting set — `--authority-store --authority-uuid --participant --work --operation-id` — plus `--proposal --expect-candidate-digest --expect-review --policy-generation --approval-id`. |
| `integrated` | the acting set plus `--proposal --expect-candidate-digest --root --reference --commit --integration-id --evidence-operation-id`. A **different** set: no `--expect-review`, no `--policy-generation`. |
| `close` | the acting set plus `--outcome --rationale` **only**. `--proposal`, `--expect-candidate-digest`, `--root` and `--expect-assignment` are optional. |

**The closure outcomes are a closed vocabulary**, and naming others would teach
operands the Authority does not accept: `satisfying`, `non-satisfying`,
`rejected`, `cancelled` (`authority.core.INTAKE_OUTCOMES`). Only `satisfying`
requires the acceptance chain — a passed verification, an accepted independent
review, the owner's approval and integration receipt, and the human integration
record still intact where the dossier cites it; any one missing refuses and the
refusal names which. The other three close honestly with none of that, and
nothing in that verb deletes or rewrites evidence. "Denied" and "abandoned"
describe situations, **not** `--outcome` values. And where an assignment is
still live, `--expect-assignment` carries the exact assignment identity the
closure ends — assignment fencing still applies.

**None of these acts is proposed here**: the digests they require do not exist
until a Job has produced a candidate, and no automatic integration follows.

## 10. Failure, cessation and retention — nothing is deleted

**R3's correction.** The previous draft said only "confirm ceased" and then
suggested removing `$DEST`, which conflicts with preserving evidence. Replaced
by a procedure with an action for each state.

**Step 1 — retain, before anything else.** Copy the identities and endpoints
out of the deployment while it is intact:

```sh
"$DISTRO/baton-v12-stack" manager --store "$DEST/db/jobs.sqlite3" --incarnation operator-1 --authority-uuid "$UUID" status --control "$DEST/db/control.sqlite3" --observe tools.stage_execution:observing_factory
"$DISTRO/baton-v12-stack" attempt-diagnostics "$DEST/state/status.json"
```

Keep the §5 create answer, both outputs above, and each attempt's retained raw
output locators (§8). Together they carry the **Job, attempt and result
identities**, which is what makes the run auditable.

**They do NOT carry the OBS-0 endpoints, and an earlier draft of this file said
they did.** Review 2026-10-27T17-42-27Z found the claim unsupported and it was:

* `documents.STATUS_SCHEMA` carries `observed_at`, which is **query time** —
  when the projection was taken, not when anything happened;
* worker visibility deliberately distinguishes **bytes observed from progress**
  and **query time from worker contact**; neither is the agent entering
  substantive work;
* nothing in these outputs records the instant the operator's command was
  received.

So **the live OBS-0 interval is not measurable from this procedure, and no live
OBS-0 result is claimed here.** The command-received endpoint can be captured
only by the operator noting it outside the product (for example by timestamping
the §5 invocation in a shell transcript), and the substantive-work endpoint has
no field in any output this packet reads. Both are therefore **unknown**, and
they stay unknown rather than being approximated from `observed_at`.

What is retained instead is **raw timestamped evidence with its source
association**: the shell transcript of the §5 and §7 invocations, each
projection as captured with its own `observed_at`, and the attempt log
locators. If a live OBS-0 measurement is wanted, it needs a method this
preparation does not have, and that is an unresolved item rather than a
recorded figure. W361912's accepted figures are **simulated-engine** timing and
say nothing about a live interval.

**Step 2 — read the state, then act on it.**

| What the projection shows | The supported action |
| --- | --- |
| an attempt `running` | **keep observing**; re-run §7. Stopping supervisors over a live runtime orphans it. There is no supported operand that cancels an in-flight provider turn, which is the same gap §8 names. |
| cleanup `pending` | **keep ticking** — the deployment's own reconcile returns the resource. Do not remove anything while it is outstanding. |
| the monitor window ended but work continues | **nothing is wrong**; the window bounded the watching. Re-enter `monitor`, or read `status` once. |
| every attempt terminal **and** cleanup settled | cessation is confirmed; step 3 is now safe. |
| an attempt terminal with a **held** result | that is `report-and-hold` working. The material is retained deliberately; §9 decides, not cleanup. |

**Step 3 — stop only the supervisors, and only then.**

```sh
"$DISTRO/baton-v12-stack" stop --instance "$DEST/instance.json"
```

**`stop` ends the processes this deployment supervises. That is not runtime
cessation** — attempts run in runtimes the manager does not own, which is why
step 2 precedes it.

**Step 4 — preserve.** `$DEST`, its stores, its retained attempt material and
its logs are **kept**. No deletion is proposed and none is needed to deliver
this preparation; a destination is discarded only by a separate explicit owner
choice, after whatever evidence is wanted has been copied out.

---

## 11. The verification

```sh
cd "$PARENT" && python3 verify_commands.py
```

Recorded at `evidence/claim-369970/verification.json`, with
`evidence/claim-369970/BINDING.json` binding what this packet delivers, the
accepted child it consumes, the owner's selection and the remaining
unresolved execution choices.

**It reads this file.** Review R2's finding was that the previous verifier kept
its own copy of the command list and therefore checked the copy — which is how
`--ticks 40` versus `400` and a missing `attempt-diagnostics` both survived. It
now extracts the commands from the published text, so there is no second copy
to drift.

What it establishes, with no build, install, store, engine or provider:

1. **shell syntax** — every fenced `sh` block through `bash -n` with this
   packet's own assignments in scope, so an unquoted placeholder or unbalanced
   quote fails; `bash -n` parses and does not execute;
2. **the subcommand is one this build serves** — from `stack_command.COMMANDS`;
3. **the operands parse**, through the product's own parser, with argv taken
   from the published text — `parse_args` is wrapped so it parses and then
   raises, so nothing past parsing runs;
4. **the parserless commands are covered** against an inert supported status
   document this check writes itself: `attempt-diagnostics <file>` exits 0 and
   `--status <file>` exits 2, so §8's correction is driven rather than claimed;
   `identity` has no operands and no parser and is deliberately not invoked;
5. **the no-capacity refusal is reproduced** inertly — a fresh instance still
   refuses creation, which is why §4's order matters; it also asserts `pool` is
   absent from the served subcommands;
6. **the archived bundle's compatibility** by §3's two checks;
7. **the child helper invocations parse** — every `capacity.py <verb>` this
   file publishes is driven through `capacity.py`'s own parser, so a published
   operand it does not serve fails here;
8. **the §4 sequence is the accepted one** — that the mint step passes
   `--inputs` and **no** `--destination`/`--distro`, that exactly **one**
   destination install is published, and that `--repository-source` is on it
   rather than `--no-repositories`;
9. **the selection is the one the owner made** — the child's default
   `INVENTORY.json` digest, its task digest and `proposed_format: false` are
   compared against the digests §2 publishes, and the seven proposal files are
   re-hashed against the accepted child binding. It also asserts their
   `status`/`authorized_by` are **unchanged**, so this packet cannot be the
   thing that flipped them;
10. **the two lanes are distinct** — composed inertly for a throwaway identity
    and checked for two roles with two participants and two principals;
11. **the refusals stay covered** — occupied materialization target,
    mismatched proposal set against the formatted task, and the no-capacity
    refusal above;
12. **the mint document is actually produced, and it actually mints** — the
    producer runs into a disposable destination this check creates, the
    output is validated (schema, `state_root`, **no** `workers`/`jobs`/
    `authority_uuid`), every remaining member is compared against the
    phase-2 composition it is derived from, the overwrite refusal is driven,
    and then `bootstrap --inputs <that file>` is **run** on it: exit 0, an
    identity *generated* rather than the throwaway, and no workers
    configured. The `sha256 4888a4be…` this file prints is re-derived
    read-only for the published destination and compared against the text;
13. **the sequence resolves in order from a clean starting directory** — the
    published lines are walked in sequence from the checkout root, every
    `cd` is resolved against the current directory and its target must
    exist, every named script must be reachable from the directory the walk
    has arrived at, and `$MINT` must be **written by a published command
    before any published command reads it**;
14. **the identities** — the prepared commit, the digest of this file, the
    accepted child binding digest, and the digest of all twelve product files
    the command surface comes from.

**Limits, which matter as much.** It does not check that a bundle exists on
this host, that an instance is installed at `$DEST`, that the worker image or
the credential reference resolve, or that any command *succeeds*. `just`
recipes are checked by name. It composes only against throwaway identities and
disposable paths it owns.

Passing it means the published text is syntactically sound, structurally
coherent, and in agreement with the accepted child and the owner's selection
— **not** that the deployment is ready. The sequence is runnable only once
§2's two prerequisites (image, credential) hold and the owner selects
execution.

---

## 12. What this packet does not establish

It selects no build, install, start, Job, owner act or deletion, and changes no
source, deployment or configuration. Every existing instance and historical
artifact is preserved.

It cannot establish — and does not claim — that a live provider authenticates,
that a container starts, that a real model produces a usable proposal, how long
a real startup takes, or that this documentation Job would pass its own review.
W361912's startup figures are simulated-engine timing; its workflow evidence is
deterministic control flow over synthetic proposal and verdict content and
includes no completed correction plus second review.

**The source-readiness boundary, stated once more because it is easy to
mis-read.** The child's connected proof installed with `--no-repositories` and
two **empty** nominated source directories, labelled as its one test
substitution. That proves the installation sequence; it does **not** prepare a
source tree. This Job needs a real one, which §4 step 4 obtains with
`--repository-source`, and whether that clone and the workspace it lands in are
adequate is an execution prerequisite rather than something proved here.

**The open live question** — does the installed create command deliver the
selected task to independent implementation and review runtimes and expose its
progress and results in the existing monitor — is answerable only by an
owner-selected run. What stands between this packet and that run is no longer
preparation: it is the two prerequisites §2 names (the worker image on the
host, the credential reference resolving), the execution decision §8 holds
open, and the owner's selection to run it.
