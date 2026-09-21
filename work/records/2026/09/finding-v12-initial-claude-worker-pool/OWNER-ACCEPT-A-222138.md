# Accepting installed PR candidate A (verification-1) — Slawomir only

    LINE=/home/sl/baton-v12/instance-2026-09-20T15-53-26Z/workers/implementation/storage/.baton-review-lines/line-37baa08d6f19fdeafe4d84157617eacff07325d91ada504b00a89b40653bb7a4/checkout
    DEST=/home/sl/baton-v12/instance-2026-09-20T15-53-26Z

## Inspect and test

    GIT_DIR="$LINE/.git" git show --stat 2fb0612ca1bd9fd8e2e254a11ff26b6b64a1eba8
    cat "$LINE/proposal/patch.diff" "$LINE/proposal/result.json" "$LINE/proposal/verification.txt"

## Accept (your merge), transport to the deployment source, preflight

    git -C <official-checkout> fetch "$LINE/proposal/objects.bundle" 2fb0612ca1bd9fd8e2e254a11ff26b6b64a1eba8:refs/candidates/verification-1
    git -C <official-checkout> merge --no-ff refs/candidates/verification-1
    ACCEPTED=$(git -C <official-checkout> rev-parse HEAD)
    # REF-CARRYING, claim222268: a bare object fetch leaves the commit
    # UNREACHABLE, and line clones transfer only ref-reachable objects --
    # measured blocking B's materialization with the object present but
    # on no ref. The fetch must land a ref; the preflight tests
    # REACHABILITY, not mere presence.
    git -C "$DEST/repo/workspace" fetch <official-checkout> "$ACCEPTED:refs/heads/accepted-$ACCEPTED"
    git -C "$DEST/repo/workspace" rev-parse --verify "refs/heads/accepted-$ACCEPTED" && echo BASE-REACHABLE

## Record the acceptance (durable, beside the dossier)

Write `ACCEPTED-BASE-<utc>.json` per OWNER-PR-FLOW section 4's document
shape, with `accepted_commit` = the `$ACCEPTED` value and
`included_candidates` = ["2fb0612c... (verification-1)"].

Then B continues on THIS deployment per review-2026-09-20T15-44-09Z.md:
compose `--job verification-2 --pr --emitting --base "$ACCEPTED"`,
apply, pin gate, start, submit — I run those on your go signal.
