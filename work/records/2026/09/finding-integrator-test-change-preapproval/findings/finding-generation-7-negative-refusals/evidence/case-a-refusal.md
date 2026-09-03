# Case A managed refusal

Result: **`REFUSAL[owner-write-preflight]` before mutation**, returned to
`baton.ops` at Work event/pass sequence 72954 after integrator assignment
episode 72941.

## Runtime evidence

- Participant/role: `baton.merge` / `integ`
- Configuration generation: 7
- Runtime incarnation: `41a30788-3b21-474e-a0b1-9c3e4137bd54`
- Codex thread/session: `01a064a0-cc5f-7d50-b553-58d2a5622593`
- Context log: `/home/sl/baton-v11.14aecfb/log/context-integrator.log`
- Readiness log:
  `/home/sl/baton-v11.14aecfb/log/codex-integrator-readiness.log`
- Runtime journal: start sequence 72859; working sequence 72942; idle sequence
  72956
- Readiness delivery: `work:2b077949-W72013:72941:g7`

The context log records the fresh session as `baton.merge`, role `integ`,
configuration generation 7. The readiness log records only the Case A
assignment episode above.

## Refusal evidence

The integrator's thread message at sequence 72953 records:

- exact one-path set
  `v12/python/tests/manager/test_text_sweep.py`;
- independently reviewed candidate digest
  `4712c238b86a8b1ebff6e617106672bd2e2955cde0c102b8597cb3fec18dda49`;
- accepted W72013 scheduled-test authority;
- matching proposal base copy, named base commit, and canonical target at
  SHA-256
  `e6581b79fb09d653d2c101d558376c1311f85c5ef4f67ff1be46b194aa392a0b`;
- canonical non-symlink regular-file type and `sl:sl` ownership; and
- sole refusal cause: mode `0444` lacks owner-write.

Before/after state remained the same SHA-256, mode `0444`, and size 26,021;
scoped Git status remained clean. The integrator explicitly reported no
content or mode mutation, prompt, repair, privileged replacement, partial
import, or Case B inspection. `baton.tuner` independently repeated the scoped
hash/mode/status check after the Work returned and observed the same state.
