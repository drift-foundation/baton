# The isolated continuation packet — W321776, claim 329810

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

Run `paired-context-w321776-329810`; selected root
`/home/sl/baton-instances/paired-context-w321776-329810` (absent, and `stage`
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

## Bounds — carried, with the tension stated

`LIMITS-CHECK.json` resolves the accepted W321780 table through the manager's
own `execution_limits`: provider turn 900s, verification command 30s, total
1500s, cleanup 60s reserved, serving 1440s, one implementation invocation, no
automatic retry, `report-and-hold`. **This may be too small.** W321528 selected
3600s with a 4200s total and still spent its turn, and a paired
two-materializer change is larger than that slice. Raising an accepted bound is
the owner's act, so it is flagged in `OPERATOR.md` and not raised here.

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
`PREFLIGHT.json` · `OPERATOR.md` · `PACKET-INPUTS.json` (sealed last, naming
every member above).
