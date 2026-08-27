# W6634 design-checkpoint packet — 2026-08-26

Status: reviewer synthesis for approver scope review; not an eighth code review
or independent sign-off.

## Current output-custody contract

The manager reads `/output/output.json` before fresh custody mutation as one
bounded, no-follow, nonblocking regular file. It validates the closed
`completionManifest`, compares the exact assignment and one answer per declared
output, and derives the completion digest from the opened bytes. It then stages
declared regular-file trees into manager custody, checks limits and live-secret
content, freezes the staged copy, and atomically publishes the manager-owned
`resultManifest` as `sealed.json`. Exact committed replay proves request-to-
receipt identity first and does not re-read transient worker state.

The W19784 ruling will deliver the worker's exact assignment through
`/input/assignment.json`. That is the worker's sole completion-identity source;
this manager side continues comparing the completion with its independently
owned expected assignment before custody changes.

## Current credential-delivery contract

The assignment names closed logical slots. A trusted profile maps each slot to
a provider plus opaque reference; the manager registers returned bearer bytes
live before writing one 0600 file per slot beneath an assignment-private 0700
volatile root. The OCI adapter bind-mounts only those files read-only beneath
the fixed `/run/baton/credentials` root. Bearers are barred from argv,
environment, labels, durable documents, diagnostics and collected output.

Teardown keeps the live-secret registry armed through quiescence, output leak
checks, container removal and volatile-root deletion. It forgets bearers only
after absence is proved. Recovery currently attempts exact attempt/runtime/
mount/root adoption; disagreement stops the worker and performs targeted
bounded cleanup, retaining unresolved state when absence cannot be proved.

## Where the systems cross

The two subsystems meet at settlement:

1. the runtime must be quiescent before output is read;
2. credential bearers must remain registered while staged output content is
   scanned;
3. the container must be proved absent before its credential mount is removed;
4. credential-root and lifecycle-record absence must be proved before the
   attempt can report clean settlement or a free slot.

That crossing causes success, refusal, cancellation, retry, restart and
uncertain-engine paths in either subsystem to affect the other.

## Existing evidence

From `w6634-2026-08-26-seventh-review.txt`:

- sealing plus credentials: 110 tests, green;
- adjacent focused gate: 437 tests, green with one skip;
- all six seventh-correction guards measured by removal;
- aggregate: 1,420 tests, 13 failures, 4 errors, 6 skips;
- attribution of the 17 aggregate failures/errors: six standing shared
  boundary-inventory cases and eleven W6633 worker-image/container cases;
- `git diff --check`: clean.

The checkpoint deliberately did not rerun these as an eighth review.

## Residual design risk

- One Work currently owns two independently complex components and their
  settlement crossing; seven same-day review cycles are evidence the review
  unit is too broad.
- Restart adoption and orphan convergence are engine/lifecycle properties that
  need W6636's full state matrix, not only focused component cases.
- The current aggregate tree is red outside W6634, so no whole-tree acceptance
  claim is available.
- W19784's assignment-manifest delivery is approved but not yet implemented;
  end-to-end completion identity remains an integration dependency.
- The seventh correction is supported by implementer evidence but has not had
  an eighth independent code review, by explicit operator instruction.

## Recommended decomposition and immediate-spike boundary

Create independently reviewable output-custody and credential-delivery Work.
Move restart adoption, engine reconciliation and orphan convergence to W6636.
Retain the current tree as provisional evidence for those slices; do not erase
it or call it accepted merely because the focused gate is green.

For the first real Claude/Codex Docker spike, retain only the boundaries needed
to avoid lying about success or leaking credentials:

1. validate completion, assignment and declarations; stage immutable output;
   atomically publish and exactly replay the manager receipt;
2. materialize authorized slots for a fresh execution, mount them only at the
   fixed read-only root, keep leak detection armed through staging, and prove
   container/root teardown or fail closed; and
3. treat manager restart/adoption as outside spike certification. Preserve
   fail-closed behavior, quarantine unresolved material, and verify the full
   reconciliation matrix under W6636.

## Ledger action still required

The operator declared W17110 independent of W6634. The reviewer issued the
canonical unblock operation, but Baton refused it because W17110 routes to
`baton.impl` and the reviewer is not one of that endpoint's resolved handlers.
An implementer or approver with workflow authority must remove the edge. No
raw-store or source workaround is permitted.
