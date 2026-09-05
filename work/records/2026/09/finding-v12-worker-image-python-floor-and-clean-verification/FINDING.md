# Make v12 worker verification Python-floor-correct and candidate-clean

Ledger Work: W85497

## Confirmed defect — 2026-09-04

The first ordinary self-hosted W71917 retry used Claude worker image
`sha256:30117fe6f1b65c0e5315a04a19638f146f05b504b7fa756215a235fca2df388a`.
The provider completed successfully, but the worker reported
`verification-failed` because its mandatory command
`python3 -m compileall -q src tests tools` exited 1.

The failure is an image/runtime mismatch, not a syntax defect introduced by
the candidate:

- `v12/python/pyproject.toml` requires Python `>=3.13`;
- `v12/worker/Dockerfile.claude` starts from `node:22-bookworm-slim` and
  installs Debian's unversioned `python3`, which is Python 3.11;
- the exact image rejected unchanged
  `src/baton_v12/worker_manager/custody.py:752` with an unterminated-string
  syntax error;
- the collected candidate passes the same full compile command on host Python
  3.13.7 when bytecode is redirected outside the candidate.

The verification also polluted the proposal. Its compile pass wrote 149
`cpython-311` cache paths into the candidate. The resulting patch was
10,779,527 bytes although only ten non-cache paths differed. Verification is
not allowed to turn its own generated artifacts into proposed source changes.

## Decision

A provider-backed worker image that verifies or executes v12 Python source
must carry the distribution's declared Python floor, currently 3.13 or newer.
The selected image is proved by its immutable digest; a host-side successful
gate does not excuse a mismatched worker interpreter.

Verification writes all interpreter caches and other ephemeral artifacts
outside the candidate tree. A proposal's changed-path inventory contains only
workload changes, never artifacts created by the verifier itself. This is a
bounded correction to the selected Claude worker image and verification
runner, not a general image-reproducibility or supply-chain redesign.

The W71917 run6 proposal remains retained as diagnostic evidence. It is not
reviewed or imported because its worker terminal is faulted and its proposal
inventory is contaminated.

## Acceptance

- The selected Claude worker image reports Python 3.13 or newer before any
  workload is admitted to it.
- The unchanged committed v12 baseline passes the mandatory compile command
  in that exact image.
- A compile verification cannot create `__pycache__`, `.pyc`, build, or cache
  entries in the candidate or its proposed changed-path inventory.
- A deliberately invalid Python file still produces a typed verification
  failure without hiding its useful diagnostic from the operator.
- A focused real-image regression proves the interpreter floor and a
  candidate-clean successful verification before W71917 is retried.

## Reviewer research — 2026-09-04

**Confirmed.** The selected image really is derived from the current
`v12/worker/Dockerfile.claude` recipe. Local immutable-image inspection shows
entrypoint `python3 /opt/baton/dogfood_entry.py`, fixed user `65532:65532`, and
the accepted closed runtime environment. The recipe installs Debian
Bookworm's unversioned `python3` into `node:22-bookworm-slim`; recipe
inspection and the run6 measurement therefore agree that the image cannot
satisfy `pyproject.toml`'s Python `>=3.13` floor. The existing reference
worker recipe already names a locally present, reviewed Python 3.13 image
digest, but copying or changing bases remains a candidate recipe until the
dogfood image itself is built and probed. A Docker registry lookup was denied
by this managed reviewer's network policy, so no mutable-tag availability is
asserted here.

**Confirmed.** Setting only Dockerfile `PYTHONDONTWRITEBYTECODE=1` cannot
solve the cache defect. `compileall` explicitly writes bytecode despite that
setting; a local Python 3.13 reproduction created
`__pycache__/probe.cpython-313.pyc`. The same command with
`PYTHONPYCACHEPREFIX` pointed outside the source wrote its caches only below
that prefix. In addition, both `ClaudeAgent._provider` and `_verify` pass a
composed `env` to `subprocess.run`, so image-level environment members are not
inherited by either child unless the adapter deliberately includes them.

**Confirmed.** There are two verification executions and they have different
custody effects:

- `v12/worker/claude_agent.py::ClaudeAgent.work` walks and diffs the private
  candidate before `_verify`, then publishes only that pre-verification
  `written` list. An entry added only by this inner verification is counted by
  the safety rewalk but is not copied into the proposal. However, the provider
  is explicitly prompted to run the command itself before returning, and its
  environment has no external cache root; caches created during that provider
  turn are present before the walk and therefore become proposed paths.
- `v12/python/tools/dogfood_operator.py::_derived` is the direct retained-tree
  pollution boundary measured in run6. After freeze and intake it computes
  `changed = sorted(_changed_paths(...))`, then runs the frozen verification
  with `cwd=candidate`, inherited environment, and no external cache root.
  Its generated entries therefore mutate the custody candidate after the
  changed-path answer was computed. This explains how independent evidence
  can report the ten workload paths while later proposal packaging sees the
  additional 149 caches.

**Confirmed.** `_derived` currently sends both verification streams to
`DEVNULL`. That makes a nonzero return code typed at the later `_Lost`
boundary, but discards `compileall`'s filename, line, caret, and `SyntaxError`
diagnostic even though this independent host-side rerun is not the
credential-bearing child governed by the worker adapter's no-stream ruling.
The correction must not put child output into proposal or durable protocol
evidence, but it must leave the supervising operator an actionable bounded
diagnostic.

**Observed baseline.** Before correction,
`tests.manager.test_claude_agent` passes 87 cases and
`tests.tools.test_dogfood_operator` passes 331 cases. The managed reviewer can
inspect the retained image but cannot start containers or query the registry;
the required build and exact-image probes must run in the implementation gate
and be recorded by digest rather than treated as skipped.

## Proposed implementation boundary

**Proposed.** Keep the Node 22 provider runtime and install a Python 3.13-or-
newer runtime by an explicit reviewed recipe change. A move to the matching
Debian suite or a multi-stage import from the already reviewed Python base is
acceptable only if the built artefact proves both `python3` and the pinned
Claude CLI work under the existing non-root, read-only-root, no-secret and
network boundaries. Recipe text, a host Python result, and a mutable tag are
not substitutes for that artefact proof.

**Proposed.** Give the provider child and the worker's inner verification
child explicit cache, temporary and non-credential home roots below the
private scratch directory but outside `candidate`. Preserve the provider's
prepared credential home; do not forward the ambient environment. This keeps
a provider that follows the prompt and runs `compileall` from adding bytecode
before the candidate walk, and keeps the adapter's own verification from
mutating the private candidate afterwards.

**Proposed.** Give the operator's independent rerun a temporary/cache root
outside the custody proposal and prove the entire candidate path/byte snapshot
is unchanged across a successful compile. The result continues to record the
frozen argv and integer status only. On failure, surface a bounded actionable
diagnostic to the supervising operator without copying it into the candidate,
proposal members, evidence JSON, recap, or Baton message.

The newly built image is recorded as a candidate digest first. Independent
review validates the exact digest and its path set; only then may the owning
record explicitly select it and authorize another ordinary W71917 attempt.
Building a new tag, editing a grants file, or passing host tests does not
select an image.

## Decision clarification — 2026-09-04 — verifier roots are descriptor-bound

Review `review-2026-09-04T18-59-48Z.md` confirmed that pathname validation
cannot establish the verifier-root boundary. A provider descendant may outlive
its leader and replace a validated root before the verification child resolves
the same name.

The verifier's `HOME`, bytecode, temporary, and cache roots are therefore
opened before the provider runs and carried as directory descriptors held only
by the adapter. The verification child inherits those exact descriptors and
receives `/proc/self/fd/<n>` names; it never resolves a provider-writable root
pathname. Immediately before launch the adapter validates the held directory
objects themselves. A provider may rename or replace the visible names, but it
cannot redirect the objects the verifier receives. This descriptor binding is
the accepted correction to the surviving-descendant race; a later return to
pathname-only validation would supersede this decision and requires new
evidence.

## Selected image — 2026-09-04

Review `review-2026-09-04T21-41-01Z.md` approves proposal
`sha256:ed4a6743689e320776fa1ee46010c4f8b932ef4fdce2856c7204002194ad4056`
and its exact candidate image
`sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f`.
That immutable image is now the selected Claude dogfood worker image. Its
embedded adapter digest is
`sha256:516d350e3ca367b61fd33520cbfe3de4d69dbe9dee0da0a6553bd37c3349b60c`.

This selection supersedes every earlier candidate image recorded in this
finding. It authorizes a fresh ordinary W71917 attempt; it does not authorize
rebuilding under the same tag, substituting another digest, or importing the
faulted and cache-contaminated run6 proposal.
