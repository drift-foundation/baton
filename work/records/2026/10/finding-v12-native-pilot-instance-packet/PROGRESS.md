# Implementer progress — W325959

Author: `baton.claude` (role `impl`), v11 claim 325968, 2026-10-18.
Bound dossier: this directory. Parent `W321608`. Owner selection
`baton:work/records/2026/10/finding-v12-development-coordination-pilot/SELECTION-325909.md`
(M325952 / E325954). Pinned source `14e52d80679de5e844f72324df632da5e01cf393`;
the working tree carries no product change and this Work authors none.

## Operational finding, recorded before any edit

**The bound dossier carried no `FINDING.md` and no `PLAN.md` when this claim
opened** — the directory existed and was empty, and `T325959` says the
"Dossier FINDING/PLAN will pin acceptance and ownership" in the future tense. I
am not proceeding without a scope source: the authoritative sources I can read
and am working from are the thread message `T325959` (which states the selected
outcome in full), the owner selection sheet `SELECTION-325909.md`, and the
accepted W321690 packet and its evidence. Both absent files are reported here
and in the handoff rather than guessed at; if the reviewer's FINDING/PLAN
narrows this scope, that narrowing is theirs to apply.

## Owned paths

Only this dossier. The W321690 parent artifacts, the three child dossiers and
every product file are untouched; accepted evidence is read and cited, never
modified.

## What this Work owes, from T325959 and the selection sheet

One immutable, instance-specific **preparation** packet — configuration,
submission, provenance and operator commands — for one new native v12
operator-quickstart Work. No execution, no launch, no cutover, no product
source change, and no live authority. Destination
`/home/sl/baton-instances/native-coordination-pilot-w321608-1` (fresh,
retained). Two stages only (implementation + independent review), separate
verify/review receipt actors, `baton.slaw` as human owner, dedicated diagnostic
ownership. An unresolved production value stays explicit and non-executable.

## 2026-10-18 — claim 325968: the pins, revalidated at the selected source

Everything below was read from the tree at `14e52d80` in this claim, not
carried over from the W321690 packet, and two pins moved:

* **`git diff --stat 372281f4 14e52d80 -- v12/` is NOT empty.** `2aa8ca56`
  added `v12/python/tools/worker_visibility.py` (1004 lines) and its tests
  (1426). So the W321690 packet's "record-only commits since" line does not
  hold at this source, and this packet re-states the provenance rather than
  inheriting it. `worker_visibility` is a separate tool and is **not** one of
  the thirteen `stack_command` subcommands — the installed surface is
  unchanged at thirteen.
* **The submission schema to pin is `baton.v12.job-submission/2`**, not `/1`.
  `documents.SUBMISSION_SCHEMAS` accepts both, but
  `SUBMISSION_LIMITS_SCHEMAS` is `('baton.v12.job-submission/2',)` — the
  `execution_limits` member a Job uses to carry the selected 3600 s provider
  turn exists only in `/2`. A `/1` submission cannot express the owner's
  selected limit at all.

Unchanged and re-read: thirteen subcommands; `bootstrap` REQUIRED nine /
OPTIONAL seven / `owner_participant` with grants `approve`,`integrate`,`close`;
`CURRENT_GENERATION` 1 with 3600/900/1800/300 and bounds 1/86400; authority
schema 6; `baton.v12.stack-instance/1`; `baton.v12.instance-recovery-set/3`.

**Two product facts that decide the packet's shape.**

1. `bootstrap`'s own validator makes the **integration role optional** —
   "owner 2026-09-20T14:57:48Z (W202663, the PR model): integration is a human
   act or an explicitly submitted ordinary Job, never an obligatory worker".
   So the two-stage pin W321690 established by driving it is also the
   product's own configured position, not a workaround. The `integration_profile`
   *document* is still REQUIRED at install, and its `integrator_participant`
   must therefore be named even though this Job submits no integration stage.
2. `bootstrap` **defers `jobs` and `workers`**: a fresh installation configures
   neither, because a worker's `deployment` carries a digest-sealed input
   manifest naming the Authority and the Work, which cannot be written before
   the instance exists. Preparation is therefore **two passes**, and the packet
   says so rather than pretending one command composes everything.

**No total or cleanup reserve exists as a product setting.** T325959 asks for
"3600s provider limits with total/cleanup reserves". `execution_limits` says in
its own words that each value is a per-invocation ceiling and that "none of
them is a cumulative allowance, a remaining balance, a budget the Job spends
down, or a limit on how long an agent may work in total"; cumulative accounting
and per-role pools are deferred. A Job can express exactly two members —
`provider_turn_seconds` and `verification_command_seconds`. The packet
therefore pins those two and states the total and the cleanup allowance as an
**operator-side wall-clock envelope**, explicitly not a configured limit. The
only teardown number in the product is `oci.stop_vector`'s `seconds=30` stop
timeout.

## 2026-10-18 — claim 325968, continued: the FINDING arrived mid-claim and changed the shape

`FINDING.md` and `PLAN.md` appeared in this dossier during the claim (written
at 13:56, after my first read found the directory empty). I read both before
handing off, and one instruction materially changed the deliverable: **"Do not
leave routine values as another owner-choice questionnaire: owner delegates
resolution here."** The first cut of this packet left 47 sentinels. The
delivered packet resolves every routine value and keeps exactly two classes of
unresolved value, each named with its evidence:

* **`BUILD:` (5)** — digests that are build outputs: the packaged stack distro
  identity, the two worker image digests, the pool's runtime-profile and policy
  digests, and the integrator instructions digest. Each carries its concrete
  separately-selectable command in the document itself, and the FINDING is
  explicit that such a build "must be described as a concrete separately
  selectable command, not silently performed".
* **`READBACK:` (6)** — values supported preparation generates: the authority
  UUID, each principal, the policy generation, the Work id, each role's input
  manifest, and the Job's `input_digest`.

Resolved with evidence rather than asked about: `retention_policy_digest` =
`sha256:0f4cd2d13c46e81cb6e721119e48b342efb3a7a0d831e241c429601aa2eae45a`,
**recomputed this claim** as the sha256 of `v12/instance-retention.md` (the
same value the shipped `v12/instance-inputs.json` names); `engine: docker`,
because `/usr/bin/docker` is present on this host and `podman` is not;
`workspace_group: 1000` from this host's own gid; `workspace_capacity.max_bytes:
167772160`, twice `source_boundary.MIN_WORKSPACE_BYTES`; `network: none` with
`credential_sources: null`, `credential_slots: []`, `credential_profile: {}`,
which is what "no provider call is selected" looks like in a document rather
than in prose; the owner route `owner` and the dedicated diagnostic route
`diagnosis` with handler `baton.diagnostician-pilot`; `checkpoint_profile: git`;
generations `1`/`1`; and the four receipt/owner/worker addresses as new native
identities rather than copies of the v11 ones.

## The non-executability claim changed twice, and the run decided it both times

This is the part worth reading. My first cut asserted that `bootstrap.held`
refuses the input while the sentinels stand — **the run said it accepts**:
`held` validates presence and relationships, not value formats. I corrected the
claim to `bootstrap.validated`, which did refuse, naming the retention policy
digest. Then resolving that digest — as the FINDING instructs — made
`validated` **accept** the configuration pass one would emit, and the run said
so again.

So the delivered packet states what is actually true: with the routine values
resolved, no validator gates pass one. The gates are `bootstrap.admit`, which
refuses an install with no built runtime ("needs a built runtime; name it with
`--distro`") and one whose distro is not there — both driven in the
verification run — plus the two worker images, which do not exist, and the
owner's launch selection, which is not this Work's.

## Delivered

* `INSTANCE-PACKET.md` — the operator packet: instance and preflight,
  provenance, the two-stage Job and why it is the control, participants and
  routes, the eleven ordered commands over two bootstrap passes, limits, the
  task and check, what is resolved and what remains, result/recovery/rollback,
  and the boundaries.
* `configuration/task.json` — fully pinned, schema `baton.dogfood-task/2`,
  validated through `dogfood_operator.held_task`; sealed canonical digest
  `5ec48d4baf2020a8ef972237444c5989cf8490dea23cc285dbfd3bc0508dc1bb`
  (1853 bytes). Its verification argv was **run against five candidates**:
  accepts a complete quickstart; refuses a missing section, a document under
  its length floor, a `TODO`/`TBD`/`FIXME` marker, and an absent file.
* `configuration/install-inputs.json`, `configuration/job-inputs.json`,
  `configuration/submission.json` — passes one, two and three.
* `verification/validate.py` + `VALIDATION.json` + five scenario records —
  **70 checks passed, 5 observed, the self-check failed for its own named
  reason, 0 unexpected, 0.165s.**
* `MANIFEST.json` binding all of it.

## Two pins that MOVED from the W321690 packet, re-read at the selected source

1. `git diff --stat 372281f4 14e52d80 -- v12/` is **not** empty: `2aa8ca56`
   added `tools/worker_visibility.py` and its tests, so the "record-only
   commits" line from that packet does not hold here. The installed surface is
   still thirteen subcommands; `worker_visibility` is not one of them.
2. The submission schema to pin is **`baton.v12.job-submission/2`**, not `/1`:
   `SUBMISSION_LIMITS_SCHEMAS` is `('baton.v12.job-submission/2',)`, so the
   `execution_limits` member carrying the selected 3600 s provider turn exists
   only in `/2`. A `/1` submission cannot express the owner's selected limit.

## What I did NOT do, and why

The FINDING authorizes a "deterministic disposable preflight" in a distinct
disposable path. I did not run `bootstrap.prepare` against a disposable root:
it composes an Authority and writes stores, and the same FINDING says no live
instance creation, while `admit` already refuses the install for want of a
distro I am not authorized to build silently. The destination preflight is
therefore read-only (it does not exist; its three reserved names are free), and
the configuration and refusal proofs are the validator-level ones the
verification run records. If the reviewer wants `prepare` driven in a throwaway
root with labelled preflight identities, say so and I will drive it there.

**Cumulative verification spending this claim:** nine read-only probes of the
product contracts (`stack_command`, `bootstrap` input and worker rules,
`single_worker._MEMBERS`, `documents` submission members and vocabularies,
`execution_limits`, `instance.layout`, `dogfood_operator` task rules,
`worker_image`, `admit`), four runs of the authoring script, and six runs of
the verification driver at 0.17–0.2 s each — three of them failing, on the
check's own length floor, the `held`-refusal claim and the
`validated`-refusal claim, each of which became a correction rather than a
sentence of prose. No install, no submission, no serving, no container, no
provider call, no credential read, no store write, no deployment, no product
source change, no raw SQL, and nothing that mutates this repository's history,
index or working tree.

## 2026-10-18 — claim 326141: revision 2, with the composition actually driven

Review 2026-10-18T20-17-05Z requested changes on four counts and every one was
right. Revision 1 is preserved unedited (its manifest digest as the review
published it: `f74a3daa…`); `revision-2/` is the corrected packet, bound by its
own `MANIFEST.json`.

**The driver now does what revision 1 only described.**
`revision-2/prepare.py` composes the packet end to end in a LABELLED DISPOSABLE
ROOT (`/var/tmp/w325959-preflight`) through the supported `tools.bootstrap`
entry point — the same one `just -f v12/justfile bootstrap` execs — and retains
the readbacks: **72 checks passed, 4 scenarios observed, the self-check failed
for its own named reason, 0 unexpected, 0.196s**, with
`selected_destination_untouched: true`. It refuses to run against the selected
destination or against a root that does not carry the label.

**Correction 1 — the five recipes did not exist.** `stack-distro`,
`worker-image ROLE=…`, `pool-policy`, `pool-profile` and `integration-bundle`
were my invention. The real surface, read from `v12/justfile` and the tool
CLIs this claim: `setup`, `build` (distro at `v12/python/build/out/distro`),
`bootstrap INPUTS DESTINATION [DISTRO] [EXTRA]`, `start`/`stop`/`status`/
`monitor DESTINATION`, `test-bootstrap ROOT`, plus
`python3 -m tools.worker_image --tag … [--engine --context --dockerfile
--platform]` and `python3 -m tools.pool add --deployment … --worker …`.

**Corrections 1 and 4 — the inputs are now reused with verified provenance.**
A prior prepared instance of this product
(`/home/sl/baton-instances/failed-reporting-w321528-324054/packet/`) holds a
complete validated worker deployment pair. Reused and **recomputed this claim**:
`policy_digest` is the canonical digest of that packet's `policy.json`,
`profile_digest` of its `runtime-profile.json`, `adapter_digest` of its
`adapter.json` (21 checks). The provider-backed pair is bound **by reference** —
`network: bridge`, `credential_slots: ["claude"]`, profile
`{"claude": {"provider": "operator-file", "reference": "w202663-development"}}`,
sources `/home/sl/.baton/credential-sources.json` whose existence is checked
and whose content is never read. The image digest is reused by reference with
its provenance and the exact re-validation command, which is an engine read
this preparation does not perform. Revision 1's `network: none` / no-credential
pair, which bound no workload that could do the task, is withdrawn.

**Correction 3 — the two routes `bootstrap` does not register.** Scenario 2
measures the gap first (before registration, `baton.slaw` claiming its own Work
is refused because the route resolves to nobody), then registers `impl`,
`rview`, `owner` and `diagnosis` and proves each by claim: the implementation
participant claims, hands off to `rview`, the reviewer claims, hands off to
`owner`, and **`baton.slaw` claims the Work its review ending handed on** with
`principal:baton.slaw` on the decision; a participant that does not handle the
route is refused; a dedicated diagnostic Work on `diagnosis` is claimed by
`baton.diagnostician-pilot` and an identical claim replays. The five per-Work
grants are made and read back, and the owner is proved to hold **neither**
`verify` nor `review`.

**Four faults of mine the run caught rather than my prose**, each now a
comment in the driver:

1. I expected pass one to create the Job and control stores. It does not — a
   compose-in-place pass makes the Authority, the record and the configuration;
   those two stores belong to the installed instance's manager. The check is
   corrected to assert their ABSENCE.
2. The dossier locator must be ONE FLAT SEGMENT ending in an **8-character**
   hex suffix. My first cut passed a path, my second a 12-character suffix, and
   the Authority refused both by name.
3. A changed `pool_generation` on a repeated Job-less pass is **accepted**, not
   refused: `bootstrap`'s preservation rule is about BINDINGS, and a Job-less
   install binds none. The real drift refusal is proved where bindings live —
   pass two, repeated with a changed `line_declared_base`, is refused and the
   emitted binding still names the original base.
4. `dogfood_operator.input_manifest` hardcodes the STAGED delivery shape
   (`baton.directory/1`), and the stage deployment refuses a descriptor that
   does not declare `baton.source-boundary/1`. There is no composer in the tree
   for the nominated-mount shape, so the manifest is ADAPTED from the prior
   validated instance's own manifest — Work reference, human contract and
   manifest id replaced, re-sealed with the canonical digest the manager
   recomputes — and then held to `check_manifest_structure`, the manager's own
   validator. The human contract's frozen schema is closed at five members; my
   first cut invented a `path` member and omitted `locator`.

**Named rather than smoothed over:** seven identities in that adapted manifest
(`resource_`, `network_`, `mount_`, `tool_`, `credential_policy_digest`,
`role_instructions_digest`, `toolchain_digest`) are repeated-hex placeholders in
the prior instance. They compose and pass the structure check, and before any
launch the owner's real documents must be digested in their place.
`revision-2/configuration/manifest-inputs.json` lists exactly which.

**The cleanup window is now quantified** (§6): ≤ 4500 s per turn-plus-
verification, ≤ 9000 s for one attempt pair, 30 s per runtime stop
(`oci.stop_vector` default), ≤ 120 s cleanup settle for two runtimes, so ≈ 2 h
45 m of operator window per attempt pair — advisory arithmetic, explicitly not
a configured limit, with the supervision procedure named command by command and
the honest statement that stopping a supervisor is not cessation.

**Cumulative verification spending this claim:** seven read-only probes (the
real justfile recipes, `worker_image` and `pool` CLIs, the prior instance's
packet and its digests, the manifest composer, the human-contract schema, the
dossier locator grammar), one authoring run, and seven runs of the preparation
driver at 0.16–0.2 s each — five of them failing, on each of the four faults
above plus one wrong working directory. No install into the selected
destination, no engine call, no provider call, no credential content read, no
image build, no submission, no `start`, no product source change, no raw SQL,
and nothing that mutates this repository's history, index or working tree.

## 2026-10-18 — claim 326225: revision 3, one coherent path and four corrections

Review 2026-10-18T20-29-02Z proved four faults in revision 2. All four were
real. Revisions 1 and 2 are preserved unedited; `revision-3/` is the corrected
packet with its own manifest and `FROZEN-INPUTS.json`. `revision-3/prepare.py`:
**83 checks passed, 4 scenarios observed, the self-check failed for its own
named reason, 0 unexpected, 0.207s**, `selected_destination_untouched: true`.

**R1 — I submitted the wrong input identity.** Revision 2 resolved
`input_digest` with a SHA-256 of the whole manifest; the reviewer proved it
unequal to `contracts.job_input_identity`, which projects out the role-specific
members first. The driver now calls the public function, records both values
side by side, and proves the projection's two properties (the worker image
digest does not move it; an included policy identity does). It also asks the
**runtime consumer boundary** — `stage_execution._disagreements`, which is
`single_worker._matches`'s own operand comparison: empty for both workers, and
non-empty when the Job names another input. And
`bootstrap.configuration(document, principals)` is now called with its real
two-operand signature and its emission **validated**; revision 2 passed
`principals` twice and merely noted the `TypeError`, which proved nothing.

**R2 — the documented command could not have worked.** Revision 2's step 9 told
the operator to run the install recipe a second time, and `bootstrap.admit`
refuses an installed destination carrying a distro, a justfile and an instance
selector. The corrected sequence is one installation (with the built distro),
then the **in-place configuration pass** (`--inputs` alone against the
installed state root) — which is exactly what the driver exercises: accepted,
repeated without change, the install-derived `workspace_storage`,
`launch_home`, `credential_home` and `nominated_source` preserved, and a
changed `line_declared_base` refused with the original binding intact. The
`pool add` step is **removed**: `tools/pool.py` takes a worker DOCUMENT
filename, not an id, and `bootstrap` already supplies both workers. And the
source-acquisition gap is now stated plainly rather than implied: the
disposable proof's nominated source is an empty directory, so acquisition and
base availability are unproven there and the operator must read the prepared
`repo/source` and confirm its head is the pinned base before configuring.

**R3 — a build described as a read.** `worker_image._main` builds, saves,
normalizes, loads and cleans an image. Calling it a "re-validation engine read"
was wrong; the packet and the driver now classify it as a build, say that a
read-only presence check is an engine inspect, and state that this preparation
performs neither.

**R4 — frozen inputs, and the gap named properly.** The consumed documents are
copied into `revision-3/inputs/` and digested in `FROZEN-INPUTS.json`, so
preparation reads an immutable boundary rather than a mutable path, and the
three content-derived digests are recomputed from the frozen copies. For the
seven repeated-hex identities the answer is no longer "the owner will do it":
no document for any of them exists in this tree or the frozen inputs and no
product operation composes one, and `dogfood_operator.input_manifest` says why
— "a tool that filled one in would be making a grant on an operator's behalf,
which is the one thing" it may not do. The packet records the split that
matters: `resource_`, `network_`, `mount_` and `tool_policy_digest` are **in**
the Job input identity and must be real documents before launch;
`credential_policy_digest`, `role_instructions_digest` and `toolchain_digest`
are excluded from it.

**Limits re-marked as the review required:** the 120 s cleanup figure is a
**proposed observation allowance**, not an observed cessation bound — no engine
cleanup was observed in any run here, and an unknown runtime retains its hold
rather than expiring. The 9000 s arithmetic is explicitly conditional on one
provider and one verification invocation per stage.

**Five faults of mine the run caught this claim**, each now a comment in the
driver: a `manifest_inputs["policies"]` key that revision 3's schema no longer
has; `bootstrap.configuration`'s real signature (two operands, not three); a
manifest sealed and then mutated, which `verify_manifest_digest` refused with
"a manifest that does not identify itself is not one"; the same mistake again
in the two projection-stability checks, which must re-seal their mutated copies
before calling the public function; and a leftover `refusal` reference in the
return value.

**Cumulative verification spending this claim:** four read-only probes (the
public projection and its excluded set, the consumer comparison site,
`bootstrap.configuration`'s signature, `pool`'s operands), one freezing and
authoring run, and eight runs of the preparation driver at 0.17–0.21 s each —
six of them failing, on the five faults above plus one wrong working directory.
No install into the selected destination, no engine call, no provider call, no
credential content read, no image build or inspect, no submission, no `start`,
no product source change, no raw SQL, and nothing that mutates this
repository's history, index or working tree.

## 2026-10-18 — claim 326286: returning INCOMPLETE, with the blocking facts established

Review 2026-10-18T20-37-30Z accepted the identity, image-classification and
frozen-input corrections and requires one composed installed-instance path.
I did not get revision 4 built in this claim. What I did establish is the set
of facts that was missing — every one of them read from the tree this claim —
so the next claim starts from them rather than re-deriving them. No revision 4
is published; revisions 1-3 are untouched.

**1. The per-worker source paths are NOT `repo/source`.**
`bootstrap.repository_plan(document, places)` with the two workers configured
plans four repositories, named from the worker ids:

```
target     <D>/repo/target.git        (bare)
workspace  <D>/repo/workspace
source-implementation-pilot  <D>/repo/source-implementation-pilot
source-review-pilot          <D>/repo/source-review-pilot
```

Worker-free (the install input) it plans only `target.git` and `workspace`,
which is exactly what the reviewer's `INSTALL-TRANSITION.json` showed. So every
revision so far named `nominated_source` as `<D>/repo/source`, which no
supported operation ever creates. **That is the concrete cause of the gap**, not
merely a missing step.

**2. `stack repository` cannot prepare them — it is read-only by design.**
`tools/stack.py:repository` says so in its own words: "NO REPOSITORY TOOL IS RUN
AND NOTHING IS WRITTEN. The layout is read from the filesystem and `HEAD` from
the file of that name". It is the *check*, not the preparer.

**3. The preparer is the OPERATOR, before bootstrap, and it is documented.**
`baton:work/records/2026/09/finding-v12-stack-launcher/OPERATOR-INDEPENDENT-REPOSITORY.md`
is the owner packet for exactly this. Its table assigns each worker's
`nominated_source` at `<D>/repo/source-<worker_id>` to "**you**, once per
worker", and its order section is explicit: *every path the configuration names
has to exist BEFORE `just bootstrap`*, because `single_worker._held` →
`nominate_source` proves each worker's source with an `lstat` and one
`O_DIRECTORY | O_NOFOLLOW` open and refuses a source that does not exist yet.
The documented commands are one mirror clone of the selected source to
`target.git` and one `--no-local` clone per worker source and for the
workspace, plus `mkdir -p` for the worker storage roots — separate repositories,
not worktrees, not hardlinked.

**4. So the sequence the packet must carry is five steps, not three**, and the
reviewer's refusal falls out of it: the operator creates the repositories and
worker roots at the pinned base; the install runs with the distro and the
worker-free input (and leaves those paths alone, which the owner packet states);
the Authority identity, policy generation and canonical target are read back;
the Work, dossier, routes, grants and input manifest are composed; and only then
the in-place configuration pass runs — **naming `integration_target` and
`integration_workspace`**, because `bootstrap.dropped_selections` refuses a
document that omits what the root is already configured with. Revision 3's
`configure-inputs.json` omits both, which is the exit-2 the reviewer proved.

**5. The policy precedence question has a concrete answer.** The frozen
`policy.json` is the prior pilot's own admission-gate document
(`baton.single-implementation-execution-policy/1`, "the caps the admission gate
enforces; W239528") declaring provider 900 / verification 30, while this
packet's Job names 3600 / 900. Reusing that digest as `policy_digest` therefore
declares caps that contradict the submitted Job. The resolution is to author a
proposed execution-policy document for THIS selection (3600 / 900) and use its
canonical digest, rather than inheriting a document that describes another
pilot's caps — which also answers the reviewer's point that a copied historical
digest is provenance, not compatibility.

**Exact remaining scope for the next claim** (one revision 4, coupled, no new
gate):

1. Author the proposed accountable documents for all **seven** identities —
   resource, network, mount, tool and credential policy, role instructions,
   toolchain — traced to the selected runtime profile, adapter, engine,
   `network: bridge` and the single `claude` credential slot, plus the
   execution policy of finding 5; digest each canonically and use those
   digests. The reviewer has ruled that preparing proposed documents is within
   the delegation, so the "a tool must not invent a grant" position from
   revision 3 is withdrawn for *proposed* documents; it still holds for
   anything presented as live authority.
2. Fix `nominated_source` to the planned `source-<worker_id>` paths and add
   `integration_target` / `integration_workspace` to the configure input.
3. One driver scenario, one disposable authority, in this order: the operator
   repository preparation (clones from this checkout at the pinned base into
   the disposable root — read-only on the repository, writes only under
   `/var/tmp/w325959-preflight…`, labelled a disposable representation of the
   operator's own documented step), install-in-place with the installer-derived
   fields bound through the public `workspace_bound` / `repositories_bound` /
   `storage_bound` helpers, the readbacks, routes, grants, Work, dossier,
   manifest, the in-place configure pass, the read-only `stack repository`
   check, each source `HEAD` proved to be the pinned base, the consumer
   `_disagreements` comparison, the submission, and the binding-drift refusal —
   with the generated artifacts written to evidence as the real configuration
   and submission rather than READBACK templates.
4. Verify the five frozen input hashes **before** any effect, and keep the
   120 s cleanup figure marked a proposed allowance.

**Cumulative verification spending this claim:** six read-only probes —
`repository_plan` with and without workers (the decisive one),
`workspace_bound` / `repositories_bound` / `storage_bound` /
`prepare_repositories` / `dropped_selections` signatures, `stack.repository`'s
body, the search that located `OPERATOR-INDEPENDENT-REPOSITORY.md`, and its
layout and ordering sections. No driver run this claim, no install, no engine
call, no provider call, no credential content read, no image build or inspect,
no submission, no product source change, no raw SQL, and nothing that mutates
this repository's history, index or working tree. The selected destination is
untouched and still does not exist.

## 2026-10-18 — claim 326316: the repository sequence is decided; revision 4 still owed

**Actual cause of this return: my turn budget, not missing authority.** Review
2026-10-18T20-41-30Z is right that research is not delivery, and revision 4 is
still owed. What this claim settles is the one question that was blocking its
design, and it settles it against current sources rather than historical prose.

**Finding 6 — the superseded clone-first prose, and the option that replaces
it.** The reviewer is correct that `OPERATOR-INDEPENDENT-REPOSITORY.md`'s
"Later owner interface ruling — 2026-09-16" supersedes manual pre-clone as the
normal workflow, and that `prepare_repositories` (1503-1565) **refuses an
existing path at any planned repository** and leaves it as it is. So my
claim-326286 checkpoint sequence — pre-clone, then a repository-producing
install that "leaves them alone" — is **false and is withdrawn**.

The explicit repository option that does make a coherent sequence is
`--no-repositories`, which the justfile's `EXTRA` operand passes through
(`just bootstrap INPUTS DESTINATION DISTRO "--no-repositories"`). With it the
installation prepares no repository and the operator's own are left untouched
by construction rather than by assumption. The alternative — a
repository-producing install — can only prepare per-worker sources if the
install input already carries the workers, and that collides with Finding 7.

**Finding 7 — why a repository-producing install cannot carry these workers.**
Measured this claim:

* `check_work_id` accepts any `<8 hex>-W<n>`; it does **not** require the
  Authority's own UUID prefix, so the operator may name the Work id in advance.
* But a worker's nested `input_manifest` must carry
  `work_ref.authority_uuid` equal to the worker's own `authority_uuid`
  (`single_worker._held`), and `bootstrap._compose` fills in only the worker's
  top-level `participant`, `principal`, `authority_store`, `authority_uuid` and
  `launch_role` — never the nested manifest. The UUID is generated by the
  installation.
* Therefore a fresh install that carries workers would need a manifest naming
  an Authority identity that does not exist until that same command runs.

So the two coherent sequences are: **(A)** install with `--no-repositories`,
the operator having prepared `target.git`, `workspace` and
`source-<worker_id>` at the pinned base (owner-run, labelled, unexecuted by
me), then the in-place configure pass; or **(B)** a repository-producing
install with no workers, which never prepares the per-worker sources at all and
therefore cannot reach a launch. **(A) is the sequence revision 4 must carry.**

**Finding 8 — `prepare_repositories` refuses a mismatched source name.** With
revision 3's document it refused by name: *"this input asks for repositories to
be prepared AND names different ones: workers[implementation-pilot].
nominated_source is …/repo/source"*. That is the same defect Finding 1 named,
seen from the other side, and it confirms the corrected value must be the
planned `…/repo/source-<worker_id>`.

**Finding 9 — the controlled runner boundary the review authorizes exists as an
operand.** `prepare_repositories(document, places, *, runner=None, …)` takes
the clone runner, so revision 4 can record the exact composed clone commands
through a recording runner — proving the planned set and the command
composition — without any repository mutation, and label precisely what that
proves versus what needs the owner's own run. A recording runner was exercised
this claim and recorded zero calls only because the refusal in Finding 8 came
first, which is the correct order.

**Exact remaining scope — revision 4, unchanged from review 20:37:30 plus the
above.** (1) `nominated_source` → the planned `source-<worker_id>` paths;
`integration_target` and `integration_workspace` carried in the configure
input. (2) The seven proposed accountable documents plus the 3600/900 execution
policy, canonically digested. (3) ONE driver scenario in ONE disposable
authority on sequence (A): frozen-hash verification before any effect, the
recording-runner repository proof, the install-in-place with installer-derived
fields bound through `workspace_bound`/`repositories_bound`/`storage_bound`,
the readbacks, routes, grants, Work, dossier, manifest, the in-place configure
pass, the read-only `stack repository` check, the consumer `_disagreements`
comparison, the submission, and the binding-drift refusal — writing the real
generated configuration and submission to evidence. (4) The packet's
owner-run commands labelled and unexecuted.

**Cumulative verification spending this claim:** the `prepare_repositories`
source (1503-1565) and the superseding ruling read in full, one probe that
exercised `check_work_id`, `repository_plan` and `prepare_repositories` with a
recording runner in a disposable temporary root, and the manifest cross-check
rule re-read. No driver run, no install, no engine or provider call, no
credential content read, no image build, no submission, no product source
change, no raw SQL, and **no repository mutation of any kind** — the recording
runner executed nothing and the refusal came before any effect. The selected
destination is untouched and still does not exist.

## 2026-10-19 — baton.codxpc claim 328521: revision 4 prepared for independent review

Recovered after owner release E328516 (incidents 75/76; prior managed stack
stopped). Read canonical Work, claimed at E328521, complete handoff through
E328521 and thread T325959/M325959; no continuation message was omitted.
Current scope remains FINDING/PLAN and reviews 20:37:30, 20:41:30, 20:44:22.
An unfinished revision-4 draft and dossier-local scratch from claim 326343
already existed. Preserved those inputs and prior revisions; finished the draft
under this claim. Prior claim's elapsed verification total is unknown, not zero.
Reviewer FINDING/PLAN/reviews and all product files remain untouched by this turn.

Revalidated current HEAD 03b94fc80744671150cca1997712ee95a6537df5 against selected
14e52d80679de5e844f72324df632da5e01cf393: v12 committed diff is empty and current
v12 working-tree diff is empty. Selected destination remains absent. Read current
bootstrap repository runner, installer options, public authority creation and
job-manager submission interface; no old clone-first/normal-install assumption.

Delivered revision-4/INSTANCE-PACKET.md, prepare.py, owner_operations.py,
verify_pins.py, accountable frozen inputs/templates, native dossier templates,
and actual disposable generated artifacts with MANIFEST.json. The seven policy
identities are content-derived proposals; execution policy is consistently
3600/900. Input hashes and derived policy/profile/adapter identities are checked
before effects. Source paths are source-<worker_id>; one explicit no-repositories
installation joins registration, scoped grants, dossier, task, manifest, in-place
configuration and submission artifact in one authority. Second install and binding
drift refuse; binding drift preserves configuration bytes. The owner driver uses
the same registration/composer, with real read-only Git prechecks and no simulated
claims or diagnostic placeholder Work. It is proposed and was not invoked here.

Artifact inspection caught additional inherited defects before handoff: default
create_work contract was v11 with deployment-wide scope; manifest record_binding
still named an old dossier with repeated-hex hashes; generated pretty task JSON
was not the exact staged manifest-bound byte sequence. Corrected to explicit
v12-assignment-1, scope:native-pilot-quickstart (diagnosis has its own scope), native
flat dossier binding with exact finding/plan hashes, and exact staged task bytes.
Added final readback/assertions. No policy specification changed.

Evidence: revision-4/evidence/run-328521-4/PREPARATION.json and generated/:
60 checks, one coherent successful scenario, one intended self-check failure,
zero unexpected, 0.060 seconds. PIN-REFUSAL.json proves changed frozen input
refuses before root/evidence creation (0.118684521 seconds). ARTIFACT-CHECK.json
checks script syntax and actual task/dossier/manifest/worker/submission binding
(0.005188029 seconds). Earlier runs 1/2/3 are preserved: respectively 58/58/59
checks, 0.062/0.060/0.064 seconds. Cumulative measured driver time this claim
0.246 seconds; focused pin/artifact checks add 0.123872550 seconds, total measured
verification 0.369872550 seconds. Imports, reads and authoring are not included in
that measured sum. Earlier authors' estimates and unknown recovered-claim spending
remain above; no invented lifetime total.

Proof limitations are explicit: controlled recording Git runner and nonfunctional
repository layouts, mocked bundle identity and external-checkout location; real
bootstrap copy/configuration/authority behavior. No real Git objects, packaged
runtime, engine/image/provider compatibility, live cleanup or quickstart usefulness
is certified. The existing bundle predates selected source and is not accepted;
packet supplies separately selectable setup/build/identity/install/submit commands.
Fresh bundle provenance, image presence and actual generated production identities
require later selected operations and review. No selected-instance write, build,
engine/provider, credential content, admission/serving, raw SQL, product edit or
mutating Git operation occurred. Temporary preflight roots /tmp/w325959-preflight-
328521-{1,2,3,4} are retained; original dossier-local scratch is untouched.

Next: independent review of revision 4 through baton.bug, then parent W321608
consumes the disposition before any owner execution selection. No remaining
implementation change is asserted necessary by this author; no acceptance or
launch readiness is claimed. Required human Git checkpoint remains pending after
independent acceptance. Suggested message: `docs: prepare instance-specific native
v12 pilot packet`. No commit has been made or inferred.
