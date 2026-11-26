# MANUAL implementation

Implement the accepted M386287 proposal on 67fd60f8. Acceptance is the complete walkthrough and deterministic verification matrix in ../finding-v12-shared-work-liveness/evidence/manual-mode-proposal/PROPOSAL.md, including idle/overlap restart, capacity waits and no duplicate starts. Independent review follows implementation and accounted focused checks.

Owned product boundaries are MANUAL Job Store decisions and clock, selection-to-research execution and custody, and installed commands/status. Affected logical test groups are job_manager, manager-pure, tools-pure. Exercise the real scheduler, worker exchange, provider adapter and output custody with a deterministic provider process and simulated engine. Source-scoped research uses the configured Claude research capability. Existing AUTO Jobs and previous status generations remain readable. Confirm generated Work replay and optional authorized Work binding on the installed operator path. Return the sealed, verified candidate and check the claim has been released.

Implementation and focused checks are complete. Independent review now owns the next milestone. Review [the exact candidate and acceptance evidence](evidence/candidate-386296/REPORT.md) alongside the owner ruling in FINDING and the proposal. After independent acceptance, Slawomir owns the Git checkpoint. Suggested commit message: “Support owner-paced MANUAL research Jobs with restart-safe budgets and explicit closure.”

M386315 U1 settled: test delayed manager recovery and owner-held results against the recorded result time, including another outstanding selection. Preserve the separate owner-disposition requirement in R1.

M386315 U2 settled: verify a closed Job with mixed phase outcomes shows CLOSED plus accurate outcome counts, remains inspectable and leaves the open to-do list.

M386315 R1 owner disposition settled. Provide an owner finish action addressed by visible Job and phase names; record chosen outcome and deciding principal, preserve the held evidence, and freeze the result. Exercise success, failure, conflicting second decisions and safe replay of a committed decision, plus close after all selections settle. Combine with U1/U2 in one correction.

E386317 correction to the reviewed 51705e1a candidate. Apply R1, U1 and U2 together under the updated SCH-2m. Verify authenticated held-phase resolution and retries, attributable preserved evidence, restart at a delayed observation with overlapping frozen intervals, and closed counts in all views. Return one delta to K.

Current milestone: K independently reviews the [combined correction and focused evidence](evidence/correction-386317/REPORT.md) against M386315 and the dated owner rulings. Delta ae409cfa on the M386309 candidate. After acceptance the pending human checkpoint is “Support owner-paced MANUAL research Jobs with authenticated held-phase decisions and restart-safe budgets.”

M386325 U3 resolved at the requirement level: require personal confirmation before attributing a finish-phase decision to Slawomir. Confirmation mechanism remains open; R2 worker-release correction is independently actionable.

M386325 R2: prove that after owner disposition and confirmed cessation, a later explicitly selected phase launches on the same single worker, including after manager restart, without losing the original evidence.

Exercise owner disposition from a new operator session after manager restart and an idle interval. The pending item must still identify the same frozen result; retries preserve the one final decision.

Specify and test the owner-decision operation at the API boundary; demonstrate it through the existing CLI. Future TUI and web clients can use that operation. Keep personal authentication distinct from client choice.

E386327, latest selection. Implement and exercise the local-owner decision API behind finish-phase, including discovery and inspection from another session, exact frozen-result reference, truthful authentication basis, replay and conflict refusal. No signing key or additional frontend. Deliver with R2 release and restart verification.

U3 resolved by the owner: retain the existing trusted operator boundary and explicit finish-phase API. Personal signing, proof of presence and new audit logging are outside this change. Preserve existing decision persistence and retry semantics. The outstanding implementation correction is R2, automatic safe release and reuse of the worker after owner disposition.

Final owner scope in E386327 supersedes the prior U3 implementation entry: preserve M386318’s existing trusted-owner implementation byte-for-byte. Deliver R2 worker reuse only with its restart and evidence tests.

Current milestone: K reviews the [R2-only release delta](evidence/correction-386327/REPORT.md) against M386325, with source tree 1983d1dacec7e227a25e4c6cefc3049557fd7f5d. After independent acceptance the human checkpoint remains pending. Suggested commit message: “Support owner-paced MANUAL research Jobs and release settled workers after verified cessation.”

## Verified owner checkpoint

Commit 76b2f2b2359a1211139625f8f5062d980c5f68bf on 67fd60f8afee40b6b4e58ea25e909e682879f72d has the exact tree reconstructed from the three M386334-reviewed patches (41 changed paths). Source checkpoint complete; runtime verification to date is simulated.
