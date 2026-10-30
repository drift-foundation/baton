# Implementer progress — W376723

## claim376786 — the closed capability document and the pure predicate

Authorization: owner E371253 and continuation M376590; first bounded slice
from W371295. Base `f36bcd75ed22430355efe1b274b8f236cb591f6b`. Candidate:
`v12/python/src/baton_v12/job_manager/role_capability.py` (new)
`af370172d58a763b5b766930317acdbdeabba301293c31c56e2fe1807da59990` and
`v12/python/tests/job_manager/test_role_capability.py` (new)
`45e6321a0e63576d375513bcaeba9820d2845c709c4e45d7abaa616e0d4da5a3`.
Nothing else is edited: the accepted W371294 `role_contract.py` and
`templates.py` candidates are untouched byte-for-byte.

### The approved digest reproduces, which is the whole identity

`CAPABILITY.synthetic.json` read from the record canonicalizes under this
tree's own `contracts.digest` to
`sha256:4d6a3391facb990ac61090ab5e6b114203b27a27faeca1083458c7bd8f649601` —
exactly the proposal's value — and the module asserts the same at import. Its
`role_contract_digest` IS `role_contract.BASELINE_DIGEST`, so the approved
pair really does point at the contract W371294 delivered.

### What the validator closes

`capability/1` is exactly seven members. Each of the five identities must be
one lower-case `sha256:` + 64 hex: **a wildcard is not an identity**, and what
makes that enforceable is that no other spelling is admitted at all. `roles`
is exactly one of the three approved sets, so an empty list, a duplicate, a
reordering and an unknown role all refuse. 2048 canonical bytes, duplicate
keys refused before canonicalization — the same two-readings fault the
contract reader closes — and no embedded digest member for a claim to
disagree with.

### What the predicate answers, and what it refuses to mean

`compatible_capability` validates BOTH documents through their own owners —
neither is trusted as already-checked data — then requires the capability's
`role_contract_digest` to equal the contract's **computed** digest, and every
declared role to be a role the contract declares. It answers the agreed roles
as a fresh list.

It grants NO qualification: `qualification_digest` is required, bounded text
and nothing here verifies what it refers to. A case drives that explicitly by
changing it and still getting agreement — a self-authored advertisement grants
nothing, which is W371296's work. And no carrier is composed or read: a case
asserts the module's own source mentions no deployment, derivation or
resolution schema, no `ControlStore` and no `subprocess`.

### One honest adjustment to a case I first wrote wrong

My unknown-role case narrowed the contract's roles — but `check_role_contract`
refuses that FIRST, because that document is closed at exactly two roles. So
with any VALID contract every capability role is necessarily declared, and
that branch is **defence in depth**. The case now asserts the refusal that
actually happens and says why the branch stays: the two closed sets are owned
by different modules and a later revision could widen one without the other.
I also corrected a digest assertion — `name_value` truncates, so the message
carries prefixes rather than whole digests.

### Verification

    tests.job_manager.test_role_capability   26 OK  (new)
    tests.job_manager.test_role_contract
      + test_templates + test_creation      272 OK  (no regression)

### Remaining in W371295

The deployment `/3`, derivation `/1` and resolution `/2` carriers, the
pre-effect wiring of this predicate before reservation, the replay and
dispatch fences and the common Job projection. None is started and no carrier
word appears in this slice. No build, engine, provider, deployment or Git
mutation; no synthetic qualification grant.

## claim376995 — the pure boundary completed

Review 2026-10-28T20-04-40Z was right: `compatible_capability` took only a
capability and a contract, so the tuple binding, the final per-role
declarations, task/source agreement, role eligibility and principal separation
— all assigned here by the FINDING — did not exist. The validator progress is
retained unchanged and `admissible_roles` is added beside it.

    role_capability.py       7d6aec765c1bea3b14b94c1193d8fbca81b4dded2d5468fcac97e54be71a5eaf
    test_role_capability.py  eab9e26eee1068ca27aefac6597a5cdd4aedd8608d3df444a0757f45c656104c

**ONE function, because those facts are only meaningful together.** A
capability matching the contract but qualified for another image, or two
eligible lanes answering to one principal, are both admissions nobody
selected — checking them separately would let either pass alone.

* **The actual tuple.** `installed` is the adapter, image and runtime-profile
  digests this deployment resolved, and the capability must have been
  qualified against exactly it: *a capability is evidence about one tuple and
  proves nothing about another*.
* **The final per-role declarations**, member for member against the
  descriptor — name order included, so a reordered, short or extended set
  refuses. This is where an incompatibility used to reach a running adapter.
* **Task and source agreement** per lane against the contract.
* **Eligibility** — a qualified role with no composed candidate refuses, and a
  candidate the capability does not cover refuses too.
* **Principal separation** — two roles may not answer to one principal, and
  *two worker ids do not create independence*; the refusal names both ids.
* **One common Job projection**, with per-lane runtime identity left alone,
  which is the `ID-4` distinction rather than whole-manifest equality.

PURE throughout: every operand is owned built-in data, `own` snapshots each,
and a case asserts the module's own source contains no `open(`, `subprocess`,
`ControlStore`, `socket`, `requests` or `os.path`. No carrier, no effectful
wiring, no synthetic qualification grant.

    tests.job_manager.test_role_capability   40 OK  (was 26)
    with test_role_contract + test_templates
      + test_creation                       312 OK  (no regression)

### Remaining in W371295

The deployment `/3`, derivation `/1` and resolution `/2` carriers, the
pre-effect wiring of this boundary before reservation, the replay and dispatch
fences. W376731 stays blocked; the parent retains integrated acceptance.

Verification spending: two focused suite runs. No build, engine, provider,
deployment or version-control action.

## claim377550 — the four faults review 20-08-41Z found, closed

Base `8876bf950ff1f8ab8767ce9786df268cc9d767c6`. PROPOSAL re-hashed at claim to
`ad0f2171f06f8da9e6e3c2784e50cab91d27f94c4d0727014e4520b00aa0b339`; the
accepted W371294 `role_contract.py` is UNTOUCHED at
`691ed3a0e653a9705f181790c9565706902bd3958f2973e49e85cff586ca6967`.

    v12/python/src/baton_v12/job_manager/role_capability.py
      09fdc0e278d16a72d79ff26f9e1523b93aae6b423ebb11fc73ff6741472a90a0
    v12/python/tests/job_manager/test_role_capability.py
      0d296dcf23f013a6f9aceb459db6078b928fdf9d37daf2311433bfc47c4ab1b8

**Every counterexample was real and each one is closed at its root rather than
patched.** `evidence/claim-377550/COUNTEREXAMPLES-REPLAYED.json` re-runs the
reviewer's own three probes against this candidate: all three now REFUSE, and
the heterogeneous positive the fourth observation asked for is ADMITTED.

### 1. Declarations are compared type-sensitively (counterexample 1)

`required: 0` was accepted against a descriptor fixing `false` because Python
holds `0 == False`. The review's diagnosis is exact — "`own` preserves built-in
types but does not make ordinary equality type-sensitive" — so the comparison
was using the WRONG RELATION, not a missing check. `_identical` compares
`type(...) is type(...)` first and recurses; `_disagreement` names the first
differing path and both types.

**And the refusal I assert is the one that actually happens.** The frozen
`outputDescriptor` types `required`, so the integer reaches the SCHEMA before
it reaches my comparison, and the case says so. The type-sensitive check is
therefore a SECOND LINE, and seven drifts that the frozen descriptor ADMITS --
`required: true`, a path, a lower `max_bytes`, an extra media type, a reordered
set, a short set and a longer set with a fresh name -- are what prove it
carries weight. An extended set reusing a name refuses at §12 rule 3, and that
case names that refusal instead of claiming this boundary caught it.

### 2. The answer is the CONTRACT's roles (counterexample 2)

A capability declaring `["implementation"]` with one matching candidate
answered `["implementation"]` for a contract requiring both roles — a full
admission for half a workflow, because the missing set was computed from the
capability. `admissible_roles` now derives the required roles from the owned
contract and refuses unless EVERY one has an independently eligible lane. A
role-specific capability stays a valid LANE input, which a positive case
proves: both lanes covered only for their own role are admitted.

### 3. The Job projection is DERIVED, never a label (counterexample 3)

Two lanes passing `job_projection=None` agreed. The operand is gone. Each lane
now carries its **actual input manifest**, and the projection is
`contracts.job_input_identity` — the rule that already owns this question: it
validates against the frozen `inputManifest`, verifies the self-digest, refuses
a durable secret, and projects out exactly the per-execution members. So
`None`, `{}`, an invented `{job_id, input_digest}` label and a manifest with a
stale self-digest all refuse, and `JOB_INPUT_EXCLUDED` members are PROVED free
to differ between lanes by a positive case.

### 4. Per-lane capability and per-lane tuple (the structural fault)

One shared capability and one shared `installed` tuple could not establish
heterogeneous binding, and the case claiming to prove heterogeneity varied only
`worker_id` — the review was right to call that out. Every candidate now
carries its own trusted capability and its own resolved tuple, and the new
positive runs the two lanes on DIFFERENT images, DIFFERENT runtime profiles and
DIFFERENT adapters, asserting member for member that the evidence really
differs while the Job input identity is one.

**And the tuple is bound to the lane's own composed input**, not only to its
capability: `worker_image_digest` and `runtime_profile_digest` must agree with
the manifest. A resolved identity no composed input mentions is a claim about a
runtime nobody is going to start. The adapter digest has no manifest member,
which is exactly why `qualification_digest` and W371296 exist.

### 5. One owned contract, and behavioural purity

The ownership observation is closed at both ends: the decision reads only the
owned snapshot, and `own` refuses any mapping that could answer a second read
differently — a `dict` subclass contract and a `dict` subclass candidate both
refuse, which a case asserts. The purity proof is now BEHAVIOURAL, as the
review asked: the caller's documents are deep-compared before and after, then
mutated, and the answer does not move. The source-text scan remains as a
secondary signal and says so in its own docstring.

`_admissible_lane` is deliberately not named `_lane`: `job_manager/scheduler.py`
already has one, and `test_boundary_inventory` resolves private helpers by bare
name across the package.

### Verification

    tests.job_manager.test_role_capability    56 OK  (was 40)
    with test_role_contract + test_templates
      + test_creation                        328 OK, 0.672s  (no regression)
    unittest discover tests/job_manager     1505 run, 3 errors

The three `job_manager` discovery errors are **not this candidate's** and I did
not assert that from reading: `test_native_permission`, `test_native_stop_
restart` and `test_serving_renewal` were all already failing in this shared
checkout under this Work's PRE-CLAIM bytes (`role_capability.py` `7d6aec76`),
measured an hour earlier during W376586 claim 377048, and two of the three also
fail in an isolated snapshot outside the checkout. None imports
`role_capability`; the third is the store-path-inside-the-checkout case recorded
in that Work's PROGRESS. Named rather than waved away.

Evidence: `evidence/claim-377550/{CHECK.json, focused.log,
COUNTEREXAMPLES-REPLAYED.json}`.

### Remaining in W371295

The deployment `/3`, derivation `/1` and resolution `/2` carriers, the
pre-effect wiring of this boundary before reservation, and the replay and
dispatch fences. W376731 stays blocked; the parent retains integrated
acceptance. No build, engine, provider, deployment or version-control action,
and no qualification minted — `qualification_digest` is still only required
text that nothing in this module verifies.

## claim378068 — the actual task, bound to each lane's own manifest

Review 2026-10-28T21-35-39Z accepted the previous corrections and named one
remaining gap. It was right, and it is the same fault in a new place:
`task_schema` and `source_profile` were **labels**, and a matching label is not
validation of the underlying composed input — exactly the distinction this
boundary already learned about the invented `job_projection`. Base
`8876bf950ff1f8ab8767ce9786df268cc9d767c6`.

    role_capability.py       9861727b1871b15be7200b427a8a80641e74922afe8a117341b4ba43283986f5
    test_role_capability.py  38684c0df66fcad9c91388f0ea52c8e57c8874d033f847545e61f367bd671255

Reused and **untouched**, re-hashed rather than assumed: `role_contract.py`
`691ed3a0…`, `tools/job_task.py` `a9ce7948…`, `verification_context.py`
`f599072a…`.

### The counterexample, replayed

`evidence/claim-378068/TASK-BOUNDARY-REPLAYED.json` runs the reviewer's probe
against this candidate. The `text/markdown` task delivery that was **admitted**
now refuses; a real pair composed through `tools/job_task.py` is admitted,
including for heterogeneous lanes; an unsupported task generation refuses
through the task owner; and a candidate without a task operand refuses as a
missing member — because the task is a required member now rather than an
absent one.

### What replaced the labels

`CANDIDATE_MEMBERS` carries `task_document` — the lane's ACTUAL composed task,
as `job_task.compose_task` answers it — and the two labels are gone. Three
facts are then established per lane, none of them asserted:

* **The supported generation, through its own owner.**
  `verification_context.generation` is the existing data-only owner of that
  question: it refuses anything outside its two generations, a `/2` carrying a
  `/3` member and a `/3` without one. The contract then fixes WHICH generation
  this template supports, so a valid `/3` task under a `/2` contract refuses
  here rather than at a worker — a case drives all three.
* **The source profile, read out of the task** and held to the contract's,
  type-sensitively through `_identical`.
* **The exact artifact binding.** The manifest's human contract IS this
  profile's task delivery, so its media type, byte count and content digest
  must describe THESE bytes. That is what makes the manifest's Job input
  identity a statement about this task rather than about a document nobody
  has.

One encoding, which is `job_task.delivered_bytes`'s own rule restated for its
own reason: the bytes the artifact names and the bytes the worker reads must
not be two renderings of one string.

### The media type is one contract in two places, and a case says so

`src/` may not import `tools/`, so `TASK_MEDIA_TYPE` is spelled here and
`job_task.CONTRACT_MEDIA_TYPE` there. A case holds the two against each other
and a second asserts this module's IMPORT STATEMENTS name no tool — the same
guard `test_exchange` keeps over the worker's and manager's copies of the
exchange vocabulary, for the same reason.

### What I got wrong in my own cases, and what the honest answer was

* **Five spoiled artifact values refuse at the frozen schema**, not at my
  binding check: a media type with a parameter breaks its pattern, and a null
  or boolean breaks its type. The case is split by LINE and each half asserts
  the refusal that actually happens, with four schema-valid spoils reaching
  this boundary.
* **The manifest must be spoiled AFTER composition.** `job_task.manifest_for`
  proves the manifest through its own owner, so my first declaration-drift
  fixtures could not even be built — the refusal came from the fixture. They
  now compose a valid pair and then re-seal a spoiled member.
* **`compose_task` SUBSTITUTES `task_id` and `instructions`.** My first
  differing-task case changed the installed task's instructions and then
  asserted two byte-identical documents were different. It drifts
  `verification` now — a member that travels as the deployment wrote it.
* **The common-task check is a second line nothing valid can reach**, and I say
  so rather than writing a case that pretends otherwise. The task artifact's
  digest lives inside the manifest the Job input identity is taken over, so a
  lane whose task differs has either an artifact that does not describe it (the
  binding refuses) or one that does (the identity refuses). There is no third
  input. The check stays because the FINDING requires the fact and because the
  two documents that imply it are owned by different parties; the case asserts
  the positive, drives both negative routes, and names the refusal each one
  actually produces.

### Verification

    tests.job_manager.test_role_capability    66 OK  (was 56)
    with test_role_contract + test_templates
      + test_creation                        338 OK, 1.330s
    unittest discover tests/job_manager     1515 run, 3 errors

The three discovery errors are the same three recorded under claim 377550 —
already failing in this shared checkout under this Work's pre-claim bytes, and
none imports `role_capability`. Evidence:
`evidence/claim-378068/{CHECK.json, focused.log,
TASK-BOUNDARY-REPLAYED.json}`.

Still pure: no filesystem, store, engine, provider or callback inside the
predicate, and no qualification minted — `qualification_digest` remains
required text that nothing here verifies.

### Remaining in W371295

The deployment `/3`, derivation `/1` and resolution `/2` carriers, the
pre-effect wiring of this boundary before reservation, and the replay and
dispatch fences. W376731 stays blocked; the parent retains integrated
acceptance.

## claim378340 — the supported `/2` task contract, proved against its consumer

Review 2026-10-28T22-37-51Z accepted the task/artifact binding and named one
blocker: `verification_context.generation` answers WHICH generation a task
declares and whether it carries the `/3` context member, and nothing about its
supported shape. The probe is the proof — **four fully digest-bound pairs were
admitted here and refused by the consuming reader**. A generation label plus a
correct artifact digest is not a task contract, and the review is right.

    role_capability.py       07f9f827d197900825d2abf234f116821675edf43dffa5ff183bcd022e339959
    test_role_capability.py  de1d0d9370da8b02604369f1c5b1e0e3319f213df0f77b56bcaa986552cd40f1

Reused and **untouched**, re-hashed: `role_contract.py` `691ed3a0…`,
`tools/job_task.py` `a9ce7948…`, `verification_context.py` `f599072a…`, and
`claude_agent.py` `017257c0…`.

### `check_dogfood_task` — the closed `/2` shape, in the consumer's own order

A dict; exactly the seven members; `schema` by equality; `task_id` held to
`type is str` BEFORE the identity pattern (W44424's correction at the consumer:
a JSON number reached the regex as its decimal spelling and passed);
`instructions` and `source_root` bounded non-empty text; `source_root` by
EQUALITY, because the workload stages exactly one path; `verification` a
non-empty list of non-empty words, since a command assembled from a string is
a shell and there is no shell. Pure owned data throughout — no filesystem, no
callback, no provider import.

**And the profile rules are not respelled.** `baton_v12.source_profiles` owns
the profile vocabulary and the declared-base rule, it lives in this package,
and the consumer's own reader defers to it for exactly these two members —
"the pairing is the profile package's rule, not a second copy of it". This
defers to the same owner.

### The agreement is MEASURED, not asserted

`TheTwoTaskReadersAgree` runs **both** readers — this pure boundary and the
actual `claude_agent._read_task` — over one set of sixteen vectors and requires
the same verdict from each. The set is not vacuously agreed: exactly one vector
is accepted, so a validator that accepted everything would fail there. The
review's four retained counterexamples are also named one by one, and
`evidence/claim-378340/TASK-VALIDATION-REPLAYED.json` replays its five-vector
probe: `agreed: true`, with the four now refused by both readers.

### The coordination, stated rather than assumed

The vocabulary is spelled in the generic host rather than imported, for two
reasons that are both constraints you set: the consumer is a **provider
adapter inside the worker image** and must not be imported into the generic
host, and `claude_agent.py` is **W376586's current candidate, under review** —
so extracting a shared module in this claim would be an uncoordinated edit to
another open slice. Its bytes are unchanged at `017257c0`. A case asserts this
module's import statements name no provider adapter and no tool.

**The coordinated follow-up, named:** once W376586's `claude_agent` slice is
accepted, the `/2` vocabulary should have one owning home that both parties
import. What is NOT deferred is the agreement, which is proved now by
measurement rather than promised.

### One of my own cases moved, at the line that actually refuses

`test_a_drifted_task_source_profile_refuses` asserted the agreement message
for every spoiled profile. Four of those now refuse EARLIER, at the task
contract, through the profile package that owns that vocabulary — which is the
right order (shape before agreement). The case is split: values outside the
vocabulary assert the task-contract refusal, and `generic` and `git` — real
profiles this workload consumes and this contract does not select — reach the
agreement check. Both halves assert the refusal that actually happens.

### Verification

    tests.job_manager.test_role_capability    70 OK  (was 66)
    with test_role_contract + test_templates
      + test_creation                        342 OK, 1.322s
    unittest discover tests/job_manager     1519 cases run, 3 failing cases

**The three are attributed by cause this time, not by name**, since the review
declined the earlier waiver:

* `test_native_permission` — `stage_execution.held_configuration` refuses a
  configured `integration_store` path the fixture composes under `v12/python`
  itself, inside the checkout.
* `test_native_stop_restart` and `test_serving_renewal` — `resource-token.
  launch` refused for a REVOKED generation of `workspace:43:<n>`, inside each
  suite's own fixture.

And their independence of this candidate is **structural**: each fails IN
ISOLATION, so none is cross-test interference, and **nothing in `src/` or
`tools/` imports `role_capability` at all** — the importer set is empty, so
this candidate is not in their execution path.

Still pure, still no carrier, and no qualification minted.

### Remaining in W371295

The deployment `/3`, derivation `/1` and resolution `/2` carriers, the
pre-effect wiring of this boundary before reservation, and the replay and
dispatch fences. W376731 stays blocked; the parent retains integrated
acceptance.

## claim378520 — the source/base pairing, asked through its own owner

Review 2026-10-28T23-13-01Z accepted the task shape and artifact binding and
named one more: `check_dogfood_task` permitted **`git-line` with a null
`declared_base`**, admitted for both roles, while `source_profiles.
checkout_plan` refuses it. A lane nobody could check out was passing the
boundary whose whole job is to refuse before effects.

    role_capability.py       7b3db27c0f400d66f678ad714fe12aba5db80b47c94a38e22833d4d4c2b5456c
    test_role_capability.py  128cf227ffbf82d1406992580e40147ce0a25ad505d46bedf56b134fdf0eb7ca

Reused and **untouched**, re-hashed: `source_profiles/checkout.py`
`037f197a…`, `role_contract.py` `691ed3a0…`, `tools/job_task.py`
`a9ce7948…`, `verification_context.py` `f599072a…`, `claude_agent.py`
`017257c0…`.

### Why I had it wrong, and it is worth saying precisely

I mirrored the consuming reader: hold the profile to the vocabulary, hold the
base to its shape. That reader can afford to, because it **defers the pairing
to `checkout_plan` later in the same turn** — its own comment says so. A
pre-effect admission predicate has no later turn, so mirroring the consumer
reproduced its deferral without its follow-through.

### The rule is ASKED, not restated

`_paired` calls `source_profiles.checkout_plan` and keeps only the refusal.
`checkout_plan` refuses **both** directions — a version-control profile with no
base AND a generic profile with one — and asking it means this boundary cannot
drift from it when a third profile arrives. A second copy of the pairing is a
second rule.

The two path operands are the consuming contract's own fixed `/input/source`
and `/output`; the plan is discarded, and nothing here decides a workspace.
`test_verification_context` asks the same rule the same way with the same two
paths, which is the established idiom in this package for asking a rule you do
not own.

### The relation this boundary holds, stated exactly

`evidence/claim-378520/PAIRING-REPLAYED.json` measures all three parties over
five vectors:

* **EQUAL to the profile package on every vector** — the rule is the package's.
* **AT LEAST AS STRICT as the worker reader, never laxer.** Three pairing
  vectors refuse here and are accepted there, for the deferral above.
* **No false admission**: nothing admitted here is refused by either the
  consumer or the package.

So `TheTwoTaskReadersAgree`'s core case changed from equality to the relation
that is actually true and actually load-bearing: *this boundary never admits
what the consumer refuses*, plus every strictness accounted for by name in
`test_the_deferred_pairing_is_stricter_here_and_accounted_for`, which asserts
for each deferred vector that the rule THIS boundary asked is the one that
refuses. Insisting on equality would have forced one of two wrong moves —
weakening this boundary, or editing an adapter that is another open slice's
candidate.

### One of my own cases moved again, at the line that actually refuses

`generic` carries a base in my fixture, so it now refuses as a **pairing**
rather than as an unsupported source. The case names that explicitly, and the
vector that reaches the agreement check is `git` — a profile the workload
consumes, correctly paired, and not the one this contract selects.

### Verification

    tests.job_manager.test_role_capability    72 OK  (was 70)
    with test_role_contract + test_templates
      + test_creation                        344 OK, 1.350s
    unittest discover tests/job_manager     1521 cases run, 3 failing cases

The three are the same three, attributed by cause and not by name: one is a
configured store path the fixture composes inside the checkout, two are
`resource-token.launch` refused for a revoked generation inside their own
fixtures. Each fails IN ISOLATION, and nothing in `src/` or `tools/` imports
`role_capability` at all — the importer set is empty, so this candidate is not
in their execution path.

No checkout is performed, no filesystem or callback work happens inside the
predicate, no provider adapter is imported into the host, and no qualification
is minted.

### Remaining in W371295

The deployment `/3`, derivation `/1` and resolution `/2` carriers, the
pre-effect wiring of this boundary before reservation, and the replay and
dispatch fences. W376731 stays blocked; the parent retains integrated
acceptance.
