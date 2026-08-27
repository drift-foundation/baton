# Plan: local OCI lifecycle composition

1. [blocked on component and manager Jobs] Revalidate every dependency's final
   public contract before integration.
2. [pending] Compose consent teardown, activation and fresh execution creation.
3. [pending] Compose cancel, quiescence, freeze, collect, destroy and positive
   absence with effectively-once operation identities.
4. [pending] Run Docker restart/race/failure evidence and compatible Podman
   evidence where available.
5. [pending] Return for independent integration review; do not claim W6's
   portable conformance result.

## 2026-08-27 — first implementer round

- [done] 1. Every dependency's final public contract revalidated. Ten closed,
  **W6634 non-satisfying**; the provisional reach mapped call by call, and the
  acceptance clause on satisfying dependencies recorded as unmet.
- [done] 2. Consent teardown, activation and fresh execution creation composed
  against a real engine, including consent proved absent BEFORE the execution
  container is created, and the input-root authorization measured at both
  manager boundaries and at the adapter's own seam.
- [partial] 3. Cancel and quiescence composed with effectively-once identities;
  fence-then-stop established off one ordering trace. **Freeze, collect, destroy
  and positive absence are NOT composed** — all four are reachable only through
  W6634's provisional code, and that reachability fact is itself established by
  a case rather than asserted.
- [partial] 4. Docker restart, race, partition and failure evidence composed.
  Podman is absent on this host; the cases are written and skip narrowly.
- [done] 5. Returned for independent integration review. No portable
  conformance result is claimed and nothing is closed.

### Open, and none of them mine to settle

- [review, blocking] May integration proceed across a non-satisfying
  dependency, or does W6634's half need a successor Work before W6636 can reach
  terminal signoff? The acceptance says it may not; only review can rule.
- [needs an owner] `run_vector` composes no `--env`, so no worker the adapter
  starts can run. Component defect, surfaced by composition.
- [needs an owner] No manager operation calls `adapter.observe`, so an exited
  worker is recorded `running`. Component defect, surfaced by composition.
- [needs an owner] No operation joins the `consent_runtime` axis to the consent
  posture; the composition drives the adapter directly meanwhile.
- [needs an owner] W19784 left `check_input_pair`'s three receiving parameters
  unregistered in the contracts inventory's `OWNERS` table, so the full-tree
  gate carries a seventh failure beyond the accepted six. Mine originally, and
  that Work is closed satisfying — not mine to edit now.

## 2026-08-27 — independent review disposition

- [done] Preserve the 24-case module and 18-mutation harness as diagnostic
  integration evidence. Do not describe any tested arc as certified: the
  shared `start` and `destroy` paths include W6634's provisional changes even
  with empty output and credential operands.
- [decision required] Approve two successor Work items to W6634: one for output
  custody and one for credential delivery, with the shared start/destroy
  settlement crossing assigned explicitly. Neither successor inherits
  acceptance from the retained provisional tree.
- [queued after decision] File bounded correction Work for (a) delivery of the
  four non-secret worker launch values through the OCI seam, (b) exact
  `adapter.observe` use during reconciliation, and (c) a manager-owned consent
  runtime operation. Each needs a positive real-engine regression replacing
  the current expected-failure reproduction.
- [queued after decision] File a follow-up to W19784 for the three missing
  `check_input_pair` inventory owners, add the closed W19784 dependency and its
  correction as W6636 gates, and restore the aggregate gate to only its
  explicitly accepted baseline.
- [blocked] Resume lifecycle composition only after those component/correction
  Works close satisfying. Then run independent Docker review across success,
  refusal, cancellation, retry, restart, uncertainty, freeze, collect,
  destroy, positive absence and cleanup recovery; run the same Podman contract
  when the daemon is available.

## 2026-08-27 — approver decomposition ruling

- [approved] Split W6634's required surface into independently reviewed output
  custody and fresh-run credential-delivery successors; keep W6634 terminal
  non-satisfying and treat its tree only as provisional input.
- [approved] W6636 owns the successors' shared start/destroy settlement
  crossing plus restart adoption, reconciliation and orphan convergence.
- [next reviewer] Create and bind those two successor Works plus bounded
  correction Works for launch environment, exact observation, manager-owned
  consent and W19784 inventory ownership. Add W19784 as historical dependency
  and all six new Works as live W6636 blockers; index them in this plan.
- [blocked implementation] Resume W6636 only after all six close satisfying.
  Preserve the diagnostic suite, convert its expected failures into positive
  real-engine regressions, complete the remaining lifecycle matrix and return
  for independent Docker review.

## 2026-08-27 — decomposition recorded

- [live blocker] W26283, “Build OCI output custody provider,” bound to
  `work/records/2026/08/finding-v12-oci-output-custody/`.
- [live blocker] W26284, “Build OCI fresh-run credential delivery provider,”
  bound to `work/records/2026/08/finding-v12-oci-fresh-run-credentials/`.
- [live blocker] W26291, “Deliver reference-worker launch environment through
  OCI,” bound to
  `work/records/2026/08/finding-v12-oci-worker-launch-environment/`.
- [live blocker] W26294, “Reconcile exact OCI runtime state through adapter
  observation,” bound to
  `work/records/2026/08/finding-v12-oci-runtime-observation/`.
- [live blocker] W26295, “Compose manager-owned consent runtime lifecycle,”
  bound to `work/records/2026/08/finding-v12-manager-consent-runtime/`.
- [live blocker] W26296, “Register check_input_pair receiver ownership,” bound
  to `work/records/2026/08/finding-check-input-pair-inventory-follow-up/` and
  recorded as a follow-up to W19784.
- [historical provenance, ledger edge refused] W19784 supplies assignment
  identity and remains a closed satisfying prerequisite rather than a live
  implementation gate. The canonical CLI refused `block work=W6636
  on=W19784`: WS-2 permits blocker edges only to open Work. W26296's atomic
  `follow-up-of=W19784` relation and these records preserve the authorized
  history without bypassing the ledger rule.
- [blocked implementation] W6636 owns the shared crossing and later lifecycle
  matrix. It resumes only after W26283, W26284, W26291, W26294, W26295, and
  W26296 all close satisfying.
