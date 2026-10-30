
## 2026-10-22 — baton.claude, claim354646 — THE CHEAP TWO-STAGE SHAPE IS RULED OUT BY PRODUCT REFUSAL

Claimed at snapshot354646 after reading canonical state (queued, unclaimed,
routed `baton.impl`, `last_change_seq 354642`, zero open blockers, new child
W354630 created at 354630), the complete handoff through `work-events` (92
events, no pagination remaining) and thread T325959 in full (5 messages,
`last_seq 329708`, unchanged). Read `review-2026-10-22T19-47-41Z.md`.

**Scope narrowed, and I respected it.** Stop/cancel, cleanup/unknown holds and
persisted restart moved to child **W354630** (codxpc) with its own
`test_native_stop_restart.py`. Mine is now the two-stage acquisition /
beyond-900 proof and the joined owner-failure → `/7` status → packaged report.
I did not duplicate the child proof, edit its test path, or read into its
dossier.

### What I tried, and what the product said

The cheap shape: drive the review stage's **own** acquisition independently
through `SingleWorkerCase` — the harness that already reaches a real acquired
token — by composing a review-kind stage with no predecessor and setting the
deployment's `launch_role` to `review`. Both operands are parameterisable, so
it looked available.

It is not. `single_worker.py:296 _held` refuses:

> `ContractRefusal('policy','denied')`: *"this deployment launches
> implementation and this configuration names 'review'"*

So **`single_worker`'s deployment is implementation-only by design** — the
review role is served by `stage_execution`'s composed review worker, not by
`single_worker.operations_from`. The shortcut is not awkward, it is refused,
and the refusal is correct. **I deleted the non-working case rather than
leaving it behind**: the module is back to 12 OK at the same digest as
claim354604, and no product byte changed.

### The harness split that is the real cost

- `SingleWorkerCase` reaches a **real** acquired token — my proved
  implementation-stage case — but is structurally single-stage and now
  implementation-only *by product refusal* rather than by fixture shape.
- `ComposedLifecycleCase` drives one Job through **both** stages, but its own
  docstring says the freeze, intake, retention and cleanup operations are *not
  performed* because *"they need an engine, a delivered workspace and a custody
  tree, which is the live proof's half"* — exactly the half where a token is
  acquired.
- `ServingCase` composes both stage workers for real and is the **only** base
  with a review worker at all, but its existing cases assert composition
  rather than acquisition.

The two harnesses split along precisely the line this proof must cross.
`ServingCase` is the only base with both halves present.

**Exact next step**: build the review-stage acquisition on `ServingCase`, whose
composed review worker is the only one the product will launch in that role —
drive *its own* runtime start against an admitted review stage with a delivered
workspace, then observe that worker's acquired token: its own generation, its
Job's composed lifetime, above 900. The implementation half is already proved
at claim354566.

### Remaining owed

The review stage's own acquired token (route above), and the joined
owner-produced cause through durable capture, `/7` status and the packaged
secret-free report.

### Unchanged

All four product paths byte-unchanged; **zero product edits**. Test file
identical to claim354604 — the attempted case was added and removed inside this
claim. The 31-path composition plus my five paths stands, manifest and delta
unchanged. All five link-reversion arms retained in their own evidence
directories, not repeated.

Measured: three focused runs at 0.260s, 0.242s, 0.252s. No live instance,
engine, provider or credential; no deployment, recovery, migration or shared
import; no version-control mutation — reads only.
