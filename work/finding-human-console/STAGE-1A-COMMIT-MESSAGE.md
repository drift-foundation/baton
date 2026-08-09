The agent CLI adopts the shared core

`bin/baton` is built from `baton_core` now. The console already was, so there
is one implementation of the protocol behind both artifacts instead of two
copies of it.

Behaviour and protocol are unchanged. This is adoption and nothing else: no
schema move, no wire change, protocol still 9, no fresh authority and no
cutover. The artifact bytes change, which is the whole visible effect.

The oracle stays, and stays out
-------------------------------
`baton_v6.py` is byte-identical and is NOT packaged. Its remaining job is to
be the differential oracle: the reference for what the CLI did before
adoption, and the only thing that can catch a silent behaviour change
afterwards, precisely because it did not change alongside. An oracle shipped
inside the thing it measures has stopped being one.

`test_core_parity.py` drives both implementations through the same operations
and records every divergence rather than reconciling it.

Two records, and they are not the same record. OBSERVABLE PARITY is what that
harness sees: exactly two differences, both additions — a manifest `address`
on each delivered part, and `created_ts` on claimed scan rows. Anything else
differing fails as unrecorded.

The CLIENT API is a separate matter: the core adds `list_roots`,
`list_notice_activity`, `read_claimed_external_part` and two columns on
`list_messages`, and removes `list_received`, which served a view that no
longer exists. That removal is not a parity divergence — it is a method the
oracle's callers never had, because the oracle has no front end.

One door, not a wider surface
-----------------------------
`baton_core.cli` re-exports `main`. `import baton_core` still gets a library
with no `main` on it, because a library that offers a command line invites
being run as one. The bootstrap imports `baton_core.cli` rather than reaching
into `_impl`, which would have made a private module part of the distribution
contract by accident. Both halves are pinned.

Superseded contracts, each recorded where it lived
--------------------------------------------------
`test_the_frozen_cli_remains_the_released_implementation` asserted the CLI
contained `baton_v6.py` and no core. Its own docstring said "until an explicit
decision says otherwise"; the decision arrived, so it asserts the reverse now.
The load-bearing half is the oracle staying OUT of the archive.

The corpus's distribution-root check pinned the manifest against
`baton_v6.py`; it pins `baton_core/_impl.py`. The bootstrap floor check looked
for `from baton_v6`; it looks for `from baton_core`, and what it is about is
unchanged — the floor check must precede the import, or an old interpreter
dies on the import instead of printing the diagnostic its exit code promises.

Three live descriptions were asserting the opposite of the artifact and are
corrected: `baton_core/__init__.py`, the README, and the parity module. The
first of those ships INSIDE the executable, so it was wrong about the thing it
was packaged in.

Two guards got stronger, and one caught me
------------------------------------------
The isolated-checkout test copies the core package: a bare checkout that
cannot build the executable is not a reusable checkout. The extraction purity
gate covers every packaged core module, because a host needle in it now
travels exactly as far as one in the old single source file did.

That gate then refused a build asset over a word I had written in a comment —
a host project name, used in passing. Reworded rather than weakened.

Verification
------------
    full suite            1883 passed
    git diff --check      clean
    parity vs oracle      6 passed
    packaging isolation   13 passed
    two builds            89932cefdaf3c135b85bcb0d7ea616169e66b8222fe2a5c7d1479340832055a7
                          identical both times

    bin/baton      89932cef…  (was a23461ae…)
    baton_v6.py    6d9ffe8c…  unchanged, unpackaged
    source_sha256  613fa954… = sha256(baton_core/_impl.py)
    protocol       9

The corpus exercises the PACKED executable for its end-to-end flows, so those
tests now run against the core rather than the oracle.
