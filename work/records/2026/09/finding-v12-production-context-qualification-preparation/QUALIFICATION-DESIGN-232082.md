# The three remaining prerequisites, pinned — design and exact path boundaries (claim232082)

Per review-2026-09-21T17-49-06Z.md's accepted disposition: the feedback
slice is in; what remains before any live qualification is these three
guarded prerequisites, each pinned here with its exact paths, its selected
shape and its open owner decision — followed by the concrete packet. This
claim edits NOTHING outside this dossier: pinning is the deliverable, and
each slice below is implemented only after the owner selects it and only
within the paths it names.

## 1. Production profile qualification and model evidence

**Today:** `worker_manager/provider_context.py` `_profile` admits
`qualification == "deterministic"` only; `certify_context_profile` records
what it is given. There is no admissible production profile and no
evidence contract that could make one.

**Pinned design:** certification becomes evidence-driven. A profile with
`qualification: "production"` is certifiable ONLY with a retained
qualification receipt bound to it — the strict serving receipt of an
owner-selected qualification run carrying exactly the profile's
`model`/`reported_model`/`cli_build` and a `terminal: success` two-turn
open→restore pair, digest-bound to the run's attempt and conversation.
`certify_context_profile` gains the evidence operand and its validation;
`_profile` admits the second value only through that path. The
chicken-and-egg is resolved by the packet itself (§4): the qualification
run executes under an explicit one-run owner selection, not under a
production profile — its receipt is what mints one.

**Paths:** `worker_manager/provider_context.py` and the context suite.
Nothing else.

## 2. Cross-UID custody — an owner decision with two pinned branches

**Today:** `worker_manager/context_delivery.py`
`configure_context_storage` refuses a runtime UID different from the
manager's; `_private` demands manager ownership with no group/other bits;
roots are 0700. The retained campaign (candidate-183524) designed for a
TWO-UID world (fixed 65532 worker vs manager).

**The fact that decides the question:** the shipped runtime's W194457
ruling made the execution identity SHARED for these development
deployments — the worker runs as the manager's own euid. Under that
posture the current same-UID custody is not a stopgap; it is correct, and
"cross-UID custody" is NOT a prerequisite for qualifying the current
serving path.

**Branch A (recommended): production keeps the shared identity.** No
custody change at all; the prerequisite is closed by decision and
recorded. The qualification packet runs under exactly the custody that
exists.

**Branch B: production returns to two UIDs.** Then candidate-183524's
accepted findings apply — traversal-not-contents publication (0o2750
directories with setgid, files keeping their modes), group-based
delivery, and the two-UID inventory rules — and the exact paths are
`context_delivery.py` (`configure_context_storage`, `_private`,
`_directory`, `_read`/`_write` mode gates) plus the context suite's
custody cases. This branch is NOT recommended for the qualification
packet: it widens the change surface before the first live evidence
exists.

## 3. Real OCI context admission

**Today:** `worker_manager/oci.py` `OciAdapter._context_execution`
unconditionally refuses actual OCI context execution; the composed tests
mock the guard (correctly, and they say so).

**Pinned design:** the refusal becomes a NAMED PRECONDITION LIST rather
than a constant: admission requires (a) the deployment's context profile
certified per §1 — or the one-run owner qualification selection for the
packet itself; (b) context storage custody valid for the actual runtime
identity per the §2 decision; (c) the already-composed context mount
boundary (the mocked tests prove its shape; the unmocked positive becomes
possible only in the packet run). Each unmet precondition refuses by
name. The composed suite keeps its mocked cases AND gains the
named-refusal cases for the real guard.

**Paths:** `worker_manager/oci.py` (`_context_execution` only),
`tools/single_worker.py` (`_context_preflight` naming the same
preconditions), and the context/oci suites. No other adapter surface.

## 4. The concrete qualification packet (executable only after §1–§3)

ONE live two-turn qualification through the REAL serving path, owner
executed, separately selected:

- **Code/image:** the exact reviewed candidate at that point (today's
  candidate is `sha256:e84a033c6600…`, adapter `e42b2728…`; the packet
  names whatever the then-current accepted build is, independently
  rebuilt and selected — never an author-reported digest).
- **Custody:** per the §2 owner decision (Branch A: the existing
  same-UID storage, unchanged).
- **Profile/receipt contract:** a candidate profile naming the pinned
  CLI build and model; STRICT acceptance — the serving receipts must
  answer `terminal: success`, the profile's exact model and
  reported_model, and the derived conversation identity on BOTH turns;
  generation 1 must restore from the manager-reconstructed minimal
  state, which is the question the whole dossier was opened to answer.
- **The run:** episode 1 `open` with a trivial bounded task; a scripted
  changes-requested review; the correction episode `restore` — whose
  prompt now carries the findings (the accepted feedback slice), so the
  restore turn's answer must also demonstrate conversational continuity
  with turn 1's content.
- **Identity:** a FRESH sixth identity minted for this run by the owner
  selection; the five consumed identities stay consumed; no root
  repair.
- **Bounds:** two turns; 180 s per provider turn; 600 s total;
  `ordinary_verification` unchanged; no retry; report-and-hold; no
  production enabling regardless of outcome.
- **Evidence:** both receipts, both attempt rooms (the provider result
  JSONs are also the retained usage artifacts named under review230731
  R2), the reconstructed-state manifest, and a packet outcome record —
  all hash-bound in this dossier for independent review before any
  certification act (§1) consumes the receipt.
- **Operator command:** one line, composed by the implementation claim
  that lands §1–§3, gated fail-closed on the reviewed manifest exactly
  as this Work's earlier fixtures were.

## Order and ownership

§2 is an owner decision (recommended: Branch A) and costs nothing; §1 and
§3 are one bounded implementation claim each (or one combined claim —
they touch disjoint files); the packet is a preparation claim after both,
then the owner's separate live selection. Every consumed identity, every
retained byte and every guard stays exactly as it is until those
selections are made.
