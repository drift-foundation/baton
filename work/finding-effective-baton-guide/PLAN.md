# Plan — effective Baton adoption guide

1. Revalidate the README, mailbox protocol, and repository finding rules — completed.
2. Write the path-neutral effective-use guide and release announcement — completed.
3. Link both from the README and verify examples/links/whitespace — completed;
   16 focused documentation/distribution checks and `git diff --check` pass.
4. Send Slawomir a deployment-specific announcement with exact references —
   completed.
5. Route the documentation through implementer review before commit — completed;
   final approval is appended to `review-2026-08-11T04-04-55Z.md`.

Review pass `review-2026-08-11T04-04-55Z.md` approved the scope with one
required correction. The guide now states the real generation+1 `regen`
workflow and that `see` drains all unseen notices. The released protocol
wording is preserved and tracked separately in
`work/finding-config-regen-wording/`.

K's runner addendum was incorporated with one correctness edit: a detached
protocol-10 `wait` can delay consumption but cannot create or strand a claim.
The guide now records first-hand Claude monitor behavior and first-hand Codex
live-turn polling separately, while keeping both outside the protocol. Final
correction verification passed.
