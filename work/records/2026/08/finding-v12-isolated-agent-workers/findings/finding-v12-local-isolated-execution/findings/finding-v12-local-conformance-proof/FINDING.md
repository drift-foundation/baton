# Finding: prove the complete local isolated lifecycle

Work `W2931`, child of W1425. This is M2's final independent verification
slice and follows W2930.

## Confirmed boundary

Compose the reviewed v12 authority, Worker Manager, OCI adapter and reference
worker against a disposable authority and fixture repositories. Exercise one
complete local isolated lifecycle and independently assess every applicable
`local-oci` portable conformance case from the frozen 1.0 suite.

This Work owns harness, fixtures, immutable retained evidence and review. It
does not silently repair the implementations it certifies. A defect returns
to the owning child or creates a bound finding before any workaround.

## Acceptance

- Run the full positive Git and directory lifecycles from offer/consent through
  authoritative generation-bearing claim, writable activation, activity,
  quiescence, output freeze/collection and return.
- Run all 106 applicable local-OCI portable cases with exact required facts,
  evidence purposes, fixture/register/case/adapter/profile digests and derived
  assessments; the derived core verdict is `certified`.
- Preserve negative evidence for pre-claim execution denial, source/output
  integrity, isolation, credential canaries, policy/approval refusal, stale
  generation, cancellation ordering, unknown quiescence, restart, duplicate
  start, exact replay/collision and cleanup/intake boundaries.
- Recompute manifests/digests and authority projections independently; prove
  no disposable state entered the checkout and no worker received authority or
  canonical write capability.
- Keep W151 54/54, all 141 M1 design tests and the complete v12 package gate
  green. Counts are supporting evidence only; no missing/failed/unable core
  case may be hidden by a total.
- Record one append-only independent review and return W1425 for approver
  reconciliation. Provider certification, remote execution, M3 proposal
  integration and production rollout remain excluded.

## 2026-08-28 — critical-path revalidation after W5 capability pass

**Observed — the acceptance count is stale.** The current frozen case register
contains 135 cases applicable to `local-oci`, not the 106 named above. A count
cannot be used as a compatibility alias; the exact current case identities are
the certification boundary. See `evidence/w6-revalidation-2026-08-28.txt`.

**Confirmed conflict — three current core cases require the superseded
architecture.** `A-consent-sees-neither-input-document`,
`C-preclaim-no-execution`, and `H-consent-then-execution` require a consent
runtime/container. The campaign and satisfying W6636 now require reservation
without a runtime, atomic claim, and one execution container only after claim.
Passing both is impossible. Marking the three unobserved or unable correctly
derives `not-certified`; silently skipping them or fabricating consent evidence
would violate the conformance contract.

**Confirmed blocker to implementation:** W6 cannot honestly promise the
current acceptance's full `certified` verdict until the register receives an
explicit direct-topology supersession. That protocol/specification change is
not reviewer-owned and cannot be smuggled into a proof harness.

**Proposed next capability pass:** independently seal and assess the accepted
W6636 real-Docker evidence against an exact named subset of still-live
portable cases whose required facts the arc genuinely observes. Publish the
formal overall result as `not-certified` with every unobserved/conflicting case
named, plus a separate campaign conclusion that the evidence/assessment path
is promising. Split direct-topology register revision and exhaustive current-
register certification into later named Work. This exercises the conformance
machinery without claiming a verdict its own rules deny.

**Open decision:** approve that bounded W6 pass, or keep formal full
certification on the critical path and first authorize a conformance-register
revision. The choice materially changes W6 acceptance and needs approver
authority.

## 2026-08-28 — approver ruling and acceptance supersession

**Confirmed by approver response M33739:** use the bounded capability pass.
W6 shall seal and assess an exact named and digest-bound compatible subset of
the accepted W6636 evidence. It shall publish the honest formal
`not-certified` result, naming every unobserved or conflicting case, and shall
separately determine whether the evidence and assessment path demonstrate a
promising design.

**Superseded for this Work:** the original acceptance requiring “all 106”
local-OCI cases and a derived `certified` verdict is retained above as history
but is no longer actionable. The current register has 135 applicable cases and
three conflict with the approved direct claim-to-one-container topology; W6
must not hide, skip, or fabricate those gaps.

**Confirmed sequencing:** direct-topology register revision and exhaustive
current-register certification move to separate later Work. That rewrite does
not hold the present vertical-slice finish line. W6 remains a capability proof
of honest sealing/assessment plus a separately stated promising/not-promising
design conclusion, never a certification claim.

## 2026-08-28 — the bounded pass, run; what it measured

**Confirmed — the ruled pass is complete and its formal result is
`not-certified`.** Ten cases were observed by measurement against a real
Docker daemon through W6636's own composition fixture; eight were derived
`passed` and two `failed` by the frozen assessor; 125 are named unobserved in
`evidence/w6-capability-pass-2026-08-28.txt`, with no count alias and no
silent exclusion.

**Confirmed — the three topology conflicts are derivable, not merely
asserted.** The seal computes the conflicting set by asking which cases read a
fact only a consent runtime can produce, and returns exactly
`A-consent-sees-neither-input-document`, `C-preclaim-no-execution` and
`H-consent-then-execution`.

**New [P0], and it is not this Work's to fix — the execution container cannot
read its own `/input` pair.** Both manager-authored documents are written at
mode `0o400` owned by the manager's uid, and the container runs as
`65532:65532`; the launch document beside them is `0o444` and IS readable.
`workspaces.READ_ONLY_FILE` is `0o400` while `launch.READ_ONLY_FILE` is
`0o444`, and `launch.py`'s own prose explains why world-readable is correct
there. `baton_worker.py` reads both `/input` documents, so no worker can get
past reading its assignment.

**New [P0], same root cause — the container cannot write `/workspace`.** The
bind is read-write and the host root is the manager's uid, so the worker
cannot write the outputs it is required to declare.

**New [P1] — a specification conflict at the offer boundary.**
`C-decline-carrying-bearer-refused` requires a decline that transmits the
bearer to be refused `integrity/schema` with the offer un-terminated. v12's
reviewed boundary checks possession before branching on the decision, so such
a decline succeeds and settles `declined`. This is the same class as the
topology conflict: a specification decision, not reviewer-owned.

**Confirmed — the frozen suite admits no partial fixture.** `certify` refuses
a fixture that has not planted a canary in all ten surfaces, and behind it
`MANDATORY_FAULTS_BY_PROFILE` requires all 21 fault capabilities for
`local-oci`. A bounded pass therefore cannot reach a report through `certify`
without declaring capabilities it does not have. The enumeration is derived
instead by calling the frozen `assess` and `core_for` per case and applying
§6's disjunction to their output.

**Separate conclusion, as ruled:** the design and the assessment path are
**promising**. The machinery found two failures and a live defect against its
own author's interest. The one structural correction it needs is to admit a
fixture with declared capabilities and derive `unable` beyond them, which the
existing `faults_available` already supports — the all-or-nothing fixture door
makes incremental conformance impossible and rewards a fixture that overstates
itself.

## 2026-08-28 — revalidated after review, and an evidence-handling finding

**Confirmed — the pass survives the tree moving under it, and improves.** One
of the sixteen sealed inputs has changed since the reviewed run: `workspaces.py`,
by `W33935`, the Work this pass's own findings created. Re-run against the
current tree the frozen assessor derives
`A-assignment-manifest-delivered-read-only-beside-the-input` as **passed** where
it was **failed**, and the formal result is `not-certified` on one remaining
failure — the offer-contract conflict parked as `W33937`.

**That is the promising-design conclusion measured rather than argued:** the
machinery derived a failure from facts nobody had reported, the failure became
its own Work, the fix landed, and the same unedited assessor now derives the
corrected verdict.

**Operational finding against this Work's own harness.** The seal wrote its
pack to a fixed path, so re-running it overwrote the evidence the independent
review had verified by digest, and those bytes are unrecoverable. The reviewed
transcript survives and records every artifact's digest, so the pack remains
described and the review's verification stands; the bytes do not. The harness
now takes a run name and REFUSES to overwrite a pack that holds different
bytes, which is measured rather than asserted.

**Unchanged and not this Work's to resolve:** no independent party has executed
the arc end to end, because the reviewer's deployment is denied the Docker
socket and escalation is forbidden. A rerun by the implementer is not
independent verification of the implementer's own pack.

## 2026-08-28 — approver disposition M34887

**Confirmed by approver response M34887:** the independent sealed-pack
verification is sufficient to finish W6 **without a second independent Docker
execution**.

**The recorded result, in the ruling's own terms:** a **promising but formally
`not-certified` capability pass**. It is NOT integration certification and NOT
exhaustive certification of the current register, and no consumer may read it
as either. Independent Docker reproduction and exhaustive current-register
certification remain later Work.

**The overwrite limitation, recorded explicitly as the ruling requires.**
Re-running the seal overwrote the evidence pack the independent review had
verified by digest. The reviewed report was 36,491 bytes,
`sha256:6dea05a443e314d8f5e79541f2defef00c7736475e5345aed3a040e049c55ad5`; the
bytes now under that name are a later run's. **The original bytes are
unrecoverable.** What stands in their place, by this ruling, is the reviewer's
own transcript and its recomputed digests — retained at
`evidence/w6-review-verification-2026-08-28.md` with their read-only verifier
at `evidence/w6-review-verifier.py` — together with the reviewed run's own
transcript at `evidence/w6-capability-pass-2026-08-28.txt`, which records every
artifact's byte count and SHA-256. The pack is therefore fully DESCRIBED by
digest and independently verified; its bytes are gone.

**Named immutable evidence packs are required for subsequent runs**, and the
harness enforces it: `w6-conformance-seal.py <run-name>` writes under that name
and REFUSES to write different bytes over a retained artifact. Re-validated —
re-running into the reviewed pack exits non-zero with the operational finding
and the remedy named.

**The two runs are separate and named.** `w6-seal-2026-08-28b` with
`w6-capability-pass-2026-08-28b.txt` is the re-run whose verdict improved to
9 passed / 1 failed after W33935 landed; the reviewed run keeps its own
transcript. Nothing is presented as the reviewed pack.

## 2026-08-28 — independent disposition review

**Confirmed satisfying under approver M34887's superseded acceptance.** The
independently recomputed sealed-pack derivation, surviving transcript/digests,
explicit unrecoverable-byte limitation and named immutable-run correction are
the ruled finish line. No second independent Docker execution is required for
W6.

The outcome remains deliberately narrow: promising capability pass, formal
`not-certified`, not integration certification and not exhaustive current-
register certification. The current separately named re-run remains
`not-certified` with 9 passed, 1 failed and 125 named unobserved cases; its
report digest is
`sha256:82fc922bb40a5d7ff86e897b689f60e657173b89015cfa981d3addb27f75d6fb`.
The overwritten reviewed report's original digest remains the independently
recomputed `sha256:6dea05a4…49c55ad5`; its bytes remain unrecoverable and are
not claimed to exist.
