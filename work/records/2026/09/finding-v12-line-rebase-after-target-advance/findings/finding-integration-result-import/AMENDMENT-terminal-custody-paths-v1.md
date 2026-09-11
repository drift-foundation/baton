# Q terminal custody — exact two-path scope amendment

**Approved by owner baton.slaw return136677, 2026-09-10T13:50:24Z.**
Reviewer136680 pins that ruling before dispatch. The pending-approval language
below is superseded; the substantive two-path amendment and existing95s/10s
ceilings are accepted. DELIVERY-SCOPE-2026-09-10.md controls the happy-path
minimum and W136578 remains parked. No further scope decision is required
for these exact terminal-custody changes.

Proposed by reviewer136606 after P acceptance136604. No new Work or budget.
This is the one demonstrated source-scope omission preventing Q's already
accepted terminal transition; it is not deferred hardening.

## Observed requirement and gap

P's accepted integration/reconciliation.py declares IMPORT_KIND but
_expected_signature returns None for that kind (current line1583), and
_CHAIN_FOR_STATE requires it for imported. Thus every imported result refuses
result_of even if Q settles a real matching entry. Q explicitly owns terminal
import/receipt linkage, but its accepted twelve-source/nine-test allowlist
omits this custody owner and its imported-state tests. Implementing only Q's
listed execution/queue files cannot make that reader accept legitimate success.

The record already has entry_id and the necessary result/source/assignment/
publication/evidence bindings; no additional schema change is proposed.
P's result is proven through authorized import-account resolution, so Q's next
visible result is actual bytes imported, verified and terminally accounted for.

## Exact requested addition to Q's existing allowlist

- v12/python/src/baton_v12/integration/reconciliation.py — only define the
  legitimate terminal import transition/signature and its typed reader/replay
  binding to this result, matching integrated entry, derived Authority receipt
  and retained source/publication/authorization chain. A terminal writer such
  as record_imported(store, authority, *, result_id, entry_id) resolves the
  existing owners' settlement and receipt; no caller success boolean. Q's
  already allowed execution/driver owners call it at their actual settlement.
- v12/python/tests/integration/test_reconciliation.py — replace only the
  temporary expectation that no imported result can exist with a valid matching
  terminal success/readback control; preserve missing/invented/unrelated entry
  and missing/foreign receipt refusals and existing P acceptance controls.

Base is independently accepted candidate136400: reconciliation.py SHA-256
caa250d3bca47f713e9b49ed33646c9cdfad6f6a01fa80c2fe01b9388612470a,
92162 bytes,0664; test_reconciliation.py SHA-256
55c25a07bc11993dad4afb6c1a622a90fe85f2dd4a39ea2be6cbe982ded465fe,
91387 bytes,0664. Full retained base is in sibling custody dossier
evidence/review-136558/candidate/. Revalidate before edits. Q is the next serial
writer after P closure, so no file ownership overlap is introduced.

## Acceptance, scope and decision

Use parent DELIVERY-SCOPE-2026-09-10.md's owner-directed minimum. Required Q
positive imports the reviewed combined bytes, verifies them, aligns target
reference and Authority cursor, records matching terminal custody and releases
the actual capacity. Preserve essential unapproved/stale-target/path/mode/
writer-exclusion and false-terminal refusal controls, reusing accepted evidence.
The exhaustive crash/tamper/race matrix is parked W136578; no added recovery
guarantee or acceptance sweep is proposed. R still owns actual ordinary A/B
terminal composition and consumers reuse that evidence.

Approve these two exact path additions and the bounded expectation change
within Q's existing95s author/10s review ceilings, both0 product runtime spent.
All other Q source scope stays fixed; no Authority/Manager/schema source
expansion, live migration, broad verification, P transfer or new allocation.
Existing W71830 test authority applies once this exact scope is accepted.
If approved, pin the ruling in Q FINDING and parent scope then dispatch Q's
implementation immediately. If rejected, identify another concrete terminal
owner; do not claim the imported state passed or rerun unrelated P controls.
