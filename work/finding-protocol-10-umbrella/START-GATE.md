# Protocol 10 start gate

Protocol-10 implementation begins immediately after the current Stage 1B
multipart CLI work is reviewed and committed by Slawomir.

The remaining Stage 1B gate is deliberately narrow:

1. correct the confirmed `reply --attach` silent data loss;
2. add the missing packaged invalid-reference regressions for `reply` and
   `close`;
3. apply the root-qualified `ROOT_ID:REL/PATH` references ruling;
4. focused reviewer verification, then one full suite;
5. Slawomir commits the clean candidate.

No unrelated polish is added to this gate. If that correction round is clean,
protocol-10 work starts in the same work session after the commit.

**Commit preference (Slawomir):** prefer a passing full suite for the Stage 1B
commit, but a clearly identified WIP commit is acceptable if necessary to
establish the phase boundary. In either case, commit Stage 1B before beginning
protocol-10 implementation.
