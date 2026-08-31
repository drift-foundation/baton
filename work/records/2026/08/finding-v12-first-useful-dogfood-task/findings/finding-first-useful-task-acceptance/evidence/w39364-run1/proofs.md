# W39364 run 1 — the proofs, measured after the attempt

Attempt `attempt-w39364-run2`, runtime
`76776832e5a5b0f4dc30555c1dbde230b7105a323225355ca7a48060726eb494`.
(The `run2` suffix is the second INVOCATION; only one supervised attempt ever
reached a container. See PROGRESS.md for the first invocation, which the
manager refused before any runtime start.)

## Runtime absence

    $ docker inspect 76776832e5a5b0f4dc30555c1dbde230b7105a323225355ca7a48060726eb494
    -> absent: the daemon does not have it
    $ docker ps --all --format '{{.Names}}' | grep -c w39364
    -> 0

The manager's own observation agrees and is the one the evidence records:
`observed_after.state = "absent"`, "the engine answered that this exact
identity does not exist", and `cleanup = {cleanup: complete, state: absent}`.

## Credential teardown

    $ find <storage>/attempt-w39364-run2/credentials \
           <storage>/attempt-w39364-run2/credential-state \
           <run>/credential-home -mindepth 1
    -> <run>/credential-home/credentials   (an empty directory, nothing else)

No credential material survives the attempt. The authorized source at
`/run/baton/credentials/claude` is untouched -- the operator reads it once
into memory and never writes it back -- and its bytes appear in no file in
this record.

## Execution roots discarded, custody retained

    $ ls <storage>/attempt-w39364-run2/
    credential-state  credentials  custody

`inputs` and `workspace` are gone. What remains under `custody` is
`sealed.json` alone -- see the REJECT record for why that is a finding rather
than the expected state.

## The delivered source subset was not modified

The four staged files, hashed after the run, are byte-identical to what was
staged; the worker held `/input` read-only.

    1f7491ad2e0be6bb1245123263749bb2d0a9772b740ca9bad704c2e422fa167a  preflight.py
    6122590459714d947bdfdd1861d949ddaccc7500a09191996eb0ef15fa9b13bb  trial.py
    ef5af45c66922bc0a9030771e55ce5b4cecfc8adbad5be00c56bc3c9feaaae34  trial.mjs
    d8ec6ec17f6e3ed2ebc5e62890405e86abf34d0a55c94b3657cca85c3ecf8c8b  test_harness.py

## The canonical checkout was not modified

    $ sha256sum -c <baseline taken before the run>
    v12/spike/ping-pong/preflight.py: OK
    v12/spike/ping-pong/trial.py: OK
    v12/spike/ping-pong/trial.mjs: OK
    v12/spike/ping-pong/test_harness.py: OK

A porcelain status of `v12/spike/ping-pong/` reports no modification.

The worker's candidate is external output. Nothing in this attempt wrote to
the repository the source was staged from, and the run's own roots were all
under `/tmp/w39364/`.

## The Baton authority was not touched by the run

The attempt's authority is its OWN v12 store at `<run>/authority.sqlite3`,
created for this attempt. The v11 coordination authority this deployment
reports to is a different system and saw only the ordinary claim, message and
pass this Work performed through the CLI.
