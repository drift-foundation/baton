# The isolated continuation packet, revision 2 — W321776, claim 329953

**Supersedes `continuation-329810`, which is preserved unchanged** (sealed
manifest `1afddeeb3db646f5f574a41898a7084e3cbe192fd724202afca33f656507efdc`,
re-verified member-by-member this claim). Review 2026-10-19T05-00-43Z accepted
that packet's composition — checkpoint as pinned input rather than base, source
from the declared committed base, `/2` launch with `/3` produced behaviour, the
`-c` wrapper not mistaken for paired 102 evidence, the module names as a
convention — and required exactly one preparation revision: turn the
acknowledged-inadequate historical bounds into a **concrete proposal**, resolved
from the generated submission rather than from prose, with the policy digest,
packet bounds, submission and `LIMITS-CHECK` in agreement, re-pinned and proved.

Two things differ from 329810, and nothing else does:

1. **The proposed bounds**, below — and one requested value that this vehicle
   cannot express, reported rather than faked.
2. **A real defect in the sealed gate, found while proving the revision.** The
   329810 program set `sys.path` only, which is in-process; named cases in the
   credential gate spawn the operator as a **subprocess**, so the gate failed
   `test_help_names_the_credential_source_the_launcher_requires` with returncode
   1 because the child could not import `baton_v12` — a failure about the
   command's own environment, not about any candidate. The program now also
   assigns `PYTHONPATH` from the same two derived facts, overwriting rather than
   extending so no ambient value leaks in. Measured both ways over the eight
   gate names that exist at the base: **209 tests, one failure without the
   assignment and none with it (0.248s).** The argv still carries no environment
   assignment; the program derives the value, which is what the contract asks.

The rest of this document is 329810's, which the same review accepted.

## Why there was a 329810 at all

Review 2026-10-19T04-39-20Z preserved the delivered Stage-A slice and ruled the
**vehicle** wrong: host working-tree edits carry no selected v12 Job or attempt
provenance, and uncommitted bytes may not be treated as accepted source. The
required next step was named exactly — *prepare a concrete digest-bound isolated
v12 continuation packet consuming this exact checkpoint as explicit input, with
freshly bound accepted base, a supported `/2` launch, image/run/destination
identities, the candidate import and retention boundary, isolation and focused
acceptance. No launch authorized.*

This is that packet. **Nothing is executed against the selected root, no Job is
submitted, no engine, container or provider is invoked, no credential is read,
no product file is edited and no mutating version-control operation is
performed.** The preparation steps were exercised once into a throwaway root;
`PREFLIGHT.json` is the record.

## What the vehicle is, and why this one

| element | selection |
| --- | --- |
| mechanism | `baton.single-implementation-packet/2` — an isolated instance with its own authority, stores and staged manager code, driven by the single-implementation supervisor |
| why | it is the vehicle the sibling implementation Work in this same campaign (W321528) actually ran on, so "selected v12 Job/attempt provenance" means this, not a new mechanism invented here |
| launch envelope | `baton.dogfood-task/2`, because both selected holders check the schema by closed equality (`claude_agent.py:117`, `dogfood_operator.py:768`) and a `/3` launch would refuse before the implementation turn could type anything |
| base | `bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c`, this tree's committed HEAD, read at the start of this claim and again before sealing |
| checkpoint | five preserved files as **digest-bound inputs**, never as a base |

## The checkpoint is an INPUT, and that is the whole correction

The delivered slice is five uncommitted host files. Three mechanisms keep them
from being mistaken for accepted source:

1. **`candidate-input/`** holds them as byte-for-byte buffers, copied from the
   reviewer's own preserved copies under `evidence/review-329794/checkpoint/`.
2. **`fixture.files`** in the composed packet pins all 13 task inputs. The
   supervisor's `held_packet` re-pins every one *before any store opens*, so a
   drifted buffer refuses the run rather than silently changing what the turn
   consumes.
3. **`restore.py`** places them inside the private checkout and nowhere else.
   It refuses `/input/source`, the canonical host checkout and its own record
   root as destinations, validates **every** buffer *and* every base file before
   its first write, and refuses a file where the base carries none — so a
   checkout that is not the declared base cannot be overwritten into looking
   like one. Its digest is named in the task text and in `LOAD-COMMAND.txt`, and
   `verify-inputs.py` compares the two.

The declared base genuinely does not carry two of the five, and that is
recorded rather than papered over:

| path | at the base | restored |
| --- | --- | --- |
| `v12/python/src/baton_v12/verification_context.py` | **absent** | `f599072a…` (26520 B) |
| `v12/python/tests/manager/test_verification_context.py` | **absent** | `42dcbfc9…` (35250 B) |
| `v12/worker/Dockerfile.claude` | `9f7e439b…` | `487748a0…` (14206 B) |
| `v12/.dockerignore` | `7aae9bcf…` | `b7da7ead…` (2931 B) |
| `v12/python/tests/manager/test_claude_agent.py` | `42191d07…` | `215e9db2…` (211808 B) |

Every digest above was compared this claim against **three** independent
holders — the reviewer's `CHECKPOINT.json` declaration, the reviewer's
byte-for-byte copies, and the live tree — and all three agree. The preserved
host files were **not edited** by this claim.

## Identities, all concrete

Run `paired-context-w321776-329953`; selected root
`/home/sl/baton-instances/paired-context-w321776-329953` (absent, and `stage`
refuses an existing root); worker image
`baton-v12-claude-worker:w239528-244216` at config digest
`sha256:c862c055…`, **existing and not rebuilt**; manager runtime the installed
distro at binary `sha256 04aa459a…`, build commit `1e576ff2`; manager source
112 files taken from the **declared base** rather than from the working tree;
supervisor `baseline.py` at the base's `c1b0a10e…`. `OPERATOR.md` carries each
owner command, labelled, with the start command marked as the owner's act and
**not authorized by this packet**.

## The launch is `/2`; the acceptance surface is `/3`. Both were asked, not assumed

`CONTEXT-CHECK.json` records three questions put to the code that owns each
answer, with nothing materialized and no store opened:

| question | asked of | answer |
| --- | --- | --- |
| would the operator stage this launch? | `tools.dogfood_operator.held_task`, staged from the base | **yes** — `/2`, `source_root` `source`, `git-line`, base `bbdacb5d…` |
| is the declared `/3` context Stage-A ready? | the **packet buffer** of `verification_context.held()`, with pairing delegated to the base's own `checkout_plan` | **ready**; derived import path `candidate/v12/python/src` |
| does the generation boundary hold in both directions? | the same module | a `/2` task asked for Stage A → `invalid-layout/schema`; a `/2` task carrying the member → `invalid-layout/verification_context`; a `/3` task lacking it → the same |

The declared layout is the accepted packet's: the whole prepared repository at
`candidate/`, `working_directory` at `candidate/v12/python`, `import_roots`
`["src"]`, the sealed fixture at
`sealed/worker-control-api-manifest-vectors/vectors.json` — disjoint from
`candidate/` in both directions, VER-2 satisfied — and the in-candidate copy the
gate must read declared as a `candidate.pins` entry at the same digest
(`sha256:fcc19dbd…`, 19351 B, measured again this claim).

### One interpretation a reviewer should judge as an interpretation

**The sealed verification argv is a `-c` program, not the packet's literal
argv.** The literal 102-test argv assumes a working directory and a derived
`PYTHONPATH`, and both come from `verification_context` — a `/3` member. The
launch envelope is `/2`, which has no such member, and the argv carries no
environment assignment, so under `/2` the command must establish its own cwd and
import path. The sealed gate therefore runs the same six credential-gate names
*plus* the restored contract, the image-recipe cases, and the two new modules,
under a program that sets `v12/python` and `src` itself. **The literal argv
remains the `/3` obligation**, to be exercised in the two independently
materialized views the turn produces — which is what `VERIFICATION.md` asks for
and what this launch cannot itself prove.

### The gate names modules that do not exist yet, on purpose

A sealed argv cannot name classes a turn has not written, so the module names
are the convention and the task states them: the worker view and its Stage B in
`tests/manager/test_verification_views.py`, the operator view and its Stage B in
`tests/tools/test_operator_verification_view.py`. Neither exists at the base, so
the gate **fails until the turn creates them**. The gate also refuses a skip:
VER-5 admits none, and a skipped obligation wearing a passing exit status is
exactly the outcome the paired acceptance exists to prevent.

## Bounds — a concrete proposal, resolved from the generated documents

`LIMITS-CHECK.json` is **composed from the packet, policy and submission this
preparation actually generated**, not written as prose, and it asserts that the
four agree:

| bound | proposed | where it is resolved from |
| --- | --- | --- |
| provider turn | **3600s** | `bounds.turn_seconds` → `policy.provider_turn_seconds` → `submission.execution_limits.provider_turn_seconds` |
| verification command | **30s** | fixed by the composer in fresh mode; see below |
| total | **4800s** | `bounds.total_seconds` |
| cleanup reserved | **60s** | `bounds.cleanup_seconds`; serving 4740s |
| invocations / retry / terminal | 1 / none / `report-and-hold` | unchanged |

Residual total margin is 4740 − 3600 − 30 = **1110s**. This is an estimate for
one invocation — not a correctness guarantee, and not an authorization.

**The 900s verification ceiling the review asked for is not expressible on this
vehicle.** In fresh mode the composer fixes `verification_command_seconds` at
`30` in both places it appears — `baseline_bindings.py:345`, the execution
policy whose digest the submission carries, and `:522`, the submission's own
`execution_limits` — with no compose parameter and no bounds member. Three ways
not taken, and why:

- **editing `baseline_bindings.py`** would change accepted supervisor product
  that this claim does not own, to obtain a number;
- **switching to contextual mode** does yield 900s at `:345`, but it changes the
  packet schema to `/1`, the runtime profile to `claude-context-implementation`,
  and drops `verification_command_seconds` from the submission altogether — a
  different workload chosen for a limit;
- **writing 900 into `LIMITS-CHECK.json` anyway** would be the prose-only edit
  the review explicitly refused.

The 30s ceiling is also measured rather than assumed: the eight gate names that
exist at the base run **209 tests in 0.248s**, and the two modules the turn adds
are pure-Python view tests. If a reviewer judges 30s inadequate once those exist,
the ceiling is a supervisor-product question for the owner of
`finding-v12-single-implementation-proof`, not something this packet can set.

## What this packet does NOT claim

- It does not deliver the two view materializers. Stages 6 and 8, Stage B in
  both views, `/3` at both holders and `proposal/3` + `operator-evidence/1`
  remain **unstarted**; `claude_agent.py` and `dogfood_operator.py` are
  untouched at the base.
- It does not re-run the broad suites and does not rebuild the image. The
  reviewer forbade both for preparation, and the delivered travel path is
  already covered by the recipe cases inside the sealed gate.
- It does not assert a blanket gate over W325695. That Work owns the
  verifier-descriptor defect and touches overlapping paths; the task text
  forbids redesigning the verification environment or forcing a green run, and
  concrete disjoint ownership or serial selection is a coordination decision
  recorded for its owner, not a condition invented here.
- It accepts nothing. A retained candidate is not an accepted one; independent
  review and the human checkpoint remain required.

## Members

`PACKET.md` (this) · `PROVENANCE.json` · `PREPARATION-PINS.json` · `TASK.md` ·
`LOAD-COMMAND.txt` · `candidate-input/` (5 buffers) · `restore.py` ·
`prepare.py` · `verify-inputs.py` · `CONTEXT-CHECK.json` · `LIMITS-CHECK.json` ·
`GATE-CHECK.json` · `PREFLIGHT.json` · `OPERATOR.md` · `PACKET-INPUTS.json`
(sealed last, naming every member above).

## The sealed gate, run verbatim

`GATE-CHECK.json` takes the `verification` member out of the **generated** task
document and runs it as-is, from a root holding the declared base plus the five
restored buffers, with a deliberately useless `PYTHONPATH` offered in the
environment. Result: **status 1, 211 tests, 0.246s, and exactly two errors** —
`tests.manager.test_verification_views` and
`tests.tools.test_operator_verification_view`, the two modules the turn must
write. No credential-gate case fails, which is what proves the derived import
path now reaches a child process while no ambient value leaks in. A gate that
passed here would mean the convention was not actually requiring the new work.
