# Stage 1A approval

Approved for commit.

The released `bin/baton` now consumes `baton_core` without changing protocol
9 behavior. The frozen `baton_v6.py` oracle remains byte-identical and is not
packaged. The live documentation now matches that boundary. Observable parity
and client-API evolution are recorded separately: the harness permits exactly
the two named additive row/envelope differences, while the package
documentation separately names its front-end API additions and the removal of
the obsolete `list_received` view. The final artifact pin is consistent across
`PLAN.md`, `DISTRIBUTION.json`, and the checked-in executable.

Reviewer verification:

- core parity and packaging isolation: 19 passed;
- packed version: `baton 5.1.0 (protocol 9)`;
- archive members are exactly `__main__.py` and the three core modules plus
  `baton_core/cli.py`;
- `bin/baton` SHA-256 is
  `89932cefdaf3c135b85bcb0d7ea616169e66b8222fe2a5c7d1479340832055a7`;
- `baton_v6.py` SHA-256 remains
  `6d9ffe8c8021bc692b3b474a8dc18cb468c5ce3b7a67d16e3cb838124e0f2671`;
- `git diff --check` is clean.

No blocker remains for Stage 1A. Stage 1B remains a separate protocol-9
change and must receive its own review.

This supersedes the earlier approval body that named `f309d6d3…`; that hash
preceded the final packaged documentation correction and is not the approved
artifact.
