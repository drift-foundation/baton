# B1 continuation — claim291959

Authority: owner291841 four-path selection and reviewer handoff291955;
review-2026-09-28T03-53-13Z.md. Events read through291959; thread257627.

Observed before correction: baseline serving uses total_seconds then gives a
separate cleanup_seconds window. This contradicts the selected fresh packet's
300-second total with a 60-second reserve. Within the selected baseline limit
scope, fresh mode will stop ordinary serving at total minus reserve and cap
cleanup sweeping at the earlier of its window or the overall deadline.
Historical contextual mode remains unchanged. This is a cooperative supervisor
bound, not proof that arbitrary blocking operations finish within wall time.
A deterministic pre-admission deadline check will exercise real submission and
supervisor accounting, substituting serving ticks; it cannot qualify active
runtime cancellation or G2 endings.

Generated-start negative checks now reach held_packet via emitted argv and
refuse changed fixture/manager bytes before Job/control store opens or engine
inspection, preserving changed bytes. They call main, not an OS subprocess.

## Retained result and exact continuation

Fresh serving now reserves cleanup within total; cleanup sweep deadline is also
capped by overall total. No contextual limit changes. Tests added only in
single-implementation-proof/test_baseline_bindings.py: changed fixture/source
refusal and pre-admission deadline. The deadline test uses real public submission,
real stores and accounting, with injected serving ticks; no runtime is admitted.
Assertions inside the injected serve are checked via serving_failure as well.
No new active-runtime cancellation/cleanup acceptance is claimed.

B1-FOCUSED-291959.sh: 32 PASS in0.405s. Earlier iterations:31 tests0.358s
(29pass, two message-expectation failures),31PASS0.354s,32tests0.404s
(one zero-counter expectation failure). Current author total1.521s; previous
claim291848 author2.593s; cumulative author4.114s plus reviewer0.643s.
git diff --check passed. No live engine/provider/build or deployed operations.

Current G2 detail snapshot291984: W285465 actively held by baton.claude,
claim291981; no reviewed correction consumed. The retained connected-positive
failure from previous claim remains unresolved; no redundant run this episode.
No fifth shared path changed. B1-CANDIDATE-291959.json supersedes the previous
partial candidate hashes for review, not historical evidence or acceptance.

Next: independent review of these additions, then consume the reviewed G2 fix
for T285465/291949. Re-run retained fresh positive; prove literal generated
start/status, active-runtime interruption/deadline and inaccessible-output
preservation on normal fake seams. The new negative tests invoke main with
emitted argv, not the OS entrypoint/environment. Bound-source fixture is a
small synthetic package, not the eventual frozen full runtime. Final B1 and
B2–B5 acceptance, candidate/image/profile/input freeze and provider graph
selection remain pending. No renewed owner permission for four-path continuation.
Reviewer retains PLAN/FINDING ownership; incorporate the deadline clarification
above into current decision/checkpoint without rewriting historical records.
