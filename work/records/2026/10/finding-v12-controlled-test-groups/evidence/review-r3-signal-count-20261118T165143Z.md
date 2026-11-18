# W385124 independent read-only review — r3 signal count

Claim E385125; baton.codxpc, role impl. Assignment CODEXPC-R3-REVIEW-ASSIGNMENT.md / M385123. Reviewed code and existing logs only. No tests, reproductions, builds, Docker calls, source edits, Git mutations or delegation. This unique report is the only file written. Owner full run was left undisturbed.

## Verdict

**Confirmed fixture ordering assumption; no product regression established by this failure.** The equality at test_authoring_shutdown_deadline.py:204 assumes two separate SIGTERM handler callbacks have already occurred when the fixture records its post-defer event. The fixture explicitly causes only one of them and does not synchronize the other. Do not revert the accepted process-exit handler fix or change production deadlines on this evidence. Exact r3 signal delivery order, and whether any signals coalesced, remain unproved.

## Observed evidence and limits

final-suite-20261118-r3/test-all.log:4713–4725 reports absent_cleanup expected two `signal 15` entries, observed one. It is a single failing subtest observation, not a signal-sender trace. In that branch all preceding assertions completed: intended runtime scenario/injection, named manager reaping and PID absence, manager guard reacquisition, held outer/inner outcomes, final publication, runtime quiescence/exact stop, token retained rather than returned/revoked, empty enforcement faults, actionable outstanding cleanup, and final snapshot before the shutdown request deadline. The child was not killed with -9. These are stronger evidence for the required lifecycle behavior than the callback count.

The matrix normally uses a disposable disk root; BATON_SHUTDOWN_EVIDENCE is optional. The reviewed r3 wrapper does not select it. The listed r3 evidence contains the outer failure log but no retained absent_cleanup events.jsonl/request/outcome journal. I did not search or touch live fixture state. Thus I cannot attribute this particular one-entry list to a specific scheduling interleaving, or infer the full suite's final outcome from this partial log.

Reviewed the exit-race RESULT.md, parent FINDING/PLAN and review-2026-11-18T16-29-13Z.md. Those describe accepted pre/post deterministic witnesses and continued SIGKILL enforcement; I did not rerun them. Read-only comparison of c2cb08877495b3124f426dc31e6fa76e37e8e1d9 against5b9659f0 shows only three v12 paths changed: controller, next_run_flow fixture and its tests. Shutdown matrix, baseline Termination and shutdown_fixture are unchanged.

## Senders, handlers and ordering established by code

1. Dedicated manager child_main (authoring_enforcement.py:517–525) installs cooperative SIGTERM/SIGINT handlers that set guard.stopping. The checkpoint keeps them through process exit. During baseline.supervise, Termination.install (authoring_baseline.py:1057; implementation around260) temporarily replaces those handlers with Termination._handle. That handler appends the signal and raises KeyboardInterrupt only while its mode is `raise` (294–299).
2. Independent enforcement thread ticks the shared deadline and can set stopping and cancel the runtime (authoring_enforcement.py:97ff,178ff). The controller observes snapshots, polls and requests shutdown (supervise_process:329–348). Its Process.terminate calls _signal(SIGTERM), which calls os.killpg on the owned manager group (Process:385–405). Request publication precedes that send; neither is an acknowledgment that the baseline handler ran. `terminating` prevents another ordinary controller terminate in this loop. Parent final kill is SIGKILL, not another recorded `signal 15`.
3. Baseline serving can end from a signal, terminal state, refusal, failure, no-progress or its own serving bound (authoring_baseline.py:1135–1224). Ending the loop therefore does not itself prove a prior SIGTERM. Gate closure then precedes termination.defer (1232–1237), which changes mode only; it sends nothing and waits for nothing.
4. The fixture's trace return hook for defer (shutdown_fixture.py:149–153) sends **one self-directed** SIGTERM using os.kill(os.getpid(), SIGTERM), then immediately snapshots this Termination object's `received`. An earlier controller SIGTERM plus this injection ordinarily gives two; absence of an earlier handler invocation leaves only the injected one. A later controller callback cannot change the copied list already journaled. There is no barrier/ack requiring controller delivery before this snapshot. Close pending deliveries/coalescing are a separate possible explanation, not established by the log and not necessary to show the assertion's missing ordering premise.
5. Baseline finally restores the child's cooperative handler at supervise exit (1064). Only later does child_main finalize and the interpreter exit. The old checkpoint restored SIG_DFL there; c2cb0887 removes that late restoration. The failing snapshot is earlier, inside defer's return trace. No code path in that diff changes the baseline append/defer logic or explicitly orders the two senders. Load or incidental scheduling can expose the pre-existing assumption; this is an inference, not a reproduction.

RUN-5 (DESIGN.md:535) requires cooperative stopping plus host enforcement/positive cessation; it does not promise a count of SIGTERM callbacks. The outer deadline and SIGKILL backstop remain in place. A sent signal and a received callback are different observations; neither alone proves token-safe cessation.

## Smallest correction and proposed verification (not executed)

Correct fixture/assertion ownership, not production handler lifetime. Make the defer injection observable: record received state before it, record/ack the handler callback after it, and assert a deferred signal is recorded without raising and cleanup/publication continue. Use a bounded acknowledgment, not a timing sleep. Do not merely replace expected two with one or `len >= 1`: a stale earlier signal could then pass even if the deferred injection was broken. If an external callback can overlap, use an explicit fixture-owned acknowledgment or separately identifiable injected signal; do not claim raw list deltas uniquely identify a sender. Separately assert the outer shutdown request/send and existing runtime cessation/deadline outcomes, without assuming its callback precedes the defer snapshot.

Retain deterministic repeat-signal coverage at the Termination boundary: first delivered callback in raise mode records and interrupts; switch to defer; second acknowledged delivery records and returns normally; outcome persists before interruption is surfaced. A small isolated signal fixture can serialize sends using acknowledgment, or a unit test can call the real handler directly while clearly labeling handler rather than OS delivery coverage. Keep actual OS-delivery coverage in the composition matrix.

Positive scheduling cases: controller stop delivered before defer; controller stop deliberately gated until after the deferred injection journal. Both must retain the deferred injection acknowledgment, exact runtime stop, held token/outstanding cleanup, bounded final publication and manager reaping. Negative controls: suppress the deferred callback (must fail even with an earlier signal); force deferred mode to raise (must fail downstream publication/ack); omit the outer stop or runtime cessation (existing enforcement assertions must fail). Keep the accepted late-exit positive and deadline-kill negative witnesses. Do not increase deadlines or remove the independently enforced lifecycle checks to make this count pass.

If retaining an exact two-callback assertion is preferred, first make both deliveries explicit and independently acknowledged before counting them; do not wait for an assumed controller delivery inside a cleanup deadline without a fixture protocol that guarantees it. Repair and any verification require coordinator release after this report; none was performed here.

## Source identity

The following current bytes equal their c2cb08877495b3124f426dc31e6fa76e37e8e1d9 Git objects (read-only comparison):

- `v12/python/tools/authoring_enforcement.py` — `40539886d949d678e403bb6628f86e6faa60b1c921286ef44a3eef1cea4da75a`
- `v12/python/tools/authoring_baseline.py` — `8e5987f56f8d5329c33a8e73f9df56f13213e134f2dade8180afabf80723efe9`
- `v12/python/tools/authoring_shutdown.py` — `af9e5ea6b140d772cdb143c73bccf7c321869b4707245ba7e8ca79ab855fab2e`
- `v12/python/tests/manager/shutdown_fixture.py` — `392bc63a71222fcf67ef897c1fbc8c2e5cc288de2d662edc1ec9d4ac28aee010`
- `v12/python/tests/manager/test_authoring_shutdown_deadline.py` — `09eaea1fc27eb8f579325e31f4b30c13ce387e9ade63b397cde969e8d09e60f3`

Handoff: return W385124 to baton.decide for acceptance and a bounded fixture-correction allocation. Preserve the full-run result independently; this review does not close W384870 or authorize a run.
