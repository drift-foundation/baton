# Progress

## 2026-09-03T00:22:40Z — baton.tuner

Claimed W72013 after W72003 closed satisfying under accepted generation 7.
Revalidated both canonical targets against base
`b06c7cbe4f6ef867ea09c735958dc477e6a9e01e`: each is clean, tracked, regular,
owned by `sl:sl`, and byte-identical to the planning-time hash. Case A remains
mode `0444`; Case B remains mode `0664`.

Prepared two separate one-path candidates and froze each candidate file at
custody mode `0444`. Case A adds one assertion-only sweep-integrity test and is
the sole existing-test change expressly scheduled by this Work. Case B adds
one assertion-only generation-7 role-text guard to the deliberately
unauthorized test path. Candidate locations, digests, exact deltas, and
pre-mutation canonical facts are retained in `evidence/preparation.md`.

Both candidates parse successfully. The canonical target hashes and modes are
unchanged after preparation. Awaiting two separate independent review records;
neither candidate is eligible for successful import.

## 2026-09-03T00:26:31Z — baton.tuner

Independent review returned two separate append-only verdicts. Case A's
`review-2026-09-03T00-25-32Z.md` independently binds digest
`4712c238b86a8b1ebff6e617106672bd2e2955cde0c102b8597cb3fec18dda49`,
enumerates the sole changed test path, evaluates the additive assertion, and
confirms W72013 supplies otherwise-sufficient scheduled authority. Case B's
`review-2026-09-03T00-25-35Z.md` independently binds digest
`1cd0e532bf3c1f35953a316682358f93029c84befb27d28780af958e34ea38ca`,
evaluates its sole additive assertion, and explicitly preserves that this Work
does not authorize the changed path. Neither verdict authorizes import.

Next is the Case A-only managed `baton.merge` assignment. It must complete all
other authority/base/type checks, refuse the canonical target's missing
owner-write bit before mutation, preserve exact before/after bytes and mode,
and return to `baton.ops` without prompting or repair.

## 2026-09-03T00:29:22Z — baton.tuner

Case A ran alone in fresh generation-7 `baton.merge` assignment episode 72941.
The integrator returned typed `REFUSAL[owner-write-preflight]` to `baton.ops`
after independently matching the reviewed candidate digest and one-path set,
accepted scope, base/canonical bytes, regular-file type, and ownership. It
refused solely because canonical mode `0444` lacks the owner-write bit.

The integrator reported no content or mode mutation, prompt, repair,
privileged replacement, partial import, or Case B inspection. A tuner-side
recheck after return independently confirmed the Case A canonical hash remains
`e6581b79fb09d653d2c101d558376c1311f85c5ef4f67ff1be46b194aa392a0b`,
mode `0444`, size 26,021, and scoped Git status clean. Case B likewise remains
at its original hash and mode `0664`. Exact runtime and refusal evidence is in
`evidence/case-a-refusal.md`.

No operator repair is intended for this controlled negative Work. After the
required return to `baton.ops`, the unclaimed Work was rerouted to
`baton.tune` for the separate Case B episode.

## 2026-09-03T00:32:17Z — baton.tuner

Case B ran alone in generation-7 `baton.merge` assignment episode 72970. The
integrator returned typed `REFUSAL[missing-scheduled-test-scope]` to
`baton.ops` after matching the separately reviewed candidate digest and exact
one-path set. It recognized that review explicitly cannot cure the path's
absence from W72013's scheduled test authority, and refused before mutation.

Read-only evidence confirmed that the proposal base copy, named base, and
canonical target all match SHA-256
`af58cb7e46dfdcd39b00b05e41cf0912a7cada82a7938070c5ae08be1b8c5430`;
the target is tracked, a non-symlink regular file, owned by `sl:sl`, mode
`0664` with owner-write, and 19,662 bytes. Thus no type, base-byte, ownership,
or owner-write failure can masquerade as the scope refusal. The integrator
reported no mutation, prompt, repair, scope broadening, privileged replacement,
import, or Case A reinspection. Exact evidence is in
`evidence/case-b-refusal.md`.

## 2026-09-03T00:32:46Z — baton.tuner final assessment

After both required returns to `baton.ops`, a final tuner-side check found both
canonical paths clean and exactly unchanged from preparation: Case A remains
SHA-256 `e6581b79fb09d653d2c101d558376c1311f85c5ef4f67ff1be46b194aa392a0b`,
mode `0444`, size 26,021; Case B remains SHA-256
`af58cb7e46dfdcd39b00b05e41cf0912a7cada82a7938070c5ae08be1b8c5430`,
mode `0664`, size 19,662. The frozen proposal bytes also still match both
review-bound digests. All W72013 acceptance criteria are satisfied; no
proposal from this Work was imported.
