# W361910 — implementer progress

## claim361943 — versioned implementation-to-review template resolution

Answers `FINDING.md` and DESIGN SCH-1a under handoff361941. Base commit
`182c8f943cdfc12134ae2d082d9afe98189efe90`. Every path this candidate touches
was clean in the working tree at claim start; the candidate is
`candidate-361943/` and the canonical tree is left byte-unchanged.

### Read position at claim start

`detail work=W361910`, `work-events work=W361910` through seq361943 and born
thread `T361910` read complete (one message, no pagination). Dossier
`FINDING.md`, `PLAN.md` and `review-2026-10-26T17-00-30Z.md` read in full.
DESIGN SCH-1a re-read at `v12/DESIGN.md:660`. Source revalidated against the
current tree rather than against the FINDING's evidence list:
`job_manager/documents.py`, `submission.py`, `fresh_attempt.py`,
`execution_limits.py`, `review_driver.py`, `scheduler.py`,
`tools/job_manager.py`, `contracts/pod.py`, `contracts/canonical.py`,
`worker_manager/boundaries.py` and `v12/worker/claude_agent.py`.

### The gap as it actually stands

`tools/job_manager.py submit` reaches `documents.read_submission`, which
requires a fully normalized `baton.v12.job-submission/{1,2}` document: per-Job
`input_digest`, `policy_digest`, `test_scope`, `terminal_policy`, and per-stage
`kind`, `work_id`, `profile_name`, `profile_digest` and `depends_on`. Nothing
in the package resolves that document from a task description, so ordinary
creation is operator-authored — `v12/w144813-submission.example.json` is that
authoring by hand, with six `null` members an operator has to fill in, and
`boundaries.text` refuses every one of them as written.

`tests/job_manager/test_review_driver.one_work_submission` records the part
hand-authoring gets wrong: the package's own default fixture names TWO Works
across one Job's implementation and review stages, "which the generic parser
admits and the line provider can never attach".

### What is delivered this round

Three files, two of them new. Candidate `candidate-361943/`, manifest
`834e88af1eb98106adbfe4799baac83de1b31d56a8f84502d93dd455c85a7277`, which
records each member's base digest beside its candidate digest.

| path | base | candidate |
| --- | --- | --- |
| `v12/python/src/baton_v12/job_manager/templates.py` | new | `765c583f27a407bebce2b5979c76ecccb922a600058cbc05413c5ded93e26624` |
| `v12/python/tests/job_manager/test_templates.py` | new | `ee2903ff855312907b3c3aae3fd8cbf3a9edc27956c203f173b907131a4596d9` |
| `v12/python/src/baton_v12/job_manager/__init__.py` | `7fa34e59a272ebe17054fe48963ac5dfc6dd74ef81fe7aacb44a642ba8cff8bc` | `41e31dc0ef9b9a4e4d4e54e42f938e503db6136fc2bc520c79f4930b865c99f1` |

The `__init__.py` change is the export block and its `__all__` entries and
nothing else. No existing test file is edited, no existing assertion is
changed and no product file other than the package export is touched.

### The shape, and why it is this one

**One frozen table compiled into the build, not a template format.**
`TEMPLATES` holds exactly one entry,
`baton.v12.job-template.implementation-review/1`, declaring its stages, their
roles, the gate between them, what each one consumes and produces, the
terminal policy, the single permitted override and the
completion/correction/failure rules. A second revision is a second entry, the
way `execution_limits.GENERATIONS` adds one — never an edit, because an edited
entry is the reinterpretation the structure exists to prevent. `resolve` takes
a request and a deployment configuration and nothing that could introduce a
stage, so there is no template language, no workflow editor and no registry a
caller can extend.

**Three documents, and each member has exactly one owner.** A REQUEST is the
caller's: selection, task, source, scope, acceptance and permitted overrides,
owned member by member as a submission is. A CONFIGURATION is the
DEPLOYMENT's: which template a bare request means, and which runtime profile
each role's installed workers carry. That split is SCH-1a's "Deployment
supplies workers, credentials and capacity; these are not operator-authored
per-Job manifests" — `scheduler.reserve` matches a stage's
`(lane, profile_name, profile_digest)` against the installed pool, so an
operator who typed a profile digest would be configuring the pool from a Job,
and an invented one would surface as "no eligible review worker" long after
anybody could tell why. A RESOLUTION is this build's own answer.

**The exact version and where it came from are separate members.** "A
configured default may save typing but MUST NOT hide that selection", so the
answer carries the version either way and an `origin` of `request` or
`configured-default` beside it. A misconfigured default is proved against the
configuration itself rather than against the first request that omits a
selection.

**Both stages name ONE Work, and that is the defect templating actually
fixes.** `test_review_driver.one_work_submission` already records that the
package's default fixture names two Works across one Job's two stages, "which
the generic parser admits and the line provider can never attach, because a
line is one `(authority_uuid, work_id)` pair and its reviewer is an assignment
of that same Work". A generic document parser cannot refuse that — two Works
is legitimate in some other submission — so the only place it can be refused
is a template that knows what one development line is. The request names one
Work and there is no member that could introduce a second.

**The submission is proved by its real owner before the answer exists.**
`resolve` runs the composed document through `documents.owned_submission` and
then re-derives the template's declared dependency graph FROM THE NORMALIZED
RESULT and refuses if the two disagree. So "this resolution is submittable" is
a fact rather than an intention, and a defect in the composition surfaces at
the request that caused it rather than at whatever later call tried to submit
it.

**A request that overrides nothing resolves to a `/1` document.** The
`execution_limits` member is absent rather than present-and-empty, so the
exact schema, member set and durable identity this pipeline already admits are
what comes out; only a request that configures a ceiling resolves to `/2`.
Rewriting every Job as `/2` would give one intent two identities.

### Every rule word is reported, not decided a second time

`completion`, `correction` and `failure` carry words their owning modules
already decide: `review_driver.VERDICT_OUTCOMES`,
`review_driver.FINDINGS_OUTPUT`, `documents.CORRECTION_ENDINGS`,
`documents.TERMINAL_POLICIES`, `documents.STAGE_STATES` and
`fresh_attempt.ADMIT_KIND`. Cases assert against those owners rather than
against literals, so a template that drifted from a lifecycle it does not own
fails. The one name that has to be spelled rather than imported is the
candidate output `proposal`: `v12/worker/claude_agent.py` declares
`IMPLEMENTATION_OUTPUTS` and nothing from `baton_v12` travels into that image,
and `tools/authoring_baseline.PROPOSAL_OUTPUT` is in `tools`, which the package
cannot import. Two cases hold it to both — one imports the host-side constant,
the other reads the adapter's own literal out of its source with `ast` rather
than reproducing the container's `sys.path` layout for the whole suite.

### What it refuses, every one driven

Unknown explicit version, naming what this build holds; a configured default
this build does not hold, refused for a request that named a version too; a
non-text version; either document's schema, by equality. Missing `task`,
`source`, `scope` or `acceptance`; an unrecognised request member; a missing
`job_id`, `work_id`, `statement`, `input_digest` or `policy_digest`. A scope
path that climbs out of the repository, is absolute or names one place twice
(reached through `check_relative_path`, not restated). An empty or duplicated
acceptance list, and prose past its bound. A request carrying a secret,
refused AS one with code `secret-leak` before the structural fault that is
also present. A forbidden override, refused naming what the template permits
rather than with the generic "member not named". A present `null` for
`overrides` or for `execution_limits` — an absent member and a present null are
different intents, which is the correction `documents._job` already carries one
level down. A ceiling out of range, fractional, boolean or textual, and an
unknown limit setting. A deployment that installed no reviewer, named by role;
a profile key that is not a stage kind. And in the table itself: a role gating
on a role the template does not carry, a role consuming a result no role it
depends on produces, a role consuming from a role it does not gate on, a
self-gate, a repeated role name, two roles of one stage kind, a kind outside
`documents.STAGE_KINDS`, more roles than a Job has stages, no role at all, a
terminal policy outside the vocabulary, a permitted override nothing resolves,
and a missing or extra declaration member. Every registered template is held
to that rule at import, so a bad entry fails where it is written.

### Evidence

`evidence/claim-361943/`, with `HOW-THESE-WERE-RUN.txt` giving the exact roots
and commands. The canonical tree is not edited, so every run is on a
disposable scratch root built from the canonical bytes, and the candidate root
is that same root with `candidate-361943/v12/python` unpacked over it — so a
base/candidate diff compares bytes and not environments.

- **Focused suite** `tests.job_manager.test_templates`: **78 cases, OK**.
- **Whole `tests/job_manager`**: **1255 cases, OK** on the candidate; the same
  suite on the base root is **1177 cases, OK**, and the difference is exactly
  these 78. `test_fresh_attempt`, `test_submission`, `test_execution_limits`
  and `test_review_driver` are inside that run unchanged, which is what
  "preserve old submission contracts and fresh-attempt behavior" is proved by.
- **Three package-surface sweeps** (`test_dependencies`, `test_text_sweep`,
  `test_contracts_inventory`): **89 failures on base and 89 on candidate, and
  the two lists are byte-identical**.
- **Whole `tests/manager`**: 4786 cases, 169 failures and 90 errors on **both**
  roots, and `MANAGER-BASE.txt`/`MANAGER-CANDIDATE.txt` are byte-identical at
  259 lines. These are pre-existing in that root and this candidate adds none;
  they are **not** asserted to be failures in the canonical checkout, because a
  scratch root is not a Git checkout and has no engine, instance or state root.
- **`tests.tools.test_packaging` + `test_version`**: identical single failure on
  base and candidate scratch roots (`test_version` cannot find a checkout from
  a non-checkout root). The same two suites in the **canonical** tree fail one
  different, pre-existing case — `test_every_subcommand_this_command_serves_is_offered`
  asserts `attempt-diagnostics` is offered by the **installed**
  `baton-v12-stack`, whose build predates that verb. Recorded as an
  operational observation; it is outside this Work's scope and no byte here
  touches it.

### Limits, stated rather than left to be found

- **Nothing in the product calls `resolve` yet.** That is the decomposition:
  the manager-owned admission that consumes a resolution and the thin CLI that
  requests it are W361912's, and the PLAN allocates them there. What is proved
  here is that the document a resolution produces is the one `submit`, the
  projection and the limit readers actually take.
- **The "verification contract" this resolution carries is the bounded test
  scope plus the effective per-invocation ceilings, and not a command.** Which
  verification command a worker runs is `v12/worker/claude_agent.py`'s and is
  not a submission member; a resolver that named one would be authoring the
  worker's workload.
- **No provider, engine, Authority, instance or deployment was reached.** The
  Job stores these cases open are the disposable SQLite files
  `fixtures.JobManagerCase` creates under a temporary directory, and the
  operations object is `test_status`'s own strict fake. Whether a resolved Job
  SUCCEEDS is not proved — only that it resolves, normalizes, records,
  projects its gate and reports its ceilings.
- **Only one template version exists, so the "a changed default cannot
  reinterpret an old Job" property is proved by the two mechanisms that
  actually carry it** rather than by a second revision invented for a test:
  the resolution pins the exact version and is byte-reproducible from it, and a
  changed deployment resolves a visibly different document whose submission
  `submission._unclaimed` refuses on the identity the recorded Job holds — with
  the recorded Job's own profile digest asserted unchanged afterwards.
- `submission_id_for` derives `sub-<job_id>`, the same spelling
  `fresh_attempt.admit` uses. A request may still state one.

### Cost

Read-only research across `documents`, `submission`, `fresh_attempt`,
`execution_limits`, `review_driver`, `scheduler`, `projection`,
`contracts/{pod,canonical,secrets,manifest}`, `worker_manager/boundaries`,
`tools/{job_manager,bootstrap,authoring_baseline,next_run_bindings}`,
`v12/worker/claude_agent.py`, `v12/DESIGN.md`, `AGENTS.md` and the existing
`tests/job_manager` fixtures. Test runs: the focused suite five times during
development, two of them failing — one on my own wrong assumption that a `/1`
submission leaves no `job_execution_limits` row, which `submission._job`
writes for every Job on purpose, and one on a refusal message that named the
forbidden override without naming the permitted set, which was a real product
gap and is now a product refusal of its own. `tests/job_manager` whole four
times (once on the base root, three times on candidate bytes); the three
surface sweeps once on base and twice on candidate bytes; `tests/manager`
whole three times at ~243s each (once base, twice candidate);
`tests.tools.test_packaging` plus `test_version` once on each of the three
roots. One earlier discovery run was discarded rather than recorded: the first
scratch root dropped the `v12` directory level, so 354 suites failed on a
repository asset resolved by `parents[4]`, and that is a property of where the
copy sat rather than a result. No live provider, no engine, no total
manufactured.

### Boundaries

No Git operation of any kind, in the repository or in the scratch roots. The
canonical `v12/python` tree is byte-unchanged — `git status --porcelain --
v12/python` is empty — and the reviewer's dirty `v12/DESIGN.md` and every
other pre-existing dirty record are preserved untouched. Per the PLAN's split
I wrote only `candidate-361943/`, `evidence/claim-361943/` and this file;
`FINDING.md`, `PLAN.md` and the reviews are the reviewer's. No live provider,
engine, credential read, deployment, install, instance operation or cutover.
No store opened, copied or traversed outside the disposable ones these cases
create. The scratch roots under `/tmp` hold copies only and are not
repositories.

## claim362249 — R1, R2 and R3 corrected and driven

Answers `review-2026-10-26T17-46-15Z.md` under handoff362245. Base commit
`182c8f943cdfc12134ae2d082d9afe98189efe90`, unchanged. At claim start the three
members of `candidate-361943/` and its `MANIFEST.json` were re-hashed and all
four match what that manifest and the reviewer's
`evidence/review-362222/HASHES.json` record; the scoped status of
`v12/python` was empty. `candidate-361943/` is preserved untouched and the
corrected candidate is `candidate-362249/`.

**All three findings are real and all three are reproduced as cases.** The
reviewer's `probe.py` is the better part of this round. R1 in particular is a
defect my own 78 cases were written around: I asserted that pinning the
generation in the answer made the numbers stable, and what it actually made
stable was the PROSE. Nothing carried the pin to the consumer.

### Read position

`detail work=W361910`, `work-events` through seq362249 (no pagination,
`next_after` null) and thread `T361910` complete — still one message at
seq361910, no newer discussion. Current `FINDING.md` including its
2026-10-26T17-46-15Z section, `PLAN.md`, `PLAN-HISTORY-362222.md`, both
reviews and all of `evidence/review-362222/` read in full, including
`probe.py`, `PROBE.stdout`, `RUNS.json` and `HASHES.json`.

### What is delivered

The same three paths, corrected. Candidate `candidate-362249/`, manifest
`fd92f115bc32975efde567adfb2e1fa9b7273427297a84bce24884192b61f3b1`, which
records each member's base digest, its candidate digest and its digest in
`candidate-361943` — all three changed.

| path | base | candidate-362249 |
| --- | --- | --- |
| `v12/python/src/baton_v12/job_manager/templates.py` | new | `8a93bd299f119620b741d71e11b44aac1bae8c7a972f26e50083962290ef8f3a` |
| `v12/python/tests/job_manager/test_templates.py` | new | `46da84a8c150da327a97228461f365b2e5cf072b7973ad79264104c344aa7494` |
| `v12/python/src/baton_v12/job_manager/__init__.py` | `7fa34e59a272ebe17054fe48963ac5dfc6dd74ef81fe7aacb44a642ba8cff8bc` | `dca5dfa59c02ddfa8806fd989723112aacda7134598c90dc35d3ea8c7331ca34` |

`candidate-361943/` and its manifest are preserved byte-untouched. The
`__init__.py` change is still the export block and its `__all__` entries and
nothing else; no existing test file is edited and no existing assertion
changed.

### R1 — a resolution is spendable only while this build still produces it

**The finding is exactly right and my own claim was the defect.** The
resolution reports ceilings resolved under `CURRENT_GENERATION` at resolve
time, and `submission._job` stamps a Job's generation from that same constant
at submit time. Nothing joined the two. I had written a case called
`test_the_generation_this_build_admits_is_pinned_in_the_answer` whose docstring
said "a later default change cannot move these numbers" — and what it cannot
move is the numbers in a saved document, while the Job the store admits moves
anyway. That case is renamed and its docstring says so.

The correction is `submission_for_admission(resolution, *, generation=None)`:
the one supported way to take the document out of a resolution. It refuses
when the resolution's pinned generation is not the one the consumer will admit
under, naming both and ending "Nothing has been submitted"; `generation`
defaults to `execution_limits.CURRENT_GENERATION`, which is literally what
`submission._job` writes, so the default compares against the real consumption
boundary rather than a restatement of it, and a consumer holding its own fact
passes that instead.

**It refuses rather than preserving, and that is a scope decision.**
Preserving would mean handing an admitted generation to `submission.submit`,
and that is the manager admission W361912 owns. The review permits either.

**And the check is not only about limits.** A resolution is consumable when
this build, now, resolves the resolution's own preserved request to these
exact bytes. The re-derivation is reconstructed from the resolution itself —
pinned version, task, source, both scopes, acceptance, overrides, and the
profiles its stages name — so a moved default, an edited derived member and a
changed template declaration are one contract with a separate reason each.
`_without_origin` excludes the selection origin, because consuming names the
version explicitly and must not depend on today's configured default; the
origin is instead held to `SELECTION_ORIGINS` directly, so it is not the one
member nothing checks.

**The boundary is stated rather than papered over.** The members a resolution
merely PRESERVES — acceptance, task statement, selected work scope — reach
nothing derived, so a resolution carrying different ones is a resolution of a
different request that this build produces perfectly well, and consuming it is
correct. `resolution_digest` is what binds a consumer to exact bytes. A case
asserts that directly rather than leaving it to be discovered.

### R2 — a registered template cannot be written to, at any depth

Confirmed and closed. `template_of` returned `TEMPLATES[version]` itself, so
one supported lookup changed what every later resolution of that version
delivered. **Tuples were the mistake in my reasoning**: a tuple of dicts
freezes the sequence and nothing in it, so the roles could not be appended to
and every one of them could still be rewritten member by member.

The authored literal is now private, `_frozen` turns every mapping into a
`MappingProxyType` and every sequence into a tuple at every depth, and
`_AUTHORED` is deleted — `_frozen` copied each mapping into a fresh one, so
after that statement no name in the module refers to a mutable member of a
registered template. The reviewer's exact assignment now raises
`TypeError: 'mappingproxy' object does not support item assignment`.

**And immutability alone would have made inspection unusable**, which is a
real consequence rather than a hypothetical: a proxy is something
`json.dumps`, `copy.deepcopy` and `contracts.own` all refuse. So
`template_document(version)` answers the same declaration as exact built-in
data — serializable, copyable, freely mutable and connected to nothing. Cases
drive both doors: nothing in the frozen declaration can be assigned, added to
or deleted; the detached view can be mutated, appended to and serialized and
changes no later resolution; and `check_template` still accepts every
registered entry and still refuses a bad consume/produce relationship when
handed one as a proxy.

### R3 — the two scopes are two authorities

Confirmed and closed. `scope` was one list documented as test-change paths and
copied wholesale into `test_scope`, so a request selecting the PRODUCT paths
its task covers was answered with a Job granting test-change authority over
those product paths — and the selected work scope existed nowhere in the
resolution.

The request's `scope` is now a closed two-member document: `work` is what the
task covers, the selected scope SCH-1/SCH-1a carry and a reviewer and an
integrator read a proposal against; `tests` is the narrower thing
`documents._job` means by `test_scope`, which AGENTS.md makes the
case-specific authority for editing tests. Only `tests` reaches the
submission. `work` is non-empty — a task that covers nothing has no selected
scope — and `tests` may be empty, because a Work that changes no test is the
ordinary case; the refusal for an empty `work` names which member may be
empty, so a caller who confused the two is told. Both are held to
`check_relative_path`, deduplicated and bounded. Neither is enforced here.

Cases prove the two differ and are both retained, that a product work scope
grants no test scope, that changing `work` moves the resolution digest and NOT
the submission signature while changing `tests` moves both, and that the
closed-member refusal still names an unrecognised `test_scope` key.

### Evidence

`evidence/claim-362249/`, with `HOW-THESE-WERE-RUN.txt` giving the roots and
commands and a before/after table for the three counterexamples.

- **`tests.job_manager.test_templates`**: **108 cases, OK** (78 before).
- **The reviewer's own focused set** — templates plus `test_submission` plus
  `test_execution_limits`: **167 cases, OK**, where review-362222 recorded 137.
- **Whole `tests/job_manager`**: **1285 OK**, against 1177 OK on the base root.
- **`probe-corrected.py`**: the reviewer's three constructions re-aimed at
  these bytes, with its header naming exactly which lines differ from
  `review-362222/probe.py` and why. `saved_resolution_consumption.refused` is
  true with the generation message; the lookup assignment raises; the work
  scope holds the product path and `test_scope` is empty.
- **Three package-surface sweeps**: 89 failures on base and candidate,
  byte-identical lists.
- **Whole `tests/manager`**: 4786 cases, 169 failures and 90 errors on both
  roots, byte-identical 259-line lists. Not required by the review; run
  because this round changes the exported surface. Pre-existing in that root
  and **not** asserted to be canonical failures.

### Limits, stated rather than left to be found

- **`submission_for_admission` answers "would this build still produce this",
  not "has anybody edited this".** See R1 above; the purely preserved members
  are outside its reach by construction and `resolution_digest` is what binds
  exact bytes. A case asserts this rather than hiding it.
- **The request contract changed shape in place rather than gaining a
  version.** `scope` was a list in `baton.v12.job-template-request/1` and is
  now a two-member document under the same name. Nothing in the product
  consumes that schema — W361912 is gated and no deployment calls `resolve` —
  so there is no reader to tell, and minting `/2` for a document no caller
  exists for would record a migration that never happened. If the reviewer
  prefers the version bump, it is a one-line change.
- **A frozen declaration is not JSON.** `template_of` is the immutable
  identity-stable answer and `template_document` is the serializable one; a
  caller reaching for the wrong one gets a `TypeError` at the first attempt.
  A case states that.
- **Still nothing in the product calls `resolve`,** by design: manager
  admission and the thin CLI are W361912's.
- **No provider, engine, Authority, instance or deployment was reached.** The
  compatibility generation is moved with `unittest.mock.patch` in the test
  process only, exactly as the reviewer's probe did; no installed default,
  configuration file or live instance is touched.
- The earlier round's limits still stand: the verification contract carried is
  the bounded test scope plus effective per-invocation ceilings and not a
  command, and whether a resolved Job SUCCEEDS is not proved.

### Cost

Read-only re-reading of the two reviews, the updated `FINDING.md`/`PLAN.md`,
`PLAN-HISTORY-362222.md` and all of `evidence/review-362222/`, then
`templates.py`, `submission.py`, `execution_limits.py`, `documents.py`,
`contracts/pod.py` and `contracts/canonical.py` again. Test runs this claim:
the focused suite five times (three failing — `copy.deepcopy` of a
`MappingProxyType` raising, which is what produced `template_document`; an
`origin` outside the vocabulary passing because `_without_origin` excluded it
before anything checked it, which is now its own refusal; and two cases of
mine asserting the re-derivation catches edits to purely preserved members,
which it cannot and which is now stated as the contract's boundary instead of
asserted as a property it does not have). The reviewer's focused set once; the
whole `tests/job_manager` suite twice; the three surface sweeps once on the
candidate against the base list retained from claim361943; whole
`tests/manager` once at ~242s against that same retained base list;
`probe-corrected.py` twice. No live provider, no engine, no total
manufactured.

### Boundaries

No Git operation of any kind, in the repository or in the scratch roots. The
canonical `v12/python` tree is byte-unchanged and the scoped status for it is
empty; `v12/DESIGN.md` is dirty from the reviewer's own SCH-1a transcription
and is untouched, as is every other pre-existing dirty record.
`candidate-361943/` and `evidence/claim-361943/` are preserved exactly. Per
the PLAN's split I wrote only `candidate-362249/`, `evidence/claim-362249/`
and this file; `FINDING.md`, `PLAN.md`, `PLAN-HISTORY-362222.md`, the reviews
and `evidence/review-362222/` are the reviewer's and are unmodified. No live
provider, engine, credential read, deployment, install, instance operation or
cutover. No store opened, copied or traversed outside the disposable ones
these cases create.

## claim362407 — R4: the new public input boundary owns its nested members

Answers `review-2026-10-26T18-08-59Z.md` under handoff362403, which resolves
R1, R2 and R3 and requests one bounded correction. Base commit
`182c8f943cdfc12134ae2d082d9afe98189efe90`, unchanged. At claim start
`candidate-362249/`'s three members and its manifest were re-hashed and all
four match what that manifest and the reviewer's
`evidence/review-362383/HASHES.json` record; the scoped status of `v12/python`
was empty. `candidate-361943/` and `candidate-362249/` are both preserved
untouched and the corrected candidate is `candidate-362407/`.

**R4 is real and it is my own defect in the verb I added last round.** I owned
the resolution's TOP LEVEL with `boundaries.document` and then read straight
through its members: `taken["template"].get("origin")`,
`resolution["task"]["job_id"]`, `resolution["scope"]["work"]`,
`stage["profile_name"]`, `list(resolution["acceptance"])` and
`dict(resolution["overrides"][name])`. Every one of the reviewer's seven inputs
is ordinary JSON-shaped data and every one escaped as `AttributeError`,
`KeyError` or `TypeError` instead of a `ContractRefusal` — at the one surface
whose whole purpose is to be the checked door a later manager and CLI reach.

### Read position

`detail work=W361910`, `work-events` through seq362407 (no pagination,
`next_after` null) and thread `T361910` complete — still one message at
seq361910, no newer discussion. Current `FINDING.md`, `PLAN.md`, all three
reviews and all of `evidence/review-362383/` read in full, including
`probe.py`, `PROBE.stdout`, `HASHES.json` and `RUNS.json`.

The reviewer's two rulings this round are taken as given: schema
`baton.v12.job-template-request/1` keeps its name through these corrections
and no version bump is required, and `submission_for_admission` alone is not
an atomic admission or replay proof — W361912 must use it and bind the full
resolution digest through actual admission. Neither is re-litigated here.

### What is delivered

The same three paths, corrected. Candidate `candidate-362407/`, manifest
`cdb05010acc18113d78f1197f3370d6b770bb7e3ee1beb016f6f3968ca7116e3`, which
records each member's base digest, its candidate digest and its digest in
`candidate-362249` — all three changed — and names both earlier candidates as
preserved.

| path | base | candidate-362407 |
| --- | --- | --- |
| `v12/python/src/baton_v12/job_manager/templates.py` | new | `64f9f3412c673d7bac7ace6190e3f8ddebba7056f90a279f07fc70efc0975e16` |
| `v12/python/tests/job_manager/test_templates.py` | new | `a45389dedc4008c937bca139effa6c08cba852c5c8d1ebc6e8cbfa97d6caab13` |
| `v12/python/src/baton_v12/job_manager/__init__.py` | `7fa34e59a272ebe17054fe48963ac5dfc6dd74ef81fe7aacb44a642ba8cff8bc` | `bfebb949e201c9de01075e98e3872fc2f761d460bd57308192c10a0795cf580c` |

`candidate-361943/` (manifest `834e88af…a7277`) and `candidate-362249/`
(manifest `fd92f115…f3b1`) are both preserved byte-untouched; all four of
their digests were re-derived this claim. The `__init__.py` change is still
the export block and its `__all__` entries; no existing test file is edited
and no existing assertion changed.

### R4 — one owner, stated at every depth that is later dereferenced

`owned_resolution(resolution)` is the correction: the counterpart to
`documents.owned_submission`, public for the same reason — a consumer holding
a retained resolution can prove it without spending it, which is also how a
holder tells a malformed resolution from a stale one.
`submission_for_admission` now calls it first and everything below reads only
the owned document, so `_request_of` and `_configuration_of` dereference
members whose shape is already proved. Both carry a docstring line saying that
is their precondition and naming the exact `KeyError` that happened without it.

**Why the top-level owner was not enough, said plainly, because it looked like
it was.** `boundaries.document` proves the thing is exact built-in JSON data
with exactly the member names this build knows, and that is load-bearing:
after it, every nested value is data rather than behaviour and `type(x) is
dict` means what it says. What it does not prove is anything about the SHAPE
of those values — and a resolution is a document of documents. So the closed
contract is now stated at `template`, `task`, `source`, `scope`, each resolved
stage and each of its dependencies, `rules`, `execution_limits` and each of
its boundaries, with `acceptance`, the two scope lists and the stage list held
to `_members`, which refuses a string rather than iterating it as its
characters. Five new closed member tuples are named for the shapes that were
previously implicit: `SELECTION_MEMBERS`, `RULE_MEMBERS`, `LIMITS_MEMBERS`,
`RESOLVED_STAGE_MEMBERS` and `RESOLVED_TASK_MEMBERS`.

**The template origin moved into the owner** rather than being checked
separately on the way past, which is where it belonged: it is the one member
the re-derivation cannot compare, so it has to be held by the owner or by
nothing.

**The submission member is owned there too**, by
`documents.owned_submission`, so a malformed document refuses as the
submission it claims to be instead of surviving until something read it.

**Nothing is caught.** The review asked for programmer faults to stay visible,
so there is no `try` or `except` anywhere on this path — and a case asserts
that mechanically from the module's own source across `owned_resolution`,
`submission_for_admission`, `_request_of`, `_configuration_of` and `resolve`,
rather than leaving it to be remembered.

### Evidence

`evidence/claim-362407/`, with `HOW-THESE-WERE-RUN.txt` giving the root, the
commands and a before/after table for all seven inputs.

- **The reviewer's own `evidence/review-362383/probe.py`, run UNCHANGED**
  against these bytes — not adapted, not re-aimed, not copied. All seven
  inputs answer `"typed_refusal": true` with a `ContractRefusal` naming the
  thing it is about. `stale_limit` is still `refused`, `lookup_mutation` still
  `refused` and the two scopes are still separate, so R1–R3 stay resolved in
  the same run that proves R4. Output in
  `REVIEWER-PROBE-UNMODIFIED.stdout`; stderr is empty.
- **`tests.job_manager.test_templates`**: **122 cases, OK** (108 before). One
  new class, `TheResolutionInputIsOwned`.
- **The reviewer's focused set**: **181 cases, OK**, where review-362383
  recorded 167.
- **Whole `tests/job_manager`**: **1299 OK**, against 1177 on the base root.
- **Not repeated, on the reviewer's instruction** ("do not repeat broad
  environment-dependent suites merely as insurance for this small
  correction"): the three package-surface sweeps and whole `tests/manager`.
  `evidence/claim-362249/` holds both against this same base commit with
  byte-identical base/candidate lists, and this round adds one validator and
  one export name rather than changing behaviour those suites reach.

### Limits, stated rather than left to be found

- **`owned_resolution` proves shape, not provenance.** It does not re-check
  the path rule on the two scopes — `check_relative_path` has one owner,
  `_scope`, and the re-derivation runs it — and it does not re-check the
  per-setting limit rules, which `_overrides` applies on the re-derivation.
  What it owns is exactly the shape the reconstruction dereferences.
- The earlier rounds' limits all still stand and are unchanged by this
  correction: nothing in the product calls `resolve` yet;
  `submission_for_admission` answers "would this build still produce this",
  not "has anybody edited this", and the purely preserved members are outside
  its reach by construction with `resolution_digest` binding exact bytes; the
  verification contract carried is the bounded test scope plus effective
  per-invocation ceilings and not a command; `template_of` is immutable and
  `template_document` is the serializable one; and whether a resolved Job
  SUCCEEDS is not proved.

### Cost

Read-only re-reading of the three reviews, the current `FINDING.md`/`PLAN.md`
and all of `evidence/review-362383/`, then `templates.py`,
`worker_manager/boundaries.py`, `contracts/pod.py` and `documents.py` again.
Test runs this claim: the focused suite four times (two failing, both my own
test assumptions rather than the product — one asserted every refusal would
name the top-level member a caller passed, where the refusals actually name
the nested thing they are about, which is better diagnostics and the
assertions now check the real text; one swept `overrides: {}` into a
blanket wrong-kind loop, and an empty overrides document is what every
ordinary resolution carries, so it is named as the legitimate case it is).
The reviewer's focused set once; the whole `tests/job_manager` suite twice;
the reviewer's probe unmodified twice. No live provider, no engine, no total
manufactured.

### Boundaries

No Git operation of any kind, in the repository or in the scratch root. The
canonical `v12/python` tree is byte-unchanged and the scoped status for it is
empty; `v12/DESIGN.md` stays dirty from the reviewer's own SCH-1a
transcription and is untouched, as is every other pre-existing dirty record.
`candidate-361943/`, `candidate-362249/`, `evidence/claim-361943/` and
`evidence/claim-362249/` are preserved exactly. Per the PLAN's split I wrote
only `candidate-362407/`, `evidence/claim-362407/` and this file;
`FINDING.md`, `PLAN.md`, `PLAN-HISTORY-362222.md`, all three reviews and both
reviewer evidence directories are the reviewer's and are unmodified — the
reviewer's `probe.py` was executed from where it sits and not copied or
edited. No live provider, engine, credential read, deployment, install,
instance operation or cutover. No store opened, copied or traversed outside
the disposable ones these cases create.
