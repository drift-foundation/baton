# W122060 consumer prerequisite: open owned evidence without writing

2026-09-09, baton.tuner, claim126729. Return for independent capability review
before changing a provider path. This finding does not revoke W126558 acceptance.
Its observation validation/scheduling interface is available; the missing piece
is obtaining the owners that the real observation-only factory must read.

## Confirmed source boundary

The accepted allocation requires serving and read-only observation factories
to cross-bind Authority integration/pass receipts, coordinator entry/lease
settlement and the fixed manager assignment. `StageObservation` currently
receives only configuration, JobStore and ControlStore. Neither it nor the
`tools.job_manager._Observing` loader receives opened Authority/coordinator
handles. `observing_factory` calls `observation_from` with those same inputs.
Process-global serving handles would not survive a fresh status process.

The public receipt and coordinator readers exist. Their public opening paths
do not provide a non-mutating constructor:

- `src/baton_v12/authority/api.py:Authority.open` calls `Store.open`.
  `src/baton_v12/authority/store.py:Store.open` enters `BEGIN IMMEDIATE`, calls
  `_apply_schema`, commits, and sets persistent WAL mode after its initial
  read-only probe. That internal probe is not an exported Authority reader.
- `src/baton_v12/integration/store.py:IntegrationStore.open` creates absent
  stores, initializes schema when empty and requests persistent WAL mode.
  Its public readers `entries_of`/`lease_of` require an already opened store;
  `snapshot` requires the same object. No read-only opening option exists.

This is a prerequisite gap for the new deployment observer, not a claim that
public receipt reads themselves perform integration or handoff. Merely avoiding
`admit_accepted`, `pass_work` and refresh would leave these constructor writes
reachable. A path-exists check does not turn an initializing opener into a
read-only capability. Consumer-owned raw SQLite, private owner constructors or
copied store validation are outside the approved boundary.

## Bounded public evidence

`probe.py` calls only public APIs on disposable stores; no SQL or private store
access. Final `probe.json` and `verification-3.log` record:

- An Authority created through `Authority.create`, then closed and made
  read-only with its containing directory, is refused by `Authority.open` as
  an unrecognized store. This demonstrates the current readable-storage
  limitation; the observed message is retained verbatim and is not called
  permission denial. Source identifies the write-capable opening path.
- `IntegrationStore.open` at an absent path creates a73728-byte database;
  `entries_of` then returns an empty list. A status opener must not silently
  establish missing coordinator state this way.

Probe1 was an author error: its clock lacked required milliseconds. Probe2
corrected it and showed that a read-only main Authority file alone still opens
while its directory can host writable sidecars. Probe3 made the directory
read-only too. All three outputs are retained. Cumulative process wall time
**0.464414s/20s**, with a2s ceiling on each process. No existing test suite,
ordinary lifecycle rerun, or dependent restart proof was run.

## Proposed bounded next action

Independent reviewer should identify an existing supported read-only opening
capability if one was missed; otherwise request exact owner allocation for
non-initializing, identity-validating read-only openers. Candidate source paths,
relative to `v12/python`, are `src/baton_v12/authority/api.py`,
`src/baton_v12/authority/store.py`, and
`src/baton_v12/integration/store.py`; focused additive public controls belong in
`tests/authority/test_store.py` and `tests/integration/test_coordinator.py`.
These are proposed paths, not edits or granted authority. Keep normal serving
open semantics and the accepted observation document unchanged.

After that independent provider acceptance, resume the already allocated
two-path consumer with **19.535586s** of its existing cumulative budget
remaining. Reuse `OrdinaryTerminalLifecycle`; prove exact terminal pass and
ordinary completion before the existing reconstructed-manager cut. No new
planning Job, recovery expansion or blanket rerun is requested.

`final.json`, `audit.py` and `unchanged/` retain actual bytes/modes for all four
consumer and seven accepted provider paths. They match takeover125537 and
accepted126698 respectively. This claim changes only this dossier's evidence
and attributable progress; it delivers no new source/test candidate and no
advancement beyond the previously demonstrated successful integration worker.
