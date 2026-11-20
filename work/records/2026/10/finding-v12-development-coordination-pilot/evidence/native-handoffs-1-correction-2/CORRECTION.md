# W385331 slice 1 — correction round 2: refreshed digest-bound candidate answering delta review 2026-11-20T20-53-37Z (R4a)

K (`baton.prompt`), 2026-11-20, under the owner-held W321608 arrangement (no claim held), on the owner's instruction: "Read M385365 and review-2026-11-20T20-53-37Z.md. Correct the remaining R4 validation defect in isolation, prove malformed addresses leave no policy changes and valid routing still works, then return a refreshed digest-bound packet for delta review. Preserve the accepted R1–R3 fixes. No import, rebuild or live launch." Isolated copy only; host tree, instance `native-handoffs-1`, stores and Git untouched. A candidate for independent DELTA review, not acceptance; nothing live was run, no image was rebuilt.

## Identities

| | |
|---|---|
| Base | `3d05430f97ca9d4a516b51d15eb940840a6f0eff` |
| Retained parent | `a743edebacf5c744020083ee68549f2bd1fa91f7` |
| Previously reviewed candidate | tree `sha256:766f97f2e49809c5a2ebedece65d3ebd6f6d4d933b795efd2490b4726368345a`, manifest `97eb669f…` (`evidence/native-handoffs-1-correction/`), R1–R3 resolved, R4a requested in M385365 |
| This candidate | 36 paths; tree digest **`sha256:f62bbaab53c7d6a7f9730b726d68fac8cefe48a92130cdc176924acd1ec64028`** over `candidate.sha256` |
| `manifest.json` | sha256 `4925897d2bdf6e343d6eac229544b7c2c308f31fbf59ce01ec8b70b9c2aafd24` |
| `candidate-from-3d05430f.patch` | `sha256:265f6d3e3205ea5ad6a72dc552d8ea322907707e302d932d45a05e19f923ed2c`; `patch -p1` onto an archive of `3d05430f` reproduces every path byte for byte (`provenance.json`) |
| `delta-from-a743edeb.patch` | `sha256:8f0395dafe87c3eab006a7eb22da90d9fdbccea5b9281dfe7c9e4d87118ddf92`; from the retained candidate |
| `delta-from-766f97f2.patch` | `sha256:9a50ac60147c5d29e7aa91d5b6554c3fce001e9b297afb57199d89895d35566b`; **the delta for review**, from the previously reviewed candidate (reconstructed from its own packet and verified against its `candidate.sha256`, 35/35) |

`candidate/` holds every changed file at its repository path. Host Git was used read-only (`archive`, `hash-object`); the host working tree stayed at `3d05430f` with `v12/` clean before, during and after. Every R1–R3 byte is preserved: the delta touches no `src/baton_v12` file and no worker file.

## What changed against the reviewed candidate (4 paths)

- `v12/STACK.md` (modified vs reviewed; modified vs base): routing paragraph: addresses held to the Authority's grammar; whole document proved before the installer's first effect
- `v12/python/tests/tools/test_bootstrap.py` (modified vs reviewed; modified vs base): R4a: malformed decision recipient and reviewer refused by the shared grammar across nine spellings with nothing composed; the grammar is the shared validator; a refused repeat leaves the valid policy and grant unchanged; same-address wording follows the validator; no existing case changed
- `v12/python/tests/tools/test_connected_creation.py` (modified vs reviewed; modified vs base): R4a through the REAL installer and command: `TheNativeRoutingThroughTheRealInstaller` — fresh two-role install with the selection → ordinary `/3` creation via `job_manager.main` → scoped `answer-handoff` grant and no `review` grant (the reviewer's positive probe, retained); malformed decision recipient and malformed reviewer refused by `bootstrap.main` with exit 2 and nothing durable at the destination (the reviewer's failing probe, now refused); a refused one-operand repeat leaves `install-inputs.json` and the policy unchanged
- `v12/python/tools/bootstrap.py` (modified vs reviewed; modified vs base): R4a: `_routing_faults` applies `authority.messages.check_routing` (grammar of both addresses and the one-address rule, stated once there) and keeps the membership/separation checks; `main` proves the routing selection (`_routing_preflight`, the same check `held` makes) before admitting a runtime, cloning repositories or making prerequisite roots, in both the destination and the repeat forms

The other 32 paths are byte-identical to `766f97f2` (`against_previous: unchanged` per path in `manifest.json`); `tests/tools/test_connected_creation.py` joins the set.

## R4a — malformed addresses are refused before any effect

- **The grammar is the Authority's and stated once.** `bootstrap._routing_faults` now builds the exact policy document `_compose` would persist and asks `authority.messages.check_routing` about it — the validator `Authority.native_routing()` applies at every handoff-capable preparation. Its refusal text is the fault. The role-membership check (the reviewer is a configured review worker's participant) and the implementation/reviewer separation check stay in bootstrap; the one-address-for-both-roles rule is the validator's and the duplicate bootstrap spelling was removed. No second grammar exists.
- **The selection is proved before the first effect.** `bootstrap.main` admits the runtime and clones repositories (destination form) or makes prerequisite roots and clones worker sources (repeat form) BEFORE `prepare` holds the whole document — deliberately, so those admissions' own refusals are reached in their own words — which meant a malformed address could earn durable effects even with the grammar check. `main` now calls `_routing_preflight(document)` — pure, exactly the routing check `held` makes — immediately after the destination's `state_root` is derived and at the top of the repeat form. (A first cut proved the WHOLE document there; it changed the refusal four existing installer cases pin for deliberately skeletal documents and was withdrawn in favour of the selection-only preflight, which is what R4a asks.) A refused install leaves no selector, record, configuration, Authority store or install document; a refused repeat leaves the installed selection and `install-inputs.json` unchanged.
- **Proofs.** `tests.tools.test_bootstrap.TheNativeHandoffRoutingIsConfiguredHere` (14): nine malformed spellings for the decision recipient and for the reviewer (`not-an-address`, `baton.`, `.member`, `Baton.Reviewer`, `baton reviewer`, `baton.reviewer.extra`, `baton/reviewer`, `1baton.reviewer`, `baton.-x`) refused with "a participant is team.member" and nothing composed; the shared validator refuses exactly those and the accepted selection reads back; a refused repeat leaves policy and grant unchanged; the earlier ten cases retained. `tests.tools.test_connected_creation.TheNativeRoutingThroughTheRealInstaller` (4), through `bootstrap.main` and `job_manager.main`: fresh two-role install with the selection → ordinary `/3` creation under `native-handoff/1` → `answer-handoff` held by the reviewer in the Work's scope, `review` not held, the Job handoff-capable, the selection kept in `install-inputs.json` and absent from the execution document; the reviewer's own failing probe (malformed decision recipient) now exits 2 with "refused: … a participant is team.member" and nothing durable at the destination; a malformed reviewer likewise; a refused one-operand repeat leaves `install-inputs.json` bytes and the Authority policy unchanged.
- **No existing test expectation changed.** `test_bootstrap.py` gains only the new cases; every other test path is byte-identical to the reviewed candidate.

## Verification (prepared interpreter 3.13.7 at `/home/sl/.local/state/baton-v12-venv`; roots `BATON_V12_STACK_TEST_ROOT=/var/tmp/baton-v12-handoffs-1/recovery`, `TMPDIR=work/scratch/w383217/handoffs-recovery/tmp`; final runs 21:16–21:26Z on the outside-checkout copy `/var/tmp/baton-v12-handoffs-1/tree`, byte-equal to `candidate/`; logs in `logs/`)

| Run | Result |
|---|---|
| The Job's exact six-module argv (`final-six-module.log`) | **Ran 342, OK** (unchanged from round 1; no src or worker byte changed) |
| `test_bootstrap`, `test_connected_creation`, `test_environment`, `test_instance`, `test_stack` together (`final-focused-bootstrap.log`) | Ran 538, OK — the four installer cases the withdrawn whole-document preflight had broken pass unchanged |
| `just test-group authority` (`final-group-authority.log`) | collected 509, passed 509 |
| `just test-group scans` (`final-group-scans.log`) | collected 494, **passed 492 + 2 optional skips**; 0 failures |
| `just test-group job_manager` (`final-group-job_manager.log`) | collected 1718, passed 1715, failed 3 — the SAME three identities as both earlier rounds (`test_store_readonly` ×1, `test_tool` ×2; host-baseline evidence from the first continuation, not rerun on the host) |
| `just test-group tools-pure` (`final-group-tools-pure.log`) | collected 3520 (+8 new cases), passed 3517, failed 2 + 1 error — exactly `test_live_ab` (host baseline, earlier) and `test_source_identity` ×2 (declared inputs a copy lacks, earlier); round 1's transient PR-seed case passed here, which does NOT attribute it |
| manager-pure, run as its 59 modules MINUS `tests.manager.test_checkpoint_profiles` (`final-manager-pure-minus-hazard.log`; `python -m unittest`, NOT the accounted group runner) | Ran 4391, failed 6 — the SAME six identities as both earlier rounds (`test_store.ReadonlyAcquisition`, `test_integration_worker` ×2, `test_custody` host baseline; `test_frozen`, `test_w197661_verifier` need `build/`); the hazardous module's 3 classes NOT rerun, unverified on this candidate |
| Withdrawn first cut (`logs/withdrawn-whole-document-preflight/`) | the chain run on the cut that proved the whole document early: six-module 342 OK, authority 509, scans 492+2, job_manager 1715/1718, manager-pure 4391/6 as always, tools-pure 3513/3520 with FOUR extra failures (`test_environment` ×1, `test_instance` ×3: pinned refusals for deliberately skeletal installer documents) — the reason that cut was withdrawn for the selection-only preflight; retained as evidence, not as a result of this candidate |

Measured wall: six-module 19 s; focused 49 s; authority 2 s; scans 103 s; job_manager 16 s; tools-pure 170 s; manager-pure-minus-hazard 240 s.


## Limitations and what is not claimed

- No live provider, engine, container, image or instance; the installer runs against a stand-in one-folder runtime exactly as `test_connected_creation` always has. The worker image must be rebuilt for the adapter change before any live use.
- `tests.manager.test_checkpoint_profiles` was NOT rerun (disclosed hazard); its three classes remain unverified on this candidate.
- The transient tools-pure PR-seed failure of round 1 remains cause unknown; a pass here does not attribute it.
- The next slice (Work filing / blocking prerequisite) is untouched. The separate "cause unknown" status finding stands.
