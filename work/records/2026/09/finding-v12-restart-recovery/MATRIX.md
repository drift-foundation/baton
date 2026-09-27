# R3 — the selected G1 restart-cut matrix

Kept by baton.claude under W275776, corrected per review 2026-09-27T12-07-41Z: exact
file/class/test selectors instead of ellipsized names, every unproved row CLASSIFIED against a
named authority, and no claim that an unproved row is a harmless hold.

Counting rule (review 2026-09-27T12-00-40Z): only DISTINCT cases of this Work are counted.
Inherited executions of Child A methods through a shared fixture are regression evidence, not
cut coverage.

Shorthand for the three files, all run standalone:

    R = work/.../finding-v12-restart-recovery/test_restart_recovery.py
    W = work/.../finding-v12-restart-recovery/test_worker_resume.py
          :: TheWorkerResumesItsOwnLaunchWithoutDispatchingAgain
    D = work/.../finding-v12-restart-recovery/test_dispatch_cuts.py
          :: TheDispatchBoundarySurvivesARestartWithOneCommand
    P = work/.../finding-v12-restart-recovery/test_provider_effect_cut.py
          :: TheProviderEffectIsPerformedOnceAcrossARestart
    T = v12/python/tests/job_manager/test_tool.py
          :: TheRecoveryPassVisitsTheUNCERTAINTokensToo

## Proved rows

| # | Cut | Exact selector | Resume or hold | Custody / no repeated effect |
|---|---|---|---|---|
| 1 | Before launch, nothing journalled | `R::ARestartFindsTheUncertainTokenItMustReconcile::test_nothing_unresolved_before_a_launch_is_attempted` | Nothing to resume | No token, no container |
| 2 | Launch journalled, no container bound | reader `R::EveryUNSETTLEDLAUNCHCutIsVisibleAfterARestart::test_the_UNBOUND_cut_is_selected_with_nothing_to_observe_by_id`; worker `W::test_the_restarted_worker_reconciles_and_never_starts_a_second_container` and `W::test_the_resume_reaches_an_ACTIONABLE_state_rather_than_spinning` | Actionable held: stage `exceptional` | ONE container, ZERO activations |
| 3 | Container bound, activation never asked | reader `R::EveryUNSETTLEDLAUNCHCutIsVisibleAfterARestart::test_the_PRE_ADMISSION_cut_is_selected_and_named`; worker `W::test_the_BOUND_NOT_ADMITTED_cut_resumes_without_a_second_container` | Resume composes nothing further | Binding unchanged |
| 4 | Activation admitted, outcome unknown | reader `R::EveryUNSETTLEDLAUNCHCutIsVisibleAfterARestart::test_the_admitted_cut_is_still_named_as_itself`; worker `W::test_the_ADMITTED_UNSETTLED_cut_resumes_without_a_second_container` | Resume composes nothing further | Not returned, not revoked |
| 5 | Lost adapter reply, settlement ran | `R::ARestartFindsTheUncertainTokenItMustReconcile::test_a_lost_reply_leaves_the_activation_unsettled_and_findable` | Reconciliation attaches the exact container | Crossing count unchanged |
| 6 | Killed with no settlement | `R::ARestartFindsTheUncertainTokenItMustReconcile::test_a_KILLED_manager_leaves_the_same_findable_state` | Reader names the container the row does not | Resource held |
| 7 | Engine unavailable at observation | `R::ReconcilingFromThatSetAttachesWithoutASecondCrossing::test_an_unreachable_engine_keeps_the_hold_and_names_the_execution`; `T::test_an_unreachable_engine_holds_and_says_so_per_attempt` | Actionable hold with exact references | Nothing attached or released |
| 8 | Engine recovers after an outage | `T::test_a_LATER_TICK_RETRIES_after_the_engine_comes_back` | Retry on the next pass | No duplicate dispatch |
| 9 | Engine names a DIFFERENT runtime than the attempt recorded | `W::test_conflicting_engine_EVIDENCE_is_refused_before_use_not_substituted` | **Refused before use**: axis `cancel-requested`, recorded runtime unchanged, stage `exceptional` | No container, no activation; binding intact. **This row replaces an earlier false claim** that this scenario reports a contradiction -- it does not, because the worker refuses instead of adopting, and the same case now asserts the pass reports no contradiction here |
| 10 | Attempt row genuinely names another runtime | `T::test_a_contradiction_between_the_attachment_and_the_binding_is_reported` | Reported and held | Binding never rewritten |
| 11 | Labelled container adopted when NO runtime is recorded | `R::TheEVIDENCEARestartActsOnIsExactOrItHolds::test_a_DIFFERENT_container_under_these_labels_is_a_contradiction_to_hold` | Observation only; this Work takes no position on whether adoption is right | Binding not rewritten; resource held. Narrowed by row 9: with a recorded runtime the production path refuses |
| 12 | Historical attempt over the same resource | `T::test_a_HISTORICAL_row_over_the_same_resource_attributes_nothing`; `T::test_a_GENUINE_owner_mismatch_is_still_reported` | Attribution correlated to the token's owner | One report per domain |
| 13 | Renewed deadline read after a restart | `R::TheEVIDENCEARestartActsOnIsExactOrItHolds::test_a_RENEWED_deadline_is_what_a_restart_reads` | Judged against the renewed deadline | Child B's arbitration, fresh handle |
| 14 | Expiry of an unsettled launch | `R::TheEVIDENCEARestartActsOnIsExactOrItHolds::test_an_expired_unsettled_launch_is_reported_as_expired_and_still_held`; `W::test_at_expiry_the_reclaim_REVOKES_and_the_unconfirmed_stop_stays_held` | Revoked, stop attempted, unconfirmed -> `held`/`uncertain` | NOT returned; still outstanding |
| 15 | Conflicting acquisition while unresolved | `R::ReconcilingFromThatSetAttachesWithoutASecondCrossing::test_the_hold_still_excludes_a_conflicting_acquisition` (class corrected per review 2026-09-27T12-13-56Z); `R::EveryUNSETTLEDLAUNCHCutIsVisibleAfterARestart::test_no_cut_releases_the_resource_or_permits_a_replacement` | Refused | TOK-10 "before admitting conflicts" |
| 16 | **Before dispatch**: runtime live, no command written | `D::test_a_restart_BEFORE_dispatch_publishes_exactly_one_command` | Safe resume: the resumed manager publishes EXACTLY ONE command | One container, one activation; resource held |
| 17 | **After dispatch with the reply lost** (PUBLICATION boundary only) | `D::test_a_restart_AFTER_dispatch_does_not_ASK_AGAIN_at_all` | Safe resume: the resumed manager does not reach the publisher at all -- the durable command and the canonical state already say dispatched; stage `waiting` | ZERO further publications, one container, one activation; the written command's digest re-read from its own file. **Scope of this row, per review 2026-09-27T12-20-22Z:** it proves the command INTENT is not rewritten or re-published; it says nothing by itself about a consumer repeating one published intent -- that is rows 18 and 19 |
| 18 | **Provider effect performed, receipt written, manager interrupted before observing it** | `P::test_ONE_effect_in_total_and_the_resume_never_invites_another` | Safe resume: ONE effect in total, and the resume invites nothing further | The effect recorder is wired to the PRODUCTION invitation (`exchange.publish_command`) and stays wired across the reopen, so the count is the product's rather than the fixture's: one invitation, one publication, one effect, one activation. **Corrected per review 2026-09-27T12-28-08Z**, which rejected an earlier version that called the consumer by hand on both sides and asserted TWO effects -- that proved the fixture could repeat, not that the resume refrains |
| 18b | Control: can the recorder detect a repeat at all? | `P::test_the_recorder_DOES_catch_a_duplicate_control_case` | Not an acceptance case | A deliberate second consume reaches two, so row 18's result of one is a measurement rather than a silence |
| 19 | **Receipt with no terminal: the provider outcome is unknown** | `P::test_a_receipt_with_no_terminal_is_WORKING_held_and_asks_nothing_further` | **Actionable unknown hold**: the observation answers `working` -- the module's own word for "the provider may still be running", deliberately not rounded to lost | Exact stage `running` (measured), and nothing further asked: one effect, one invitation, one publication, one activation, all counted by instruments attached throughout; resource held |

## Rows with no restart proof here, CLASSIFIED

The dispatch row that stood here is now PROVED as rows 16 and 17 above, under the review's
authorisation of 2026-09-27T12-13-56Z; what remains below is what this Work still does not
prove.

No row below is asserted to be safe. Each says what is and is not established, and names the
authority for its classification.

| Cut | Classification and authority | What exists / what is missing | Next bounded step |
|---|---|---|---|
| During freeze; during retention; after verdict | **Not established as this child's obligation.** Owner brief 275776 selects token/launch recovery; these are the review-cycle and intake acts, whose own Works proved them (`review_driver`, `intake`) | Accepted acts exist; no restart cut here, and this Work has made no observation about them | If a restart obligation for them is intended, it needs naming by the owner or reviewer before being added; otherwise separately owned |
| During handoff; during cleanup | **Not established as this child's obligation**, same authority as the row above; Child A proved the endings and the adoption release | Accepted acts exist; no restart cut here | Same |
| Terminal-after-restart accounting (a worker terminal written while the manager was gone) | **NOT a selected obligation.** Review 2026-09-27T12-28-08Z is explicit: "Do NOT add the newly proposed terminal-while-manager-gone scenario as another acceptance gate"; the already-selected unknown-hold alternative (row 19) suffices | Row 19 proves the unknown hold; no terminal-across-restart observation exists here | Nothing selected. Recorded so the boundary is visible, not as work |
| Discharge of a hold whose cessation cannot be established | **Limitation of the selected scope, not an assigned Work.** Row 14 shows the supported outcome IS an actionable hold; prior reviews expressly RETAINED unknown-cessation holds | Row 14 proves revoke + attempted stop + held/uncertain. A positive discharge would need cessation evidence naming the BOUND container, which the `launched-unbound` cut never produces | Recorded as an OPEN PROPOSAL only. No hold-clearing implementation is a release gate; if positive evidence later shows a trapped resource, report that exact case under coordination 285076 |
| Clearing a timing-ambiguity hold | **Limitation inherited from Child B**, recorded there when the hold was built; no prior review selected a clearing API | Child B's hold is proved and accepted; nothing clears it | Same: OPEN PROPOSAL with provenance, not a selected gate |

## Distinct case counts for this Work

    R  16 distinct cases   (Child A's inherited methods excluded)
    W   7 distinct cases, 8 EXECUTIONS -- the eighth is the old-name alias of the repaired
                          mismatch method, kept so an immutable artifact still runs it, and
                          counted as an execution rather than a case per review 12-13-56Z
    D   2 distinct cases   (the dispatch boundary: the publication cuts)
    P   3 distinct cases   (the provider effect, its receipt, and the duplicate control)
    T   9 distinct cases   (the production recovery pass)
