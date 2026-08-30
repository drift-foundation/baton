# Harden the v12 supervised dogfood path

Work: W39366
Discovery: split from W38956 after its thin vertical slice was decomposed.

## Purpose

Preserve broader resilience, retry, cleanup and defensive work without making
the first honest useful result wait for production maturity. This is a
top-level Work rather than a W38956 child because open containment would make
it gate the roll-up even without a dependency edge.

## Confirmed scheduling

W39366 is low priority and parked. It has no dependency or containment edge
into W38956. Resume it after the positive supervised path is accepted, or
earlier only when evidence identifies a defect that can make that path falsely
succeed; that defect is then promoted to the critical owning checkpoint rather
than hiding behind the word hardening.

## Scope

- Broader provider, control-channel and Docker transport negative matrices.
- Replay across interruption/restart, duplicate dispatch prevention and
  multi-attempt isolation beyond the minimum positive-slice proof.
- Exhaustive cleanup/custody outcomes and hostile output modes, coordinated
  with W36540 rather than duplicating it.
- Local OCI negative/race endings coordinated with W32382.
- Ownership and completion of the three W38956 boundary-inventory entries
  after the shared registry edit lands.
- A narrower provider-only egress allowlist/proxy posture and operational
  credential rotation beyond the first explicit bounded network grant.
- Diagnostic truncation, surplus-output and adversarial framing cases that do
  not invalidate the already accepted positive contract.

## Acceptance

A later capability pass names a bounded subset, revalidates overlap with
W32382/W36540, implements it under an explicit claim and proves it without
weakening the accepted supervised dogfood path.
