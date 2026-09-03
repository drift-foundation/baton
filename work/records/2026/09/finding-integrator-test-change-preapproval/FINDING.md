# Pre-authorize reviewed test changes for managed integration

Ledger Work: W71459

Follow-up to W65212, `work/records/2026/09/finding-dedicated-proposal-integrator/`.

## Observed — 2026-09-02

The first two managed `baton.merge` attempts for W33937 each imported the
approved source path and then requested interactive file-change approval when
the next approved path was an existing test file. A dispatcher-owned turn is
non-interactive, so the bridge correctly refused the request, quarantined the
context, and left the exact claim for explicit recovery. Incidents I12/I13 and
I14/I15 retain the two occurrences.

The second attempt issued the test edit as one standalone, statically targeted
file-change call. That rules out batching as the underlying cause. The missing
input was the repository policy's case-specific confirmation for changing an
existing test's assertions or expected behaviour.

## Confirmed decision — 2026-09-02

`baton.merge` never prompts for permission. An integration handoff that imports
changes to existing test assertions or expected behaviour is admissible only
when the newest independent review or `baton.ops` handoff explicitly
pre-approves that exact reviewed change. The pre-approval names:

- the immutable proposal digest;
- every existing test path whose assertions or expected behaviour change; and
- that those reviewed test changes, rather than merely additive new tests, are
  approved for import.

The approval is bounded to the reviewed candidate bytes. It is not permission
to weaken other tests, redesign the proposal, edit another path, or invent a
correction during integration. If the explicit pre-approval is absent,
ambiguous, or does not cover the exact proposal and path set, the integrator
refuses before changing the working tree and returns the Work for clarification.
It never opens an interactive approval request from a managed turn.

For the current W33937 candidate, Slawomir explicitly approved the reviewed
changes to:

- `v12/python/tests/manager/test_boundary_inventory.py`;
- `v12/python/tests/manager/test_lifecycle_composition.py`;
- `v12/python/tests/manager/test_offers.py`; and
- `v12/python/tests/manager/test_secrets.py`.

The approval is tied to the independently signed run2c proposal digest
`sha256:6501754bd04c3fb846776919eb4e854d1ffd6b9bf71c4d1ba43dcab06c908c44`.

## Acceptance

- The durable integrator contract states the explicit pre-approval requirement
  and refusal boundary.
- The configured `baton.merge` role instructions carry the same rule.
- Tests or static guards prove that the role text cannot regress to prompting
  or treating generic review approval as authority to change existing tests.
- A fresh managed integrator proves, through separately accountable positive
  and negative Work or controlled immutable proposals, that a scheduled and
  reviewed test change imports without interactive approval while an
  out-of-scope test mutation refuses before changing the checkout.
- The positive gate imports only into owner-writable existing targets or creates
  explicitly planned non-executable regular files; the negative gate proves a
  read-only, symlink, non-regular, base-drifted, or otherwise unauthorized
  target refuses before content or mode mutation and returns to `baton.ops`.
- Frozen custody modes never reach checkout targets, and no privileged
  `install`/`chmod` execution capability is added.

## Reviewer revalidation and implementation boundary — 2026-09-02

### Observed

The accepted generation-5 configuration, its retained
`finding-dedicated-proposal-integrator/evidence/generation-5/baton.json`
candidate, and `docs/PROPOSAL-INTEGRATOR.md` all carry the same original role
contract. It authorizes import of independently approved immutable proposal
paths but does not distinguish ordinary path approval from the repository's
separate case-specific authority for changing an existing test's assertions or
expected behaviour. `AGENTS.md` owns that general test rule but has no
integrator-specific preflight or non-interactive refusal clause.

The focused W65212 guard in
`tests/work/test_w65212_proposal_integrator_deployment.py` checks provenance,
path, refusal, and Git boundaries. It does not check test-change authority,
preflight ordering, or the prohibition on asking for interactive approval.

W33937's newest independent review binds the run2c digest and six exact
candidate byte sets, including four existing test paths. Its verdict does not
expressly say that the reviewed assertion or expected-behaviour changes in
those four files are approved for import. The later recovery message calls the
failed attempt a batching problem and tells the integrator to issue static
single-file edits; the second static attempt disproved that diagnosis. A fresh
integrator reading only W33937's dossier, newest review, and current role text
therefore still lacks the explicit input required by `AGENTS.md`.

At this review instant W33937 remains claimed by `baton.merge`, whose runtime
is reported failed and quarantined after an unexpected approval request. Claim
recovery and a fresh managed context remain approver-owned operational gates;
this Work does not authorize the reviewer or tuner to perform them.

### Confirmed implementation rule

The integrator completes the authority check for the WHOLE proposed path set
before changing ANY working-tree path. If any accepted proposal path is an
existing test whose assertions or expected behaviour change, the newest
independent review or an explicit `baton.ops` handoff must:

1. name the immutable proposal digest;
2. enumerate every such existing test path; and
3. state that the reviewed assertion or expected-behaviour changes in those
   paths are approved for import.

Generic sign-off, exact path or candidate-byte enumeration, and approval of
the proposal as a whole do not imply this case-specific authority. Missing,
ambiguous, stale, digest-mismatched, or incomplete approval causes a refusal
before ANY import. The integrator returns the Work for clarification and never
opens an interactive approval request from its managed turn.

The authority is candidate-bound. It permits only those reviewed bytes at the
named paths and does not authorize another test change, weakening, redesign,
conflict correction, or opportunistic edit.

### Proposed patch boundary

- Extend `AGENTS.md`'s `baton.merge` policy and the quoted role contract in
  `docs/PROPOSAL-INTEGRATOR.md` with the exact preflight, evidence, refusal,
  and non-interactive boundaries above.
- Do not rewrite the reviewed generation-5 evidence. Prepare a new
  `evidence/generation-6/` candidate under this record from the accepted
  generation-5 configuration, incrementing only `generation` and replacing
  only `teams.baton.roles.integ.instructions`; retain a digest and rollout
  checklist for approver verification.
- Add a new focused test module rather than changing existing expectations.
  It should assert the durable contract, repository policy, and generation-6
  role all name the digest, exact existing test paths, explicit approval of
  their assertion/expected-behaviour changes, whole-path-set preflight before
  mutation, generic-approval insufficiency, refusal, and never-prompt rule.
  It should also prove the generation-6 candidate differs from accepted
  generation 5 only in the generation number and integrator role text.
- No protocol, application, dispatcher, execution-policy, or infrastructure
  code changes are required. The managed bridge already correctly quarantines
  an unexpected approval request.

### Focused verification

Run the new W71459 guard together with
`tests/work/test_w65212_proposal_integrator_deployment.py`, then the existing
role/configuration regression slice. `git diff --check` remains the final
repository formatting gate. The live acceptance proof is separate: after
independent review and approver acceptance of generation 6, a fresh
`baton.merge` context must preflight W33937's explicit digest/path approval,
import the exact six-path proposal without an approval request, run W33937's
bounded gate, and hand the result to `baton.ops`.

Before that retry, the W33937 handoff itself must carry the case-specific
approval recorded above; a cross-reference to this separate Work or the prior
generic sign-off is not a substitute for the evidence the integrator is
required to read.

## Live acceptance result — 2026-09-02

Generation 6 correctly enforced the semantic authority boundary. The first
fresh `baton.merge` turn refused before mutation because the case-specific
approval existed only as an ordinary `baton.slaw` message, not in the newest
independent review or an explicit `baton.ops` handoff. After `baton.ops`
claimed W33937 and passed it to `baton.merge` with the proposal digest, exact
four-test path set, and explicit approval of the reviewed assertion and
expected-behaviour changes, the next integrator accepted that authority and
completed the whole-path preflight.

The retry then imported only `offers.py` and the Codex tool host requested
interactive approval for the first existing-test file change. The dispatcher
correctly denied the request, quarantined the non-interactive context, and
left assignment episode 71677 orphaned. This proves that the generation-6
role contract fixes the integrator's semantic decision but does not configure
the lower Codex execution-policy layer to admit the already authorized test
edits. The earlier acceptance statement that no execution-policy change was
required is superseded by this live result.

Slawomir approved a bounded operator fallback for W33937: after recording this
defect, the interactive context may import only the independently reviewed
six candidate byte sets and verify their exact hashes. This is a stopgap, not
acceptance of W71459. W71459 remains open until a managed integrator can apply
an explicitly authorized existing-test change without requesting interactive
approval, while still refusing unapproved test changes.

### Refined mechanism observed during the operator fallback

The immediate trigger is narrower than a category-wide Codex prohibition on
existing-test edits. Before the fallback,
`v12/python/tests/manager/test_boundary_inventory.py` and
`v12/python/tests/manager/test_secrets.py` were mode `0444`; the first managed
approval request occurred at `test_boundary_inventory.py`. The other reviewed
targets were owner-writable and `offers.py` imported without a request. Every
file in the retained custody candidate is mode `0444`, because custody freezes
the proposal, but that custody mode is not an instruction to make the live
checkout read-only.

The bounded fallback added only the owner write bit to the two read-only live
targets, imported the reviewed bytes, and then passed the 154-test contract
slice, both immutable review probes, and the 32-test real-Docker lifecycle
slice (Podman unavailable and skipped). The evidence therefore proves a live
mode-propagation/tool-policy mismatch at a read-only target. Follow-up must
identify how those live paths became `0444`, prevent frozen proposal modes from
leaking into the checkout, and prove the managed integrator can update an
explicitly authorized read-only-at-entry target without prompting or partial
mutation. It must not weaken the semantic test-change approval rule.

## Root cause confirmed from retained managed sessions — 2026-09-02

### Observed

The retained `baton.merge` session for W61984 imported its eleven approved
paths at `2026-09-02T04:09:28Z` with this exact operation from the sealed
candidate root:

```text
cp --preserve=mode --parents <eleven approved paths> /home/sl/src/baton
```

That path set included `test_boundary_inventory.py`, `test_secrets.py`, and
`test_text_sweep.py`. The same session imported W64268's three approved paths
at `2026-09-02T04:34:47Z` with the same operation; that set included
`test_claude_agent.py`. The surviving `test_text_sweep.py` and
`test_claude_agent.py` checkout metadata is mode `0444` with change times that
match those two imports. The later W33937 fallback necessarily changed the
mode and change time of the other two affected targets, so their pre-fallback
`0444` observations remain the retained evidence for those paths.

`worker_manager.sealing._frozen` deliberately rewrites every custody file to
`0444`. It does not preserve an authored executable or writable mode in that
tree. Therefore `cp --preserve=mode` imported custody protection metadata,
not proposal-authored repository metadata, into the live checkout. The W33937
managed retry then used a Codex FileChange for the first already-read-only
target, causing the interactive approval request. The execution host did not
reject the preceding owner-writable `offers.py` edit.

This confirms a concrete import-procedure defect rather than a generic host
prohibition on approved existing-test changes. It also explains why changing
only the semantic pre-approval policy could not make the live gate pass.

### Proposed bounded correction for decision

Custody modes should be treated only as custody metadata. Proposal integration
should import approved bytes without propagating those modes. After the whole
path-set provenance, digest, authority, overlap, and target preflight succeeds,
an existing regular-file target should be replaced with the reviewed candidate
bytes at its preflight mode plus the owner-write bit. This retains all existing
execute and group/other bits, repairs an earlier leaked `0444` as `0644`, and
does not guess mode from a custody tree that has erased that information. A new
regular-file target needs a separately explicit default or reviewed mode rule;
W33937's live acceptance set contains only existing targets and need not decide
that broader case.

A local non-repository probe confirms that `install -m 0644 candidate target`
replaces an owner-owned `0444` regular target with byte-identical content and
leaves it `0644` without a FileChange approval request. A production rule may
use that primitive or an equivalently bounded content-only replacement, but it
must prohibit `cp --preserve=mode` from frozen custody, verify every final byte
against the reviewed candidate, verify every final target mode against the
preflight-derived mode, and leave the semantic refusal before all mutation.

The exact replacement/default-mode rule is an operational security decision,
not implicit authority to add a broad execution-policy exception. It requires
independent review and approver confirmation before the integrator role or
deployment candidate is revised. No Baton protocol or application change is
proposed by this finding.

## Confirmed bounded correction — 2026-09-02

Slawomir selected the review's recommended fail-closed contract. This ruling
supersedes the proposed `install -m` or equivalent replacement for a read-only
target. `baton.merge` receives no privileged `install`, `chmod`, or other
execution capability for bypassing a FileChange refusal.

Custody `0444` is protection metadata and is never propagated into the working
tree. Before any mutation, the integrator preflights the complete accepted path
set. Every existing target must be a non-symlink regular file, must match the
reviewed base bytes, and must already have its owner-write bit. A target that
fails any of those checks causes the entire import to refuse before content or
mode mutation and returns to `baton.ops` for exact operator repair. Once every
target passes, the integrator imports the reviewed content without preserving
custody modes and verifies the final bytes and checkout modes.

An explicitly planned new regular file, including a test, uses the ordinary
non-executable repository mode. Executable mode requires explicit accepted
scope. A new target whose creation or executable mode is not covered refuses;
the integrator does not infer mode from frozen custody.

### Clarified test-change authority

The earlier requirement in this finding that ONLY the newest independent
review or an explicit `baton.ops` handoff may supply existing-test authority is
superseded. Tests are ordinary scheduled project files. An accepted Work
description or plan that explicitly authorizes adding, editing, or removing
tests within a bounded scope is the case-specific authority, and a managed
turn must not request redundant interactive approval merely because the
reviewed proposal exercises it.

Independent review remains mandatory: it enumerates and evaluates the actual
changed paths and binds its verdict to the immutable candidate. Generic
sign-off without scheduled test scope, or a mutation absent from or outside
that scope, grants nothing and refuses before import. Deletion, weakened
expectations, or changed behaviour must be visible in both the accepted scope
and review.

W33937 is closed satisfying after the operator fallback and its candidate bytes
are already present, so it cannot be reopened or reused as the live gate. Final
acceptance instead uses separately accountable positive and negative Work or
controlled immutable proposals. This correction is limited to policy,
documentation, deployment-role evidence, and additive regression guards; no
Baton protocol, application, execution-policy generator, or infrastructure
change is authorized.

## Live-gate decomposition — 2026-09-02

The post-review handoff contained no rollout or managed-gate evidence. The live
accepted configuration remained byte-identical to generation 6. The remaining
criterion is therefore decomposed into three separately bound child Work:

- W72003 deploys only reviewed generation 7 and proves a fresh healthy
  `baton.merge` context;
- W72011 is the positive scheduled-test gate and is blocked on W72003; and
- W72013 owns two separate negative candidates, one for an otherwise
  authorized read-only target and one for an owner-writable out-of-scope test,
  and is blocked on W72003.

The positive fixture explicitly authorizes one additive function in the clean,
owner-writable existing path
`tests/work/test_w65212_proposal_integrator_deployment.py`. The two negative
fixtures use the clean read-only
`v12/python/tests/manager/test_text_sweep.py` and the clean owner-writable but
explicitly unauthorized `tests/work/test_w101_role_instructions.py`. Their
dossiers record planning-time bytes, modes, owner and base commit. Every fact
must be revalidated before candidate creation; drift requires a new reviewed
fixture rather than silent substitution.

The negative cases remain separate so a scope refusal cannot masquerade as a
mode refusal or vice versa. No negative candidate is eligible for successful
import. W71459 cannot close while any child is open, and generation acceptance
alone is not final live proof.

## Final independent live acceptance — 2026-09-03

All three child gates are closed satisfying and the combined evidence now
demonstrates the whole acceptance boundary.

The installed configuration is generation 7 and is byte-identical to the
reviewed candidate at SHA-256
`e7fac15abbcb33a09df3a5c650b2e7a9127515ecbba5ce9ff222953b1b4b6b55`.
Canonical W72003 event 72426 records approver closure under generation-7
authorization after successful deployment and a fresh healthy, non-quarantined
`baton.merge` runtime. Its plan and progress were not updated by the approver
before closure; the append-only terminal review in that child reconstructs the
canonical evidence and explicitly supersedes only the stale plan status.

W72011's independently reviewed one-file candidate added one expressly
scheduled test function and changed no existing expectation. Generation-7
`baton.merge` assignment episode 73134 completed the whole-set preflight,
imported only the reviewed bytes without a prompt or privileged replacement,
and preserved checkout mode `0600` rather than propagating candidate custody
mode `0444`. The final checkout hash remains the candidate digest
`0cd0aa957ecd7c454edb9dea0218ebb364fee70bb8bc02801900f7b4adca3afe`.

W72013 used two separately reviewed one-path candidates and two distinct
managed assignments. Episode 72941 returned
`REFUSAL[owner-write-preflight]` for the scheduled but read-only `0444` target;
episode 72970 returned `REFUSAL[missing-scheduled-test-scope]` for the otherwise
admissible owner-writable `0664` target. Current hashes and modes still match
the recorded before/after states, and neither candidate entered the checkout.
No negative attempt prompted, repaired, broadened scope, or mutated content or
mode.

The focused W71459/W65212 policy and configuration slice independently passes
11 tests, the role/configuration/deployment slice passes 82 tests, and
`git diff --check` passes. No protocol, application, dispatcher,
execution-policy generator, or infrastructure change was needed. W71459 is
satisfying and may close.
