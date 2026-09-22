# Operator steps for the W236087 managed correction packet

> **SUPERSEDED by `OPERATOR-238827.md`.** Kept in place: review
> 2026-09-22T12:55:41Z found that earlier revisions had been deleted
> when superseded, so their evidence locators stopped resolving. See
> `LOST-ARTIFACTS-238827.md`. Nothing in this dossier is unlinked now.

Claim 238700, baton.claude. Supersedes the claim-238462 revision, whose step 5
still named a superseded selections document and whose shutdown bullet still
said the deployment could not cancel. Read with
`PACKET-INPUTS-238700.json`, `IMAGE-ARTIFACT-236349.json`,
`MANAGER-ARTIFACT-236349.json`, `MANAGER-SOURCE-238462.json`, `supervisor.py`,
`packet_bindings.py`, `SELECTIONS-238700.json` and their verification receipts.

**Nothing here has been run live.** Steps 1–3 are done and digest-bound; step 4
is the one act this implementer's deployment prohibits it from performing; steps
5–6 are prepared programs the operator runs.

## What this revision changes

- **Step 4 commits four files, not one.** One Job carries one input manifest,
  so both roles read one task document; the reviewer's criteria therefore also
  travel in the fixture repository, read-only at `/input/source`, where each
  role can read what it is held to.
- **Step 5a is new and was missing entirely.** A fresh zero-Job installation
  creates no Work, no route handler and no grant -- `tools/bootstrap._compose`
  says so in as many words -- and neither the packet composer nor the
  supervisor provisions them. Naming a participant in a configuration does not
  register it.
- **The provider network is an owner selection and `none` is refused.** The
  first draft copied the image-inspection container's `--network none` posture
  into the live deployment. `oci.py` passes that value straight to `--network`,
  and the worker reaches an external Claude API, so that deployment could never
  answer the question this run exists to ask.
- **`evidence_digest` is real retained evidence**, not 64 zeroes. It names
  W177936's independently accepted isolated-recall evidence
  (`REVIEW-EVIDENCE-235998.json`), and the composer refuses an all-zero digest.
- **The deployment stops what it started.** Closing the admission gate stops
  the next runtime; it does nothing about one already waiting on a provider
  turn. On a timeout, a serving fault or an interruption the supervisor now
  asks the composed deployment to cancel each attempt it launched, and the
  deployment carries that capability -- see "The deployment now stops what it
  started" below. A canonical read that did not answer is still a reason to
  hold rather than a reason to report emptiness.

## What the earlier revisions claimed and this one does not

- It said the supervisor "stops admission" and "stops by itself". It did
  neither: the cleanup window called the ordinary admitting sweep, and a runtime
  started during shutdown was noted and then left out of the accounting.
  Admission is now closed at the operations boundary and every started runtime
  is recorded at the launch call. See R2 in the review.
- It said the packet's declared bounds were enforced. They were validated and
  dropped. Caps are now refused at the admission gate before an offer is issued,
  `turn_seconds` is the Job's own `provider_turn` ceiling and is checked as
  effective before serving, and a settled outcome now requires the actual
  correction sequence. See R1.
- It pinned a frozen executable the command never ran, while the supervising
  code came from a mutable checkout. Step 6 below now puts the **bound manager
  source** on `PYTHONPATH` and the supervisor proves the imported packages
  resolve inside it before opening a store. See R3.
- Its step 4 used an ellipsis in place of the add and commit commands. They are
  written out below.

## What is already built and bound

**1. The refreshed immutable worker artifact.** Built from
`v12/worker/Dockerfile.claude` over the accepted six-path candidate.

    reference   baton-v12-claude-worker:w236087-236349
    image       sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd
    claude CLI  2.1.247 (Claude Code)

Its effective `/opt/baton/claude_agent.py` is
`abdf903da3c767f3fe9babf84e4499f455da968a61ee3c975b9899988354bb4d` — the
accepted candidate byte-for-byte, so this artifact can honestly serve the
reviewed bytes and the old `sha256:e84a033c…` image cannot. Every layer diff ID
and effective worker file is in `IMAGE-ARTIFACT-236349.json`. Evidence for it is
an engine inspection plus one throwaway `--network none --read-only` container
that hashed those files and read the CLI version. That container **is** an
engine execution of this image, and it is the only one: no model, no credential,
no egress, no registry push, and no managed or live provider run.

**2. The isolated manager runtime.** `just build`:

    distro      /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro
    identity    sha256 04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a
    build stamp commit 1e576ff2186db69e8b44da9d38874ff7e99ebbe3, dirty, 7 changed entries

**3a. The isolated installation.** `just bootstrap` in the fresh-install form:

    destination /home/sl/baton-runs/managed-correction-236087/install
    authority   636a9493650b4efe9d03c684b5b9d904  (generated for THIS instance)
    stores      install/db/{authority,jobs,control,integration}.sqlite3
    repos       install/repo/target.git, install/repo/workspace
    jobs 0, workers 0

**3b. The bound manager source — the code that actually supervises.**

    path        /home/sl/baton-runs/managed-correction-236087/manager-source
    contents    baton_v12/ and tools/, 106 files, read-only after copy
    origin      v12/python/src/baton_v12 and v12/python/tools at 1e576ff2
    drift       none: every file matches its origin byte for byte

`MANAGER-SOURCE-238462.json` lists all 106 digests, refreshed after the cancellation
seam changed two of them. The packet binds this tree,
`held_packet` re-hashes every file in it, and `verify_imported_sources` refuses
if `baton_v12` or `tools` resolve anywhere else. The frozen distro in step 2
remains the **installation** artifact — it owns the store layout and is what
`just start` would execute — and is no longer claimed to be the supervising
implementation.

No existing deployment, service, credential store or production instance was
read, started, changed or enabled, and nothing in `/home/sl/src/baton` was
mutated: the checkout's working tree is the accepted candidate's six modified
files plus this untracked dossier, and `git diff --check` is clean.

## 4. The disposable fixture repository — blocked here by deployment policy

The Job's `line_declared_base` is a commit object, and this implementer's
deployment prohibits Git history and index mutations. The fixture BYTES are
pinned in `fixture/` and re-proved by the supervisor before it admits anything,
so you are committing bytes you did not choose:

    fixture/harness.py           362e989b9eeb58273c85b28fa156832e1b459a75fe6916712104d4035d40f3b4
    fixture/TASK.md              221464d7d411613bc246c8e5308807c36fecb0fa7c92d1f85d2dee20343c4fba
    fixture/REVIEW-FEEDBACK.md   2b810e14686f5c52e5afaf196dfc26d98fe01fde041c094f0136b740ce7de4a0
    fixture/ACCEPTANCE.md        de5b3672835a6481995c36cf233fe31e622c823c5657d03cdabf3e61e98fa1c5

`harness.py` prints `before`; the accepted correction prints `READY`. All four
are committed: the reviewer reads `REVIEW-FEEDBACK.md` and `ACCEPTANCE.md` from
its own read-only `/input/source` mount, because one Job carries one task
document and a second document for the review role is one no stage could satisfy.

```sh
DOSSIER=/home/sl/src/baton/work/records/2026/09/finding-v12-managed-session-resume
SRC=/home/sl/baton-runs/managed-correction-236087/fixture-source
mkdir -p "$SRC"
for NAME in harness.py TASK.md REVIEW-FEEDBACK.md ACCEPTANCE.md; do
    cp "$DOSSIER/fixture/$NAME" "$SRC/$NAME"
done
sha256sum "$SRC"/*               # must match the four digests above

# No ambient identity, config or hooks: the container has none, so a fixture
# that borrowed yours would differ from what the run actually sees.
FIXTURE_ENV=(env -i PATH="$PATH" HOME="$SRC"
    GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
    GIT_TERMINAL_PROMPT=0
    GIT_AUTHOR_NAME="Baton Fixture"    GIT_AUTHOR_EMAIL="fixture@baton.invalid"
    GIT_COMMITTER_NAME="Baton Fixture" GIT_COMMITTER_EMAIL="fixture@baton.invalid")

"${FIXTURE_ENV[@]}" /usr/bin/git -C "$SRC" init -q -b main
"${FIXTURE_ENV[@]}" /usr/bin/git -C "$SRC" add harness.py TASK.md \
    REVIEW-FEEDBACK.md ACCEPTANCE.md
"${FIXTURE_ENV[@]}" /usr/bin/git -C "$SRC" commit -q -m "fixture base"
BASE=$("${FIXTURE_ENV[@]}" /usr/bin/git -C "$SRC" rev-parse HEAD)
echo "$BASE"
```

Keep `$BASE`. It is step 5's one operand.

## 5a. Prepare the Authority -- the step the fresh install does not do

`just bootstrap` in the fresh-install form generates this instance's Authority
identity and its stores, and **creates no Work, no route handler and no grant**.
`stage_execution` resolves each configured participant's principal from the
Authority and mints five sessions in the target Work's scope, so a deployment
whose participants were never registered refuses at composition -- after the
packet has been written and with nothing said about why.

These are Authority mutations and therefore yours. They are ordinary owner acts
against the **disposable isolated instance**, not the production one:

```python
from baton_v12.authority import Authority

WORK = "636a9493-W1"          # this instance's prefix; see SELECTIONS-238700
STORE = ("/home/sl/baton-runs/managed-correction-236087/install/db/"
         "authority.sqlite3")
authority = Authority.open(
    STORE, expected_authority_uuid="636a9493650b4efe9d03c684b5b9d904")
try:
    authority.create_work(WORK, "impl", contract="v12-assignment-1",
                          operation_id="w236087-managed-correction")
    scope = authority.project_work(WORK)["scope"]
    authority.add_route_handler("impl", IMPLEMENTATION_PARTICIPANT)
    authority.add_route_handler("rview", REVIEW_PARTICIPANT)
    authority.add_route_handler("integration", INTEGRATOR_PARTICIPANT)
    for who, capability in ((VERIFIER, "verify"), (REVIEW_RECEIPT, "review"),
                            (APPROVER, "approve"),
                            (INTEGRATOR_PARTICIPANT, "integrate")):
        authority.grant_capability(who, capability, scope=scope)
finally:
    authority.dispose()
```

Check what is left with the composer's own preflight BEFORE disposing the
handle -- it reads through the open Authority and writes nothing. Its two other
operands are the composed documents and the participants block you filled in:

```python
import json, packet_bindings

selections = json.load(open(
    "/home/sl/baton-runs/managed-correction-236087/selections.json"))
documents = packet_bindings.compose(base=BASE, run_root=RUN,
                                    **selections["compose"])

authority = Authority.open(STORE, expected_authority_uuid=AUTHORITY_UUID)
try:
    # ... the create_work / add_route_handler / grant_capability calls above ...
    missing = packet_bindings.preflight(
        authority, documents, selections["compose"]["participants"])
    print("\n".join(missing))
finally:
    authority.dispose()
```

It names every missing Work, principal and capability, and says plainly that
route-handler registration is **not verifiable** through the Authority's public
readers -- that one is yours to assert.

## 5. Compose the per-Job bindings

`packet_bindings.py` drafts every remaining document — the two worker
deployments, the sealed `inputManifest`, the candidate context profile `/2`, the
Job submission with its provider-turn ceiling, and `PACKET.json` — and holds the
result with `stage_execution.held_configuration`, the same validator the serving
deployment and `tools.bootstrap` both run. A composition the manager would
refuse never reaches the disk. **It grants nothing**: it opens no store, mints no
session, reads no credential and starts nothing.

The three identities this deployment is accountable for are emitted as readable
documents whose digests are used, so you approve text rather than a hash:

    runtime-profile.json  -> profile_digest
    policy.json           -> policy_digest
    adapter.json          -> adapter_digest

Copy `SELECTIONS-238700.json` and fill the `OWNER-CHOICE` fields — the two
participants and their principals, your private credential registry path and
slot reference, and the bounded provider egress network. `none` is refused, by
name, with the reason. The document enumerates all six under
`_unresolved_operands`; everything else is bound, including `evidence_digest`.

```sh
BOUND=/home/sl/baton-runs/managed-correction-236087/manager-source
RUN=/home/sl/baton-runs/managed-correction-236087/run
PYTHONPATH="$BOUND" /home/sl/.local/state/baton-v12-venv/bin/python -B \
    "$DOSSIER/packet_bindings.py" \
    --selections /home/sl/baton-runs/managed-correction-236087/selections.json \
    --base "$BASE" \
    --run-root "$RUN"
```

It prints the digest of every document it wrote. An unresolved `$BASE` is
refused by name rather than written as a placeholder.

## 6. Run the bounded supervisor — one command, and it ends by itself

```sh
cd "$RUN"
PYTHONPATH="$BOUND" /home/sl/.local/state/baton-v12-venv/bin/python -B \
    "$DOSSIER/supervisor.py" \
    --packet "$RUN/PACKET.json" \
    --incarnation managed-correction-236087
```

`PYTHONPATH` names the bound tree and nothing else, so `baton_v12` and `tools`
resolve there; the supervisor refuses before opening a store if they do not, or
if any of the 106 bound files or its own bytes have moved. That refusal is
covered by a test that runs this exact entrypoint, as are its success and
timeout paths.

What it does, in order: proves every bound artifact and the imported modules;
asks the engine for the image; performs the three owner acts; submits the Job
once; checks the effective provider-turn ceiling is the declared 180s and came
from the Job; serves until the stages are terminal, a cap is refused, or the
900s bound elapses; **closes admission at the operations boundary**; re-reads
the canonical history; spends the reserved 60s settling endings through the
closed gate, which cannot admit, claim or launch; requires a positive committed
`runtime.destroy` for every runtime it launched; checks the run really performed
the selected open → changes-requested → restore → accepted sequence with two
distinct retained proposals; and retains the outcome at the packet's
`outcome_path`.

Exit 0 means settled. Exit 1 means held, with every reason named in
`held_because` — including a reviewer who accepted immediately, asked for a
second correction, or rejected. Exit 2 means the packet was refused before
anything opened. There is no retry at any exit.

**Do not wrap the older `tools.job_manager … serve` command in a bare `timeout`
and call it cleanup.** That command serves until stopped and settles nothing on
the way out; it is why this supervisor exists.

## The deployment now stops what it started

`tools/single_worker.py` and `tools/stage_execution.py` carry the cancellation
seam (claim 238462, provenance amended in `CANDIDATE.json`). On a timeout, a
serving fault or an interruption the supervisor asks the composed deployment to
cancel each attempt it launched; `stage_execution` routes the attempt to the
worker its recorded allocation names, and `single_worker` calls the accepted
`attempts.request_cancellation`, which fences the exact participant and
generation at the Authority before the agent and the runtime are ordered to
stop.

**An ordered stop is not proof of absence**, and nothing here treats it as one:
the supervisor keeps driving the ordinary ending path and still requires a
positive committed `runtime.destroy` for every runtime before it calls a run
settled. `SIGKILL` cannot be caught and no recovery from it is claimed;
Ctrl-C and an ordinary `SIGTERM` are handled, at any point in the run.

## What a successful run would and would not establish

It would answer the one remaining provider-specific question: whether the
production CLI consumes its conversation-specific JSONL, restored by the normal
manager after positive original-runtime exclusion, and uses independent-review
feedback to produce a revised attributable proposal in a fresh worker.

It would NOT be production certification, enabling, rollout, or a second
qualification. Certification remains a separate owner decision requiring
retirement and retained independent evidence, and `supervisor.prepare` refuses a
production profile outright rather than routing around that.
