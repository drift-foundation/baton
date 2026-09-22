# Owner-approved Job5 integration

Owner decision: FINDING.md2026-09-21T14:03:25Z. Work W202663, configured integrator baton.merge; claim before execution. Read current PLAN/PROGRESS and review-2026-09-21T13-56-00Z.md with REVIEW-EVIDENCE-230381.json. Preserve all prior records. Independent candidate review is the hash-bound findings/report.json referenced by that review; read it before import.

Exact scope: add v12/python/tools/pool.py and v12/python/tests/tools/test_pool.py as ordinary non-executable repository files. Neither exists in reviewed base446fa8f79d9569799a77e888e8236070e1dc78f7 or in prompt's clean checkout preflight at HEAD8b4e9ecd. No existing test file is changed. Owner authorizes these test additions; standing test authority also applies. No changes to other product/test paths; no diagnostic fixes, routing behavior additions or redesign. Accept the review-disclosed pool_generation adjustment and admission-does-not-route limitation for this bounded import.

Candidate head a12759d2df0f483da075d842ef1aebad02c1e1f9; tree eacc4edcc126228df47bdd95836edee2c83b93b1; checkpoint-dfabedb13a919728cbff16e88590b37c67f42a31d5b2a0a44bd9b9238dedaec3; checkpoint digest sha256:16e5ff8488484d749d8a790831d37a919d92885dc37db7ea7451bae18eaf317c.

Proposal directory:
/home/sl/baton-v12/instance-2026-09-21T06-27-56Z/workers/implementation/storage/.baton-review-lines/line-a5e285bf0730608a224fe2ee8fbec3984b2a1f345eb9661cbee1010437c11bfa/custody/attempt-cc65c5de55575c58360e0331122cb434c011e01055969f8acbbd9143faf8dec2/proposal

Digest bindings: change.patch SHA2565ad6aa014a2d03518db35253c297344ccaeda20f98f54442a939911a296beba4; objects.bundle SHA256cc956db744755b9cd26354a0a8527a5cfd43dfe745d0b10e6a1f1dbe1555b468; result.json SHA256abc4361e45f1d6e220239208fd19e70f49aca601b8d3baaac0bea9e171bfe283.

Independent accepted review report:
/home/sl/baton-v12/instance-2026-09-21T06-27-56Z/workers/implementation/storage/attempt-64e117198e12d14a5f48d189249baeb136645997d1d3c561fa1a3837a44aab13/custody/attempt-64e117198e12d14a5f48d189249baeb136645997d1d3c561fa1a3837a44aab13/findings/report.json

Report SHA256b7b86b8b8d4b41e7fe3bc7a7f23377d7b7fdba8cf905a87e995743bdc8dfbce9. It accepts the exact head/base/two added paths, reports158 focused tests plus33 pool tests, and records the non-blocking duplicate-participant exception/exit-code issue without deployment mutation.

Perform normal whole-path-set integration preflight against the current checkout and independently reviewed artifact bytes. Both planned new paths must still be absent; refuse overlap/drift instead of fixing candidate code. Custody file modes are not checkout modes. Import content without agent Git mutation; do not fetch/stage/commit/change branches. Verify resulting bytes and ordinary file modes. Execute focused tests.tools.test_pool and tests.tools.test_bootstrap under the repository's supported local setup with a writable disk-backed fixture root outside the checkout, sensible timeout and owned cleanup. No broad suite, live provider or deployment changes. If compatibility with current bootstrap fails, preserve exact evidence and return the concrete issue; do not redesign under integration authority.

Integrator owns the exact two added paths and its attributable PROGRESS/handoff/evidence entries during claim. Prompt owns only decision/coordination notes; no parallel product edits. Return prepared diff and verification to baton.decide for Slawomir's Git ownership. Do not close Work or launch W177936 from the integration claim; name session reuse as the already-selected next development priority once integration is ready.
