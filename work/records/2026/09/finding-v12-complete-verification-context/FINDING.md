# Make v12 verification context complete and explicit

Ledger Work: W61981

## Finding

W52821 run5b produced a retained candidate, but the operator's task verification
did not execute in a complete, declared verification context. The task invoked
Python without making the staged `src/` package importable, so the first run
failed to import `baton_v12`. An independent rerun with `PYTHONPATH=src`
executed 102 tests: 99 passed and three errored because those existing tests
load a durable evidence fixture under repository `work/records/...`, while the
retained proposal contained only the staged `v12/python` subtree.

The candidate is not rejected as defective by this evidence, and it is not
accepted. The verification environment failed to supply inputs required by
the selected test command. Treating an incomplete context as a candidate
failure obscures the cause; treating 99 passing cases as a complete gate would
silently weaken verification.

Run5b evidence is retained at
`/tmp/w52821/run5/evidence.json`. Its proposal locator is
`file:///tmp/w52821/run5/storage/attempt-w52821-run5b/custody/attempt-w52821-run5b/proposal`
with content digest
`sha256:416d79a230fe090bf95d9d71e716ff09d67c4efdf2bb3373d618c19937a838aa`.

## Confirmed scheduling decision — 2026-09-01

This defect is separate from W52821's credential-delivery implementation. Do
not widen or rerun W52821 to repair the worker platform. Address this finding
later in its own isolated v12 container. Until then, a missing package path,
repository fixture or other declared verification input fails the verification
context and never counts as a candidate verdict.

The worker's writable candidate boundary stays narrow. A complete verification
or review copy may combine that immutable candidate with all read-only source
and evidence inputs named by the selected gate; those inputs do not become
candidate output.

## Acceptance

- The task contract declares enough execution context to make the selected
  package importable without an operator-only environment workaround.
- The verifier materializes a separate complete review context containing every
  immutable repository input required by the selected tests.
- Missing declared inputs refuse with a bounded verification-context cause;
  they are not reported as candidate test failures or silently skipped.
- The W52821-style bounded gate runs with zero import skips and zero missing
  fixture errors in the worker and in an independently materialized review
  copy.
- The correction is produced by a fresh isolated v12 attempt and independently
  reviewed before import.

## Reviewer revalidation — 2026-09-01 (`baton.codex`, W61981)

### Observed — the candidate passes once the exact context is materialized

The retained run5b candidate was copied, without modifying the retained
artifact, to `/tmp/w61981-review.s8gDxE/candidate`. Running the frozen 102-test
vector there with only the missing import root corrected reproduced the report
exactly: 99 tests passed and three errored before their assertions. All three
load `tests.manager.test_output`, whose `VECTORS` constant derives this
repository-relative file from `__file__`:

```text
work/records/2026/08/finding-v12-isolated-agent-workers/
  findings/finding-v12-worker-contract/findings/
  finding-worker-control-api-manifests/evidence/vectors.json
```

A separate review tree was then materialized at
`/tmp/w61981-review.s8gDxE/context`: the candidate was placed at `v12/python`,
the one immutable vector at the canonical `work/records/...` path above, the
working directory was `v12/python`, and `PYTHONPATH=src` was explicit. The
same frozen argv ran 102 tests in 0.252 seconds and passed with zero skips and
zero errors. This is positive evidence that run5b is not a candidate failure;
its two missing context dimensions are independently sufficient to explain the
recorded result.

The exact commands, artifact identities and minimal layout are retained in
`evidence/research-2026-09-01/README.md`. The temporary review tree remains for
operator inspection; this managed reviewer performed no cleanup.

### Confirmed — worker and operator do not run one declared verification

The current `baton.dogfood-task/1` has exactly five members on both sides:
`schema`, `task_id`, `instructions`, `verification` and `source_root`.
`verification` is only an argv list. There is no working directory relative to
a repository view, import-root declaration, environment contract, immutable
input set or candidate placement.

The two executions then add different undeclared context:

- `v12/worker/claude_agent.py::_verify` runs with `cwd=candidate` and a closed
  environment containing only `HOME` and `PATH`. A src-layout package is
  therefore not importable.
- `v12/python/tools/dogfood_operator.py::_derived` also runs with
  `cwd=candidate`, but inherits the operator process's whole ambient
  environment. An operator-only `PYTHONPATH` can make this rerun behave
  differently from the worker even though both evidence records show the same
  argv.
- custody retains only the proposal and its candidate subtree. `_derived`
  receives the original staged source for its diff, but no immutable
  repository evidence root from which it could build the selected tests'
  repository layout.

The result vocabularies also collapse provenance. The worker proposal carries
only verification `status` and argv; independent evidence carries only
`verification_status` and argv. A missing package, missing immutable fixture,
command-start failure and ordinary failing assertion can all become status 1
or a generic inability. No existing closed member can say “the declared
verification context could not be materialized,” so changing prose alone
would not correct the durable result.

### Confirmed — existing protocol machinery can carry another immutable source

The frozen `baton.worker-manifest/input` already supports multiple named
sources and rejects duplicate names plus overlapping destinations.
`workspaces.compose_input_root` freezes the whole staged `/input` tree
read-only. The dogfood deployment, not the manager protocol, currently
hard-codes one `source` grant, one `stage_source` call and one input-manifest
source entry.

The smallest current-tree boundary therefore does not require inventing a
host locator in the worker, widening the writable candidate, or changing the
frozen manager manifest schema. The deployment can stage a second bounded,
no-follow immutable verification source through the same manager copier and
describe it as a second input-manifest source. The task can refer to that
input by its manifest name; it must never carry an absolute host path.

### Proposed — one versioned dogfood verification-context contract

Supersede task v1 with a closed `baton.dogfood-task/2` rather than adding
optional semantics to the frozen v1 shape. Its verification member should
declare, at minimum:

- the argv;
- one contained working directory in a separately materialized repository
  view;
- the candidate's contained destination in that view (`v12/python` for the
  measured gate);
- the named immutable input source(s) and their contained destinations;
- the exact required immutable paths that must exist before the command runs;
  and
- the import roots or a closed environment representation sufficient to make
  the selected package importable without ambient inheritance.

Both holders must apply the same path grammar: relative, canonical, bounded,
no `..`, no absolute path, no overlap between candidate and immutable input
destinations, and no duplicate destination. Task v1 must continue to refuse a
v2 member rather than interpreting the recognized subset.

For each execution, materialize a fresh private review root from two inputs:
the candidate copy and the sealed immutable verification source. Run from the
declared directory under a closed environment, then destroy or abandon only
that derived view. Never run in the retained candidate, add immutable evidence
to candidate output, let the candidate overwrite the sealed input, or resolve
a host repository path from inside the worker.

The worker and operator implementations are necessarily separate because the
isolated worker imports no manager package. Hold their literal schema,
members, path rules and context layout against each other in an agreement
test, as the current task constants already are. The independent operator must
materialize from the same sealed input source, not from whatever the host
checkout contains later.

### Proposed — distinguish context outcome from candidate verdict

Preflight every declared source, destination, working directory, import root
and required path before executing the verification argv. A missing or
unmaterializable member should preserve the candidate and answer a closed,
bounded context outcome such as `context-refused`, with a module-owned cause
from a small vocabulary (`missing-input`, `invalid-layout`, `materialization`
or `start-failure`). It must not copy exception prose, a host path or child
output into the proposal or evidence.

Only a command that actually started in a complete context may produce a test
exit status and therefore a candidate verification verdict. The worker
proposal and independent evidence schemas both need the outcome/cause; the
current bare integer is insufficient. The existing rule that verification
stdout/stderr remain discarded because the command can read the credential is
unchanged.

### Required regression matrix

- v1/v2 missing, extra and wrong-typed members refuse at both holders; their
  constants agree.
- Absolute, escaping, non-canonical, duplicate and overlapping context paths
  refuse before staging or provider work.
- The second immutable source is copied no-follow, bounded, represented by its
  input-manifest content digest and frozen with the whole input root.
- Missing declared source/path/import root reports `context-refused`, never a
  test failure, skip or raw exception; a real assertion failure remains a
  candidate verdict.
- Worker verification inherits no ambient import path; independent
  verification also ignores the operator's ambient import path.
- Candidate changes and deletions are reflected exactly in each fresh review
  view; neither the retained candidate nor immutable source is modified by a
  test.
- The W52821 102-test vector passes with zero skips/errors both in the isolated
  worker and in a separately materialized operator copy.
- Timeout, command-start failure and partial materialization clean up their
  owned derived root while preserving the retained candidate and sealed input.
- Proposal, evidence and transcripts remain free of child output, credentials,
  absolute host paths and arbitrary exception prose.

### Open decisions before implementation

1. Approve the exact task-v2 representation of import roots: a Python-specific
   relative path list is the narrowest measured correction; a generic
   task-supplied environment map is broader and needs an explicit allowlist and
   secret/durability analysis.
2. Approve the closed verification outcome/cause vocabulary and the resulting
   worker-proposal and dogfood-evidence member changes.
3. Decide whether the first implementation fixes candidate destination and
   repository working directory to this dogfood workload's measured
   `v12/python` layout, or permits task-selected contained values under the
   same overlap rules. Fixed values are the smaller first slice.

These are product/application contract decisions. No implementation should
start from the proposed shape until they are recorded as approved or replaced.

## Approver ruling — 2026-09-01

Slawomir approved a closed `baton.dogfood-task/2` verification-context
contract with the following first-slice boundaries.

Import roots are a Python-specific list of canonical contained relative paths,
such as `python_import_roots: ["src"]`. Both worker and independent operator
derive the same closed `PYTHONPATH` from that list inside their private review
root. Task v2 does not admit an arbitrary environment map, ambient inheritance,
absolute host paths or unrecognized environment keys. A later generic
environment facility, if needed, is a separate reviewed contract.

The task selects its repository working directory, candidate destination and
immutable-input destinations. Every value is canonical, relative and contained
under the fresh private review root. Absolute paths, `..`, duplicate
destinations and overlap between the writable candidate and immutable inputs
refuse before materialization or provider work. The measured W52821 values are
`v12/python`, but they are data under this grammar rather than hard-coded
application behavior.

Context and command result are two closed axes:

- context is `ready` or `refused`;
- a refused context carries exactly one of `missing-input`, `invalid-layout`,
  `materialization` or `start-failure`;
- command result is `not-run`, `passed`, `failed` or `timed-out`; and
- an exit status is present only when the child process supplies one.

Only `passed` or `failed` from a command that started in a `ready` context is a
candidate verdict. `refused`, `not-run` and `timed-out` preserve the candidate
but make no claim about its correctness. Durable documents use only the closed
values and safe structural facts; they never copy host paths, exception prose,
credentials or child output.

This ruling makes W61981 implementation-ready but does not schedule it now.
Its correction remains a separate future isolated v12 attempt and does not
block independent review of W52821.
