# Run7 runtime inspection

Observed at `2026-08-31T18:45:42Z` with read-only `docker inspect` against the
exact runtime named by run7's durable lifecycle record.

- runtime:
  `afed4c76aebe339911ab353021227f94cb8c635e9b46ed1e4ba2f642f4d7d334`
- label `baton.v12.runtime_attempt_id`: `attempt-w51487-run7`
- label `baton.v12.work_id`: `2bdb4a5d-W51487`
- label `baton.v12.participant`: `baton.claude`
- state: `exited`, not absent
- running: false
- PID: 0
- exit code: 137
- started: `2026-08-31T17:56:09.458431372Z`
- finished: `2026-08-31T18:29:01.079874978Z`

The operator stopped the process domain but did not perform the manager's
force-remove-and-observe-absence ending. No removal was attempted during this
review.

Credential metadata only: the granted volatile root is absent and its
`credentials` parent is empty. The assignment-home lifecycle record remains
and says `live`. No credential file was opened, copied, hashed or published.

The inventory and recovery-gap JSON files were produced against the offline
copy `/tmp/w55758-run7-copy.UdSqdZ` using the adjacent scripts. The original
v12 authority and control stores were not opened by those scripts.
