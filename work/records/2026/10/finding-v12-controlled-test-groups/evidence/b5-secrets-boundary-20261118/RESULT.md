# B5 batch G4 + G5: the six secrets-inventory and authority-boundary ids (M385070)

K, copilot under owner claim E384905, no claim held. Review: `review-2026-11-18T02-15-55Z.md`.
Source: owner commit 438eefa6 plus the accepted B5 diagnostic candidate (errors.py, workspaces.py,
test_workspaces.py) plus this slice's three files; content digest c5bdea87… identical before and after
every run here (`source.json`, `source-after.json`). Before-evidence for all six: the reconciliation's
`evidence/b5-reconciliation-20261118/unresolved-ids.log`.

## G4 — tests.manager.test_secrets (3 ids)

What the inventories found was real registry drift, not a sweep defect:

- `test_no_declared_coverage_is_stale`: `("review_cycles.py", "create_line", "review_lines")` named a
  writer that no longer exists -- W301404 moved `create_line`'s INSERT into `_reserved_line` under the
  held preparation (the module's own docstrings say so). Entry removed, its reason re-sited.
- `test_every_durable_writer_is_covered`: nine writers had no coverage. Each is now registered in
  `COVERED_ELSEWHERE` by the path that actually runs: `_reserved_line` (every free operand crossed the
  `review-line.create.prepare` signature's walk first), `_completed_line` and `_published_recorded_line`
  (two measured numbers + a constant, inside the journalled act / from a journalled result),
  `_withdraw_publication` (constants and NULLs), `release_writer` x2 (constant state, clock, constant
  reason; the caller's free reason is a member of the result the journalled act walks inside the same
  transaction), `restore_abandoned_correction` x2 (constants and clock inside the journalled restore
  act), `intake._no_start_declared` (the constant axis value, inside a declaration whose signature
  walked the operator's reason). No writer was exempted from §13; each reason names its walk.
- `test_every_exported_callable_is_in_exactly_one_class`: eleven exported surfaces unaccounted
  (`ControlStore.open_readonly`, `ControlStore.snapshot`, the five deadline operations, the four
  abandonment operations). All eleven are classified `RETURNS_NO_CONSTRUCTED_ARTEFACT` with the reason
  for each: readers replay journalled results or project rows; mutators answer journalled closed results
  whose operands ride `manager_signature`; the read-only opener's failure answers a refusal whose
  constructor proves its own message. `fence_pre_attach_abandonment` takes a free `reason` and is
  classified like `abandon_attempt` (its precedent) -- and, unlike that precedent, MEASURED.

Real negative evidence (`TheReviewLineWritersRefuseALiveBearerBeforeTheyWrite`, 3 tests, self-contained
fixture: configured storage and group, a nominated source, an attempt row, a profile double, a port double):

- `create_line` with a live bearer in `declared_base`: `secret-leak`, no `review_lines` row, the profile
  never materialized.
- `release_writer` on a granted writer whose runtime is quiescent with disposition `unable` (W365075's
  nothing-to-review round), bearer in `reason`: `secret-leak`; the writer row stays `active` with no
  `revoked_at`, the line stays `writing`; the same release with an ordinary reason then revokes it with
  the constant reason `released` and returns the line to `idle`.
- `fence_pre_attach_abandonment` on a never-started attempt, bearer in `reason`: `secret-leak`; the
  attempt's execution axis is unchanged, the port was never asked, no abandonment operation row exists;
  the same declaration with an ordinary reason then writes `cancel-requested` and fences once.

## G5 — tests.authority.test_boundary (3 ids)

- `EveryDiagnosticIsBoundedByTheRule` x2: `authority/store.py` had grown three unbounded
  interpolations: `_writable`'s `{what}` (two literal callers, but the rule proves origin, not
  spelling) and `_connect_readonly`'s `{type(failure).__name__}` and `{failure}` (the sqlite driver's
  own words, unbounded). Product correction: `label_of(what)`, `type_name_of(failure)` and
  `name_of(str(failure))` -- the module's existing bounding helpers; `str` on a `sqlite3.Error` runs the
  driver's formatting, not a caller's, which is the same reading the worker manager's `_said` takes.
  The pinned named-site list is unchanged and matches again.
- `Isolation.test_nothing_reaches_for_v11_the_node_host_or_a_dossier`: `opt/baton` is forbidden
  because a v11 deployment lives at `/opt/baton` on the HOST. `source_boundary.MARKER_TARGET`
  (`/opt/baton/verifier-layout-marker.json`) is a file INSIDE the worker image's rootfs: the recipe
  (`v12/worker/Dockerfile.claude`) copies it there and `claude_agent.LAYOUT_MARKER` reads it; the
  manager composes the marker's content and never opens the path. Resolution: an exact table
  `IN_CONTAINER_DECLARATIONS` keyed by module and constant with the exact value and reason, skipped by
  the forbidden-word scan only for that module and that value, and PROVED by
  `test_an_in_container_declaration_is_not_a_reach`: the value is that constant's one module-level
  assignment; the literal occurs exactly once in the whole package; nothing in the manager package
  LOADS the constant (so no code can reach through it); the worker consumer spells the same path.
  Every other literal in every module is still scanned for every forbidden word.

## Verification (focused; no group/full/Docker/live, no 95-path sweep)

| run | result | log |
|---|---|---|
| the six ids, one invocation | 6 OK | six-ids-after.log |
| tests.manager.test_secrets (whole module, incl. the 3 new evidence tests) | 95 OK | secrets-module.log |
| tests.authority.test_boundary (whole module, incl. the new proof) | 25 OK | authority-boundary-module.log |
| tests.authority.test_store, job_manager.test_store_readonly, job_manager.test_status, tools.test_accepted_base (readers of the changed authority refusals) | 164 OK | authority-store-regressions.log |

Fixture roots under /var/tmp are removed by each test's cleanup; identity stable.

## Candidate

`CANDIDATE-SHA256.txt`: authority/store.py, tests/authority/test_boundary.py, tests/manager/test_secrets.py.
`candidate.diff` against 438eefa6 covers those three files only; the tree also carries the accepted
B5 diagnostic candidate (three other files), unchanged. Paths touched this slice: those three.
