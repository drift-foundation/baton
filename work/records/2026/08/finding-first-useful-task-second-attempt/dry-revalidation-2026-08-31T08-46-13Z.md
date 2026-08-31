# W51487 dry revalidation — 2026-08-31T08:46:13Z

Performed by `baton.codex` under W51487's review claim. No authority claim,
runtime, provider turn, or credential-content read occurred.

## Frozen task

The four current checkout paths still have the exact digests accepted for
W39364:

| Path | SHA-256 | Bytes |
| --- | --- | ---: |
| `v12/spike/ping-pong/preflight.py` | `1f7491ad2e0be6bb1245123263749bb2d0a9772b740ca9bad704c2e422fa167a` | 19,064 |
| `v12/spike/ping-pong/trial.py` | `6122590459714d947bdfdd1861d949ddaccc7500a09191996eb0ef15fa9b13bb` | 26,426 |
| `v12/spike/ping-pong/trial.mjs` | `ef5af45c66922bc0a9030771e55ce5b4cecfc8adbad5be00c56bc3c9feaaae34` | 12,040 |
| `v12/spike/ping-pong/test_harness.py` | `d8ec6ec17f6e3ed2ebc5e62890405e86abf34d0a55c94b3657cca85c3ecf8c8b` | 28,469 |

Copied into isolated `/tmp/w51487-dry.Gh8CDw/source`, the exact command
`python3 v12/spike/ping-pong/test_harness.py` ran 26 tests, exit 0, `OK`.
That verification copy acquired Python cache files, so it is not an execution
source. A second clean copy was made and staged separately.

The clean staging contains exactly four entries, 85,999 bytes, with tree
digest
`sha256:9e70c7337cf7150f3004dd74abf55d26e4a4fd5740dfc0a83cdc43d69df3dfd3`.

The frozen human contract remains 3,291 bytes with digest
`sha256:e4dc000285728dea68a7bbac2f90118232a50d900f3e25b3ca0ecd212710f392`
at the canonical `file:///home/sl/src/baton/work/records/2026/08/finding-v12-first-useful-dogfood-task/evidence/first-task.md`
locator.

## Whole document pair

The current operator's pure preflight accepted the frozen task and these
authorized grants: Docker network `bridge`, retention disposition `retain`,
and the existing policy/toolchain/profile/image identities.

Using fresh planned identities
`authority_uuid=4bc7c0136f5341d0a1b4d29a32dd8213`,
`work_id=4bc7c013-W51487`, generation 1,
`attempt-w51487-run1`, and `offer-w51487-run1`, the operator composed the
clean staged input and assignment manifests. The public
`check_input_pair` accepted the whole pair:

- input manifest digest:
  `sha256:04c2f97403bf87b8836c497a065ed9e9af9a032e7832ce0eef31e6a890ce5be3`;
- dry assignment manifest digest:
  `sha256:637daa32c7dfe73ee05a242f8d21c20c23756b3f79b29453fe4970c5a2a96616`.

The assignment digest is dry evidence only: the real authority supplies the
claim receipt, event sequence and activation time and therefore will produce
its own exact digest.

## Credential and live boundary

Metadata only: `/run/baton/credentials/claude` is a 509-byte regular file,
mode `0400`, owned by `sl:sl`, and `test -r` succeeds for this managed user.
No bytes were opened or recorded.

This reviewer context cannot access `/var/run/docker.sock`. The live attempt
must run in the execution-capable managed implementer context, using a fresh
clean source (never the verification copy with cache files), the exact grants
above, and retention `retain`. The retained candidate and correlated evidence
return to independent review; nothing is applied to the canonical checkout.

The temporary dry roots and `/tmp/w51487-dry-pair.py` are intentionally left
for the operator under managed-turn policy.
