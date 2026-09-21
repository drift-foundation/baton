# Unblocking B — the owner's selection (claim225345, per review225331)

B (verification-2) sits RESERVED on instance-2026-09-20T15-53-26Z; its
existing line checkout cannot receive the accepted commit because the
installed runtime's materialization refreshes only the dedicated-target
supplement, never the nominated source (limitation recorded in
FINDING). Two paths; the choice is yours.

## (a) IMMEDIATE — current installed runtime, no product change

Make the accepted commit ref-reachable in the DEDICATED TARGET, which
the EXISTING supplement already fetches from, then start; B's reserved
attempt retries on ordinary ticks:

    DEST=/home/sl/baton-v12/instance-2026-09-20T15-53-26Z
    git --git-dir "$DEST/repo/target.git" fetch /home/sl/src/baton 2fb0612ca1bd9fd8e2e254a11ff26b6b64a1eba8:refs/heads/accepted-2fb0612c
    git --git-dir "$DEST/repo/target.git" rev-parse --verify refs/heads/accepted-2fb0612c && echo TARGET-REACHABLE
    just --justfile "$DEST/justfile" start

Your acts on your deployment repository; nothing in the coordinator
interprets them; no manual clone repair, no resubmit, no rerun. On
your signal after start, I poll B to completion and run the
candidate/evidence extraction plus the A-history and log comparisons.

## (b) FORWARD — the corrected candidate

Candidate 225345 (executable 151060fb..., bundle bb410f6c...) carries
the same-line source-refresh recovery, deterministically proven
(`AnExistingCheckoutRecoversWhenTheSourceGainsTheBase`): a failed
materialization recovers on the SAME line once the source gains the
ref-reachable base, supplement fallback unchanged. Installing it means
a fresh instance and re-running A→acceptance→B there, which conflicts
with your no-reinstall selection for THIS experiment — it is the right
runtime for every LATER deployment either way.
