# Review — participant-address identity, protocol 8

Status: **approved after re-review**

Approved source `dc24beba58ce6ae582dcae8cefbd21e2756c5d138ec81b07549f19ee822202ea`,
artifact `75a8b206e4f7a4be01260d526fa328a01fec0e2bcd6dae29b4cd2c8a3e343b4b`,
and protocol document
`c9253eddb56249549facf63317a9a7d3eb9946d0e501169f46d18812916a8a1f`.

The core implementation is coherent: protocol 8 stores claim ownership as
the recipient participant; `reply` and `close` validate that participant
before both first disposition and retry; notice receipts key on participant;
administrative operations still require their explicit capability; and the
schema, dump, CLI, and transition ledger contain no actor/seed credential.
The initial review changes recorded below were resolved and independently
verified. No open finding remains in the participant-address identity change.

## Re-review disposition

All three correction groups are complete:

- Public documentation now states one notice receipt per participant and no
  longer promises per-actor fanout. Active source/test protocol references
  were updated to protocol 8.
- Regression pins now cover foreign-participant refusal on first disposition
  and retry for both `reply` and `close`, recursively reject `actor`/`seed`
  keys in `dump`, and explicitly reject all four retired config fields with a
  protocol-specific diagnostic.
- The duplicated conditions/checks, unused identity remnants, dangling call
  syntax, and whitespace failures were removed. `git diff --check` is clean.

Focused re-review: five ownership/config/dump/doctor tests passed. Full
re-review: **318 passed, 0 failed** in 90.95 seconds, including the isolated
standalone-distribution run. Artifact/source/protocol-document hashes match
`DISTRIBUTION.json`; `bin/baton --version` reports tool 3.0.0, protocol 8.

Approval is scoped to `work/finding-seed-credential-boundary/`. The fresh
authority remains intentionally uninitialized while
`work/finding-typed-content-envelope/` is pending.

## 1. Resolved — public protocol prose contradicted participant-only delivery

The initially reviewed `README.md:195-196` promised deduplication and fanout per
`participant+actor`, including independent delivery to multiple actors of one
participant. Protocol 8 implements one receipt per participant. This is a
user-visible contract contradiction, not merely an old comment.

The same sweep needed to correct the remaining active-tree residue:

- `README.md:93` calls the consumer an actor;
- `baton_v6.py:2832` and `test_baton_v6.py:1944` say this build knows only
  protocol 7;
- `test_baton_v6.py:1` still identifies the suite as protocol 6;
- `test_baton_v6.py:3242` still labels notice delivery per actor; and
- `test_baton_v6.py:4331` says an actor is split when the test changes the
  participant.

Historical finding documents should remain historical; this request applies
to current source, tests, and public documentation.

## 2. Resolved — three claimed acceptance pins were absent or incomplete

At initial review, `IMPLEMENTATION.md` said all eight acceptance requirements
were covered by regressions, but the suite did not contain all of the claimed
checks.

1. Finding acceptance item 1 requires a foreign participant to be refused on
   both first disposition **and retry**. `test_reply_wrong_owner_refused`
   covered only the first disposition; after the owner committed, no foreign
   participant retried that known claim id. The correction added the retry
   case and covered both `reply` and `close` ownership seams.
2. Finding acceptance item 3 requires `dump` to contain no bearer credential.
   `test_dump_redacts_bodies` checked body redaction only; no test recursively
   scanned the dump's keys for `actor` or `seed`. The correction added the
   asserted pin described in the handoff.
3. Finding acceptance item 7 names `identity`, `singleton_actor`, `actor`, and
   `seed`. `test_old_identity_config_is_rejected_not_ignored` covered only the
   first two. The correction added literal `actor` and `seed` participant
   fields to the rejected cases so generic unknown-field behavior cannot
   silently regress.

The initial implementation passed an independent ad-hoc version of these
checks; the problem was that the release would not retain the required
regression tripwires.

## 3. Resolved — the mechanical sweep was not clean yet

These were small, but they were exactly the regex-removal failure mode called
out in the handoff and had to be cleaned before the distribution was rebuilt:

- `baton_v6.py:1507-1508` compares `from_participant == participant` twice in
  the same `exact_author` expression;
- `baton_v6.py:3280-3284` performs the malformed-participant test twice, which
  can emit duplicate doctor problems;
- `baton_v6.py:3615` retains the unused `singleton_ok` parameter;
- `test_baton_v6.py:18-20` retains unused `SEED_A/B/C` constants;
- several calls retain empty continuation lines or trailing commas after the
  removed arguments (`test_baton_v6.py:1934-1935`, `3908-3909`, and
  `4029-4030`; `baton_v6.py:3790`, `3822`, and `3841`); and
- `git diff --check` fails on trailing whitespace in `baton_v6.py:427` and
  `test_baton_v6.py:3899`.

Re-review required the focused acceptance tests, full suite, deterministic
build, hash checks, and `git diff --check` after this cleanup.

## Initial-review verification

- `just test`: **316 passed, 0 failed** in 90.92 seconds, including the
  isolated reusable-distribution run.
- Checked artifact/source/protocol-document hashes exactly match
  `DISTRIBUTION.json` and the handoff.
- Checked `bin/baton --version`: tool 3.0.0, protocol 8.
- Ran the documented flow against the built artifact on a fresh protocol-8
  instance: `init`, directed `send`, reviewer `wait`, reviewer `reply`,
  implementer `wait`, and `doctor`; delivery was correct and doctor returned
  `ok: true`.
- Independently inspected all dump keys, SQLite columns, and CLI option names:
  no `actor`, `seed`, `--actor`, or `--seed` remained; the claim recorded
  `team.implementer` as its participant.

No Git staging or commit operation was performed by the reviewer.
