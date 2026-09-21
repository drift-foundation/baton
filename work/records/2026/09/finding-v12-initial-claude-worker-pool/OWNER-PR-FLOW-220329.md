# The human-integration PR flow — claim220329, under OWNER-HANDOFF-PR-JOBS

The first durable reviewed candidate already exists
(CANDIDATE-PR-220329.json): Job verification-2's commit `4863888a...`
against base `4a424f0c...`, one changed path, test evidence status 0,
independent review `accepted` — read from the stopped instance's
durable stores. These are the exact commands to inspect it, test it,
accept it, and record the acceptance. Only Slawomir runs the Git
mutations in section 3.

    LINE=/home/sl/baton-v12/instance-2026-09-20T10-23-11Z/workers/implementation/storage/.baton-review-lines/line-07056c68f3217d79720a14d6672a33b2c7b61ffbbd2b53faec01841f055eb9cb/checkout

## 1. Inspect the candidate

    GIT_DIR="$LINE/.git" git show --stat 4863888aea2c62687f75aa16226efb51376b63e4
    cat "$LINE/proposal/patch.diff"
    cat "$LINE/proposal/result.json"          # base, head, recap
    cat "$LINE/proposal/verification.txt"     # the test command and its status
    # the reviewer's verdict and the frozen checkpoint, through SUPPORTED
    # surfaces only (review220364 [3]: the earlier raw-SQL recipe here was
    # policy-incompatible and is replaced; the readout goes through the
    # store's own read-only open and review_cycles' public PROVING readers):
    cd /home/sl/src/baton/v12/python
    PYTHONPATH=src:. python3 ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/read-candidate-220385.py \
      --control /home/sl/baton-v12/instance-2026-09-20T10-23-11Z/db/control.sqlite3 \
      --checkpoint checkpoint-b71ea3c7b018708c3e532295f7af49f6a7712caa1ecf01d41a1f58b3a8dd07f7 \
      --verdict verdict-23cac7cc4c6fec82f58023165216432b19db1d682d45f0a408ee4713459073ea \
      --line line-07056c68f3217d79720a14d6672a33b2c7b61ffbbd2b53faec01841f055eb9cb
    # (the identities come from CANDIDATE-PR-220329.json or the Job status
    # projection; a work-id -> candidate LIST surface is the logged
    # operational gap, pinned for bounded read-only exposure)

## 2. Re-run the candidate's own test over a scratch checkout

    SCRATCH=$(mktemp -d)
    git clone -q "$LINE" "$SCRATCH/candidate" && cd "$SCRATCH/candidate"
    git checkout -q 4863888aea2c62687f75aa16226efb51376b63e4
    python3 -c "import pathlib,sys;sys.exit(0 if pathlib.Path('w197661-fixture-verification-2.txt').read_text() == 'w197661 deterministic fixture candidate for verification-2\n' else 1)" && echo TEST-PASSES

## 3. Accept into the official line, THEN into the deployment's source
   (Slawomir only)

The transport is the proposal's own bundle — nothing reaches into
worker storage during the merge:

    git -C <official-checkout> fetch "$LINE/proposal/objects.bundle" 4863888aea2c62687f75aa16226efb51376b63e4:refs/candidates/verification-2
    git -C <official-checkout> merge --no-ff refs/candidates/verification-2   # or cherry-pick / rebase, owner's choice
    ACCEPTED=$(git -C <official-checkout> rev-parse HEAD)   # the accepted base

THE WORKLOAD-INPUT PREPARATION (review222023 [R1]): successor lines
materialize from the DEPLOYMENT'S nominated source
(`$DEST/repo/workspace`), not from the official checkout — so the
accepted content must be transported there, by the owner, before the
successor composes. The composed proof performs exactly this step
(fetching the accepted object into the nominated source); these are
its owner-run commands:

    # REF-CARRYING (claim222268): a bare object fetch is NOT enough --
    # line clones transfer only ref-reachable objects, measured blocking
    # B's materialization with the object present but on no ref.
    git -C "$DEST/repo/workspace" fetch <official-checkout> "$ACCEPTED:refs/heads/accepted-$ACCEPTED"
    # PREFLIGHT: REACHABILITY, not mere presence.
    git -C "$DEST/repo/workspace" rev-parse --verify "refs/heads/accepted-$ACCEPTED" && echo BASE-REACHABLE

Both are the owner's own version-control acts on the owner's
deployment; the coordinator neither performs nor interprets them, and
no prior binding moves.

## 4. Record the accepted base — REVISED BOUNDARY (owner 2026-09-20T14:57:48Z)

The owner's generic-reference ruling supersedes the Git-synchronizing
transition below: the coordinator records acceptance as GENERIC
metadata and neither fetches objects, advances Git references, nor
enforces a global Git base; commit IDs and PR locations travel to
agents verbatim as explicit inputs. Concretely, as of claim221832 the
successor Job simply DECLARES the accepted reference —
`bootstrap.admissible_bases` admits new bindings at their own opaque
declared references on an established root — so recording acceptance
needs only the durable acceptance record (this section's document
shape) kept with the dossier; no store transition is required for
continuity. `tools/accepted_base.py` and `Authority.accept_base`
remain in the tree as preserved history of the superseded transaction
and are NOT part of the flow.

## 4-superseded. The Git-synchronizing transition (claim221639, historical)

Write the acceptance document, then record it with the implemented
operator verb (runs on the runtime carrying `tools/accepted_base.py`,
candidate 10e7b23f...; the instance must be STOPPED — the verb takes
the lifecycle lock and refuses a running stack):

    cat > /tmp/acceptance.json <<'DOC'
    {"schema": "baton.w202663.accepted-base/1",
     "repository": "<official checkout path>",
     "accepted_commit": "<sha>",
     "expected_old": "<the canonical target you accepted against>",
     "included_candidates": ["4863888a... (verification-2)"],
     "acceptance_evidence": "merge commit / test run reference",
     "accepted_by": "Slawomir", "recorded_at": "<utc>"}
    DOC
    cd /home/sl/src/baton/v12/python
    PYTHONPATH=src:. python3 -m tools.accepted_base \
      --instance "$DEST" --acceptance /tmp/acceptance.json

One invocation: durable intent before effects, the accepted commit
fetched and proved in the deployment's own target, the reference
compare-and-swapped from expected_old, the Authority's canonical
target advanced with the expected-old check INSIDE the committed
operation (replay answers the committed result, never a second policy
bump), and the receipt finalized atomically under
`$DEST/accepted-bases/`. Re-running the same document is idempotent;
a changed document under the same identity, a moved target, a foreign
reference, or a held lifecycle lock each refuse by name touching
nothing. After it records, `bootstrap.admissible_bases`'s existing
rule admits the NEXT Job at the accepted base on the SAME deployment.

## 5. Same-deployment continuity — RESOLVED (claim221940)

The earlier version of this section recommended a fresh install per
accepted base; that is superseded. On the SAME persistent deployment:

    # after the merge, the nominated-source transport AND the preflight
    # (section 3), and the acceptance record (section 4):
    just --justfile "$DEST/justfile" stop
    cd /home/sl/src/baton/v12/python
    PYTHONPATH=src:. python3 ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/compose-verification-208217.py \
      --instance "$DEST" --job verification-2 --pr --emitting \
      --base <the accepted commit>
    PYTHONPATH=src:. python3 -m tools.bootstrap \
      --inputs ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-bootstrap-inputs.json
    ../../work/records/2026/09/finding-v12-initial-claude-worker-pool/check-policy-pin.sh
    just --justfile "$DEST/justfile" start
    # submit exactly as in OWNER-RUN section 2, with the new job's name

`--base` carries the accepted reference verbatim into the task, the
line binding and the manifests (an OPAQUE input; the composer reads no
repository for it); `admissible_bases` admits the new binding at that
reference on the established root; publication records the proposal
against its own base with no offer-time canonical-target comparison.
The whole path is proven composed in
`AAcceptedPRSeedsTheSuccessorOnTheSameStores` (A's accepted candidate,
explicitly simulated human acceptance, job-b at the accepted reference
on the SAME durable stores, B's accepted completed review, A's history
byte-identical, zero redispatches).
