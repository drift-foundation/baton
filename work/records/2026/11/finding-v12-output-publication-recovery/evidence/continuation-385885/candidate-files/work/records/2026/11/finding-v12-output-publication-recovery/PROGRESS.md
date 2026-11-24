# Progress

Allocated for preparation; no implementation started.


## Checkpoint 2 delivered to review — 2026-11-23

Base 6079ad78. The deterministic publication slice is implemented: the `/4`
submission generation, the `baton.v12.worker-pool/2` publication lane, Job
store generation 10 and the enforced `output-publication-review/1` control
profile are installed, so an approved decision now reaches a REAL admission --
the prior assignment on the reused Work is ended through the Authority's own
exact-expect `Session.end` and the publication worker claims it fresh at a new
generation. The approved original is staged read-only through the host owner's
no-follow copy-and-measure pass, adopted byte-for-byte under that fresh
assignment with a separately bounded provenance beside it, taken into custody
by the ordinary freeze and intake, and handed to review by one record that is
the only thing that opens the gate. The 900-second publication bound is
derived from the persisted stage execution admission and enforced by the
control owner's own fence AND by the worker's supervisor; a restart re-derives
the same instant.

A deployment that has installed no publication worker still receives the
checkpoint-1 HELD admission naming that prerequisite, which is what the
shipped `tools.publication_decision:owners` factory answers on a freshly
bootstrapped instance. Four checkpoint-1 defects are corrected: the vacuous
`--scope` assertion, the misleading `require_ordinary_profile` documentation
(and the guard itself, which did not cover this recovery's profile), the
`refused/limit` hold pairing that raised an AssertionError instead of
refusing an oversized original, and a fabricated publication attempt identity.

Evidence: evidence/checkpoint2-385695/REPORT.md and focused.log, 302 focused
tests, zero failures. Prior 217-test coverage preserved. Checkpoint 3 remains:
production review binding and gate opening in the serving manager, the
independent reviewer's own tests and verdict under the 3600 s/900 s limits,
packaged installed CLI acceptance (`publication-resume`, `publication-status`),
and the deployment upgrade that installs the reusable publication worker once.
No existing-instance migration, no schema upgrade of any live store, no
deployment change and no live run was performed. The original Job remains
failed and its retained output is byte-identical.
