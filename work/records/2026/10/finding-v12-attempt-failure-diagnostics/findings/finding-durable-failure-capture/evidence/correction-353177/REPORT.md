# Replay attribution correction — baton.codxpc claim353177

Owner authority: FINDING section “2026-10-22 — owner selects isolated-host replay correction”, message353169 and reroute353174. This is the selected host exception, not a new v12 Job or a claim of v12 execution. Latest review addressed: review-2026-10-22T16-25-04Z.md, narrowed by subsequent owner priority.

Retained input2d313602 was reconstructed from base bc925cf5 and hash-verified retained patch044d58bc using read-only Git object reads and ordinary patch in /tmp/w341357-353177. All30 original evidence hashes verified. No Git mutation, shared product edit, old-root write or integration. Materialized base scopes: v12/, tools/, and the worker-control-api-manifests evidence/vectors.json named by the inventory test. TESTED-TREE.json pins the resulting input files; candidate files override the base. The absent candidate path in the main repository Git object lookup was resolved by using the retained patch, not by fetching or importing objects.

Exact replay comparison now precedes current-tip value deduplication. Two additive tests establish original and middle replay identity/document when the tip has equal facts, unchanged full public reader/history, and fresh same-value dedup. Both failed on the unchanged producer before the fix (revision0 returned2 and revision1 returned3). The existing91 producer test methods are AST-identical. Nine other retained candidate patch sections are verbatim, including R2 call sites, fixture fixes and the historical report.

Verification (each command limited to30s; exact argv and process durations in JSON, raw output in logs):

- Red: 2 tests, 2 expected failures; 0.011s unittest / 0.311192s process.
- Corrected focused module: 93 tests OK, no skips; 0.398s unittest / 0.706962s process.
- Unchanged retained five-module gate: 894 tests OK, no skips; 11.196s unittest / 11.526083s process.

Interpreter 3.13.7, Linux; PYTHONDONTWRITEBYTECODE=1, focused PYTHONPATH restricted to this copy's v12/python/src and v12/python. Gate clears inherited PYTHONPATH and uses its original argv to set its own roots. Product tests use deterministic adapters and disposable stores. No live provider/engine, broader modules, new Job or retry.

Measured new test-process total 12.544237s. Historical child subtotal about5702s plus unknowns is preserved: now about5714.54s plus those unknowns and unmeasured read/hash/materialization/documentation time. Parent about2253s remains separate; campaign provider served about7362s unchanged. No provider time added.

Candidate handoff: CANDIDATE.json enumerates all11 paths and their exact base/candidate hashes; candidate/ retains their full bytes. candidate.patch applies directly to original base; correction.patch applies only the two-path delta to retained2d313602. CHECKS.json records independent patch reconstruction into /tmp/w341357-353177-patch-check with all11 hashes equal; no fuzz. These retained artifacts suffice after a /tmp wipe. No new commit exists and the retained Git head is input provenance, not the corrected candidate identity. Acceptance is unobserved.

## Historical observation clarification

The candidate W341357-VERIFICATION.json remains byte-identical to retained input. Its top-level inside-worker lease/cessation account describes the first historical run; it is not current evidence for run352156 or this host correction. What the run352156 worker positively observed about its own expiry/cessation is unavailable to this author beyond the retained report; missing inside observations are unknown and are not reconstructed. Separately attributed external run352156 evidence reports controller completed/child0, 2689.07s elapsed, workload settled/completed, token returned/unexpired and zero renewals. This correction exercised no such runtime/token; its cessation/expiry observations concern deterministic fixture behavior only. No new live proof is claimed or required for this clarification.

## Remaining independent acceptance

Reviewer must assess this exact candidate and may use the owner-authorized focused host verification through acceptance. Parent W333486 still owns ordinary status/report integration, joined12-module gate, installed-bundle proof and final acceptance; dependency341370 is unchanged. W339626 remains separately owned by Claude; attempts.py overlap requires serial reviewed integration. All11 old roots remain preserved. Upon independent producer acceptance carry the human Git checkpoint due; proposed message: “Fix durable cessation replay attribution and preserve failure diagnostics”. No commit or checkpoint completion is claimed.
