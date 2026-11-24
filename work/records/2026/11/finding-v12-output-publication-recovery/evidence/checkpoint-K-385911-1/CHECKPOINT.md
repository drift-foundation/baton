# W385695 — internal checkpoint 1 under COMPLETION-PLAN-385909, with one blocking decision

**This is a recoverable progress checkpoint, not a candidate for acceptance.** It covers plan outcomes 1 and 3 and the owner-side half of outcome 2. Outcome 2's connected positive proof is blocked on the decision in section 3. Outcome 4 is not started.
Author: baton.prompt (K), owner-selected interactive continuation (M385911), no claim.
No host import, protected Git mutation, image build, engine or container operation, live call or credential read.

## 1. Identity

| | |
| --- | --- |
| Base | `6079ad78345aa87b7148db302d48fb9b1867f940` |
| Previous candidate (preserved, re-verified, 65 packet entries) | manifest `69b9328cfa8104dadb818af9d186818b6c70a9d5328e2a1bea06cc5650bebe75`, `evidence/continuation-K-385904/` |
| This checkpoint | `candidate-manifest.json` here; sha256 in `packet.sha256` and in the Baton message |
| Paths | 38 over base; 9 changed since `69b9328c` |
| Scratch repository | `work/scratch/w385695-K-385897/repo`, head `26b6e6cf8c92629aac1563c34f278476571ecde8` |

The 9 delta paths: `job_manager/publication_execution.py`, `job_manager/publication_recovery.py`, `worker_manager/workspaces.py`, `tools/publication_worker.py`, `tools/publication_ports.py`, `tools/publication_decision.py`, `tools/job_manager.py`, and the two publication test modules. `worker_manager/workspaces.py` and `tools/job_manager.py` are new to the path set.

## 2. What is done

### Outcome 1 — authoritative adoption fence and the terminal race

- `record_adoption` now asks this store's own fence and the persisted absolute bound **inside the transaction that would write the result**, at the manager's instant. A worker terminal that says `completed`, published after the worker's last gate, records no publication.
- A result committed earlier replays unchanged, after the bound and across a restart; nothing is re-judged.
- A refused adoption is recorded as what it was — `expired` or `cancelled` — in a new `publication.ended` record, not as an uncertainty. The worker's output stays on disk as evidence.
- The worker's own residual window (two small writes after its last gate) is unchanged and is now harmless to the result: the manager's commit boundary is what decides.
- The stage ending now decides the adoption **before** it records the worker's disposition on the attempt, so a fenced answer is one the manager did not take.

The review's `probe-window.py` passes unmodified.

### Outcome 3 — settlement, truthful status, owner item

- A new `settle` act in the publication pass, owed whenever a recovery did not publish and no owner item exists yet. It: classifies the ending once; takes a **fresh** engine read; settles through the composition's own supported fourth ending (`abandon_attempt`: exact runtime removed and proved absent, workspace retained, exact token returned); then delivers one owner item.
- An engine read that fails is journalled as `runtime-unknown`. Nothing is removed, the token stays held and no item claims a settlement. A later successful read is journalled as `runtime-known`; the pair alternates, one record per change of knowledge.
- The same fresh read now runs while a publication is in flight, so an unreadable engine reports `uncertain: true`, `outcome: unknown` and says the recorded axis is not current knowledge. The review's engine-unreachable probe shows this.
- The owner item goes to the participant who decided, names the retained evidence and remaining effects, and states `automatic_retry: false`. No retry, analysis or re-admission is started.
- **Read surface:** a new read-only installed command, `manager publication-status --decision-id …`. It reports the original failure, the admission, the recovery, the recorded runtime (labelled as recorded) and the owner item as separate statements, with no bytes, workspace paths or task text.
- Restart and lost reply: an interrupted settlement finishes on the next incarnation with one `abandon` effect.

The review's `probe-failure.py` passes unmodified.

### Outcome 2, owner side — the original is the declared output, and the line layout is located

Two corrections in `workspaces.retained_output_of`:

1. **The original is the declared output directory, not the whole writable root.** The accepted read measured the attempt's entire writable mount. For any real producer that mount is the candidate's working tree — and for a pooled producer a whole checkout with its repository. It only looked like "the proposal" in fixtures whose workspace held nothing else; a publication from it nested the tree one level down (`proposal/proposal/…`). The caller now passes the declared output's own path (one component, from the selected declaration) and that directory is what is proved, measured, staged and adopted. The completion signal at the writable root is reported by the owner as present or absent.
2. **The line layout is located from durable provenance.** For a line preparation the home is found through the writer grant this exact attempt and generation was given and the line that grant names. Required before measuring: the writer cannot write (revoked, or still this attempt's grant with its runtime destroyed and cleanup settled); no later writer was granted on the line; the home is its own directory in the reserved namespace with its persisted identity; and that identity is the one the attempt's preparation completed over.

This is my reading of "the original attempt output" in REC-9 and of "identical proposal bytes" in contract section 5. I am flagging it rather than asking, because the other reading cannot publish any real producer's output; say so if you want it treated as a decision.

Proof: `APooledProducersFailedOutputIsReadThroughItsLine` (6 cases). An ordinary pooled producer is run for real, overflows its ceiling, and is ended by the supported fourth ending. The owner read then measures its four-file proposal through the line, and the installed `publication-inspect` reads it. Negatives: unsettled attempt, whole-line read, path traversal, linked output, replaced line home, attempt with no writer, later writer.

## 3. BLOCKING DECISION — where the base commit may be read from

**The accepted source-correspondence port cannot read any real producer's bundle.** `claude_agent` writes `objects.bundle` as a thin `base..HEAD` transport. `SourceCorrespondence` creates an empty private repository and fetches both the declared base and the candidate **from that bundle only** — by its own stated rule, "not from a nominated checkout". With real git both fetches fail: the base is the bundle's prerequisite, not its content (`logs/observation-thin-bundle.py`). Checkpoint 1's cases pass because they stand the Git process in.

So after everything above, the default inspection of the really pooled producer still holds on "the measured bundle does not carry <base>", and no real recovery can be approved. This is outside R1–R3 and outcomes 1 and 3, and it gates outcome 2's connected proof and everything downstream of it.

The candidate's objects are in the bundle. What is missing is the declared base. Options:

- **A — the line's own recorded source (recommended).** The durable line record holds the repository the line was materialized from (`source_path`, with its persisted device and inode) and the declared base. Import the base from there by its full object name, then the candidate from the bundle. The base's *name* still comes only from the admitted task and the adapter's measured record; a content-addressed fetch by full name cannot return other bytes under that name. The source is a deployment input the workers are already served from, not a caller path.
- **B — the line home's own repository.** It holds both commits. It is also the producer's writable tree, so the manager would run a fetch against a repository a provider could have altered. Content addressing protects the objects but not the act of reading from it.
- **C — keep bundle-only and require a self-contained bundle.** Changes the producer adapter, and does nothing for outputs already retained, including the one this Work exists for.

A and B both touch the trust statement the accepted port makes about itself, which is why I am not choosing. With A the attempt-layout case (no line record) keeps bundle-only and holds as it does today.

## 4. Also found on the connected path

- The connected proof's Job must be created through the product's creation operation: a hand-submitted Job records no admitted task and inspection holds on it. That is a fixture requirement, not a product gap; I have not built that fixture yet.
- A running manager serves the bindings it started with (unchanged from the last report).

## 5. Verification on this checkpoint

| Run | Result |
| --- | --- |
| Four required modules | 358 collected, 358 passed, 44.750 s |
| Owner module, custody, intake, worker entry, packaging, installer, bootstrap, publication stage class, manager tool, sweep, delegation | 954 passed, 35.042 s (short scratch path) |
| Reviewer probes, unmodified | 9 of 10 pass |

The tenth, `review-385908/probe-pooled.py`, fails by design: it asserts that the inspection names a layout hold, and that hold no longer exists.

Not rerun for this checkpoint: whole `test_stage_execution`, the `job_manager` group, the `scans` group. `worker_manager/workspaces.py` changed, and the scan modules inventory that package; the scans remain incomplete and unattributed, now with a changed file in scope.

## 6. Tests changed since `69b9328c`

- Added: 10 cases for outcomes 1 and 3, 6 for the line-layout owner read.
- Modified, each because it asserted the superseded behaviour:
  - `test_an_uncertain_adoption_opens_no_gate_and_offers_no_review` asserted nothing was owed and the pass did nothing after a faulted worker — the stranded state the review measured. It now asserts the settlement is owed and performed, and still asserts no gate and no review offer.
  - `test_a_missing_original_holds_and_stages_nothing` expected a digest refusal from an emptied root; a missing declared output is now reported as missing.
  - `test_the_measured_original_must_carry_exactly_one_bundle` placed its second bundle at the writable root, which is no longer measured; it now places it inside the original.
  - Fixture helpers and three path assertions now address the declared output directory.
- No case was removed.

## 7. Not done

- Outcome 2's connected positive proof: real creation, real producer, default inspection eligible, exact decision, admission, publication. Blocked on section 3.
- Outcome 4 entirely: ordinary reviewer binding through the typed publication producer edge, connected command-to-review proof, restart cuts at each external effect, the acceptance matrix, and the qualification commands.
- Owner item for a recovery that closes before anything was launched is implemented and not yet covered by a case.
- No image build, container run or kernel confinement evidence.
