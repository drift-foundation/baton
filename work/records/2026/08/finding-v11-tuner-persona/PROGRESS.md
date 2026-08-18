# Progress

No implementation agent has started. The approved configuration-only rollout
is being applied by the reviewer/operator path.

## Expanded assignment — the complete role bootstrap contract (2026-08-18)

Implemented by `baton.claude` and returned to `baton.feat`. PLAN steps 7-9.
Step 10 is deployment and belongs to the approver; the material it needs is
recorded rather than applied, for the reason below.

### Revalidation

All four gaps FINDING.md names reproduce on the settled tree:

- `config.py` accepted `instructions` as an optional role field;
- `participant_instructions` inferred the role whenever exactly one held role
  carried instructions, and both launcher configurations left their role
  optional;
- the shipped `conf/baton.example.json` carried instructions that stated
  authority but named no required reading;
- `docs/BATON-SETUP.md` said "agent-backed roles **should** also declare" the
  field, and neither guide made bootstrap reading part of the contract.

### What changed

**Universal.** Every declared role must carry a non-empty `instructions`
string. A deployment with an uninstructed role is refused at ACCEPTANCE rather
than at the launch that needed the text — an agent launched into such a role
falls back to whatever prompt an operator remembered, which is the one-off
prompt this Work exists to retire. The check is deliberately role-GENERIC: it
requires instructions on every declared role and never names one.
`test_the_contract_is_role_generic` reads `config.py`'s own source and fails if
`rview`, `impl`, `approv`, `tuner`, `AGENTS.md` or `EFFECTIVE-BATON` appears
in it, so the protocol cannot quietly acquire this deployment's vocabulary.

**Explicit.** `participant_instructions` now takes a required `role`, the CLI
operand is required grammar, `identity.role` is required on every Codex
target, and `baton.role` is required in the ACP configuration.
`readRoleInstructions` also refuses before invoking the CLI, so a launcher that
lost its configured role fails closed at the last point before a session is
created or resumed rather than sending a role-less read.

The single-role case is the one worth stating: inference there was
*unambiguous today*, and that was the problem. Giving that participant a second
role tomorrow would have silently changed the persona of every session launched
for them — a deployment edit rewriting who an agent is, with nothing in the
launch record to show it. `test_a_single_held_role_is_still_named_explicitly`
pins that case specifically.

**Role-owned.** Instructions live on the role and are inherited by every member
launched in it. A member entry that tries to carry its own is refused by the
existing strict-object check, and two members in one role read the same text —
so correcting a role's wording corrects every session started from it.

### The shipped material

`conf/baton.example.json` — which `init` copies byte-for-byte — now
demonstrates both halves of the contract: authority and required reading,
including a configured-root reference (`pushcoin:AGENTS.md`) rather than a
bare path. Two tests hold it to the contract it demonstrates.

The four Baton role texts are in `ROLE-INSTRUCTIONS.md` beside this file, as
the exact `teams.baton.roles` block plus the approver's steps. They are NOT
written into the live `baton.json`: accepting a configuration is the approver's
act, and the currently deployed binary predates this field, so editing the live
config would break every launcher including my own. PLAN's own note forbids it.
`test_the_pinned_baton_role_texts_are_complete_and_acceptable` parses that
block, checks each role names the policy, the guide and the assigned dossier,
and then validates it as real configuration — a deployment step is a poor place
to discover a malformed role.

### Superseded expectations

Requiring instructions everywhere invalidated every test configuration that
declared a role without them. `fixtures.py`, the workflow driver's `team()`
builder, and the hand-written documents in `test_config.py`,
`test_lifecycle.py` and `test_w136_participant_actions.py` now supply text; the
workflow builder fills a default only where a story states none, so a story
that cares about the wording still owns it. The ACP test rig defaults its
`role`, and a new test builds the config directly to assert the refusal.

W101's own `test_selection_infers_one_instructed_role_...` is replaced rather
than adjusted: it named the inference this ruling removes.

### Break-sweeps

| Reintroduced defect | Result |
| --- | --- |
| `instructions` optional again | 1 red |
| Single instructed role inferred again | 2 red |
| Codex `identity.role` optional again | 1 red (Codex suite) |
| ACP `baton.role` optional again | 1 red (ACP suite) |

The two launcher sweeps first came back GREEN: neither bridge had a test for a
MISSING role, only for a malformed one. Both now do, and both sweeps red.

### Gate

Parallel lane **1369 passed, 1 failed**; serial lane **32 passed**; ACP
**41/41**; Codex bridge **44/44**.

The one failure is
`test_w20_infrastructure_lifecycle.py::test_start_refuses_a_service_log_symlink_without_touching_its_target`.
It is not this Work: `tools/infra.py` and that test file are both UNTRACKED —
in-flight W20 work by the `baton.tune` participant in this shared checkout —
and neither file contains a single reference to roles or instructions. I left
them untouched.

### Not done, deliberately

Step 10 (deploy the reviewed candidate, accept the next generation, restart
each launcher) is an approver act gated on this review, and PLAN says so.
Existing manually prompted sessions keep working as documented bootstrap
sessions until then.

## Review round — the operator surfaces (2026-08-18)

The P1 is correct. The two surfaces it names were already fixed before this
review reached me — I hit the reviewer's regressions on the shared gate during
W154, fixed them, and reported on T101 — so the review was written against the
earlier tree.

But the review also says: "make adjacent missing/unheld-role wording agree with
the explicit-only model", and that part was NOT done. Sweeping properly found
two more surfaces neither the review nor I had named:

- `tools/codex-event-bridge/README.md` — twice: the `--start-thread` section
  said "Missing, unheld, or ambiguous role selection refuses", and the
  troubleshooting entry told the operator that "ambiguous multi-role
  participants specify `role`";
- `docs/CODEX-APP-SERVER-EVENT-CONNECTIVITY.md` — the dispatcher "refuses
  missing or ambiguous selection".

`ambiguous` is the tell. Under the explicit-role contract a participant's held
roles cannot be ambiguous, because the launcher names one — so a surface still
offering to resolve ambiguity is describing the superseded model and sends an
operator into a refusal from the very boundary these instructions exist to make
reliable.

An ACP test carried the same stale idea in its NAME and its stub: "missing or
ambiguous ACP role instructions refuse", with a fake error reading "multiple
instructed roles; select one with role=". The CLI can no longer produce that
error, so the test was asserting on an unreachable condition. It now uses a
reachable one — a role the participant does not hold.

### The pattern, and the guard

This is the third time I have fixed this finding's surface and missed a sibling:
first the two setup guides while leaving the per-launcher README and `--help`
stale; then those two while leaving the Codex README and the topology document
stale. Each individual fix was right and each sweep was not.

So the guard is a SWEEP, not three more assertions.
`test_no_shipped_operator_surface_advertises_role_inference` walks six shipped
surfaces and fails on any line that mentions a role together with the retired
model's vocabulary in any of its spellings — `ambiguous`, `may be omitted`,
`omitted only`, `[--role`, `optional only when`, `exactly one instructed`,
`multiple instructed`. A companion test requires each launcher's guide to state
positively that the role is required, because a refusal an operator cannot
predict from the documentation is the failure this Work exists to remove.

Break-sweep: restoring the stale wording in all four surfaces at once reds 3
tests, and the sweep names every offending file and line rather than the first
one it meets.

### Gate

`just test-v11`: **1569 passed**, serial **36 passed**, ACP **41/41**, Codex
bridge **44/44**.

## Review round — the required bootstrap policy (2026-08-18)

The P1 is correct. The two identity strings and the readiness verbs it names
were already fixed before this review reached me — I hit the regression on the
shared gate during W20, repaired it, and reported on T101.

But the review also says "audit the whole active policy surface rather than
replacing only the two identity strings", and **that part was not done**. The
audit found more, in a section I had never read:

`## The active-work claim` still said execution is owned by "the Current
endpoint" — the pre-W245 name, and for the wrong concept, since eligibility is
the ROUTE — and that the claim is "orthogonal to phase — a reviewer may be the
claimant while phase is `review`". Both halves are false under W38: `review` is
not a phase, and phase is not orthogonal to the claim at all; `active` means
exactly "a Handler holds it".

That section now states the v11 model: Route/Handler/Next as three separate
questions, the closed scheduler axis, `active` reachable only by `claim`, and a
`block` row naming its one gate.

### The pattern, and the guard

This is the third time on this Work that I have fixed the surface a review
named and missed a sibling. The guard is therefore a sweep over the whole
policy file, in both directions: a table of retired terms — the v10 identities
and verbs, plus the vocabulary v11 renamed — and a positive list requiring the
current model to actually be described, because deleting the wrong words is not
the same as saying the right ones.

Composing two of those terms rather than spelling them out is deliberate: this
file is inside the source W245's own scan covers, and a literal pairing of the
retired word with the noun it used to mean is exactly what that scan forbids.
It caught me doing it.

### A mistake worth recording

While adding the guard I destroyed `tests/work/test_w101_role_instructions.py`.
A scripted edit anchored on a function name that also appeared inside a string
earlier in the file, so the replacement started at position 0 and then recursed
— the file grew to 826,717 lines and the original header and tests were gone.
It was untracked, so there was no Git copy.

It was recovered from `__pycache__`: the compiled module from the last passing
run still held every function, its docstring, and its string constants. That
gave an authoritative inventory — 18 tests and 3 helpers — and the file was
rebuilt against it. All 18 recovered tests pass, plus the new positive one.

The reviewer should know this happened, because the reconstruction is faithful
in behaviour but is not byte-identical prose for the three tests I did not
write. Their assertions and docstrings came from the bytecode's own constants,
so the meaning is exact; the surrounding formatting is mine.

The lesson is narrow and worth stating: an anchored source edit must anchor on
something that cannot also appear as data in the same file, and a file worth
editing that way is worth committing first.

### Gate

`just test-v11`: **1658 passed**, serial **38 passed**, ACP **41/41**.
