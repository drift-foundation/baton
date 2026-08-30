# Compose the minimal supervised dogfood operator

Work: W39358
Parent: W38956
Dependencies: W39356 and W39357

## Purpose

Provide one documented Python entry point that composes the already accepted
Worker Manager lifecycle with the accepted Docker transport and real Claude
worker. It is a thin deployment composition, not a second manager.

## Confirmed boundary

- Require explicit source subset, frozen task, image digest, engine, manager
  state/evidence roots, workspace group, credential source and network name.
  There is no home credential, mutable image tag or open-network default.
- Stage source outside manager core with the bounded no-follow manifest path,
  compose the accepted input/assignment/launch documents and mount source
  read-only at `/input/source`.
- Compose the deployment authority-session facade: six members delegate to
  the v12 `Session`; `publish_answer` is a typed refusal because this pilot
  runs no `inquire` and invents no Baton publication.
- Drive offer, reservation, claim, activation, input, launch, runtime start,
  correlated worker-entry conversation, freeze, intake, retention, destroy,
  positive absence and credential teardown through the public operations.
- Independently derive the candidate diff and verification result; never
  stage, merge or write into the canonical checkout.
- Preserve an unresolved attempt whenever runtime absence, output custody or
  credential cleanup cannot be proved.

## Initial file ownership

This child owns a new dogfood operator module below `v12/python/tools/`, its
operator documentation and focused composition tests below
`v12/python/tests/tools/`. It consumes W39356 and W39357 as accepted
capabilities and does not edit their transport or worker files without an
explicit handoff.

## Acceptance

- One documented command is reusable for another bounded task and records
  input tree/task/image/network/assignment/runtime/output identities without
  credential or raw provider text.
- Injected unit/composition tests prove the positive order and honest
  provider/control/transport/verification failures required for this positive
  slice.
- Exact replay cannot start a second runtime or provider turn; a fresh attempt
  receives fresh roots and credentials.
- Success and post-start failure use the accepted destroy/absence/credential
  cleanup path, with uncertainty preserved rather than relabelled success.
- A real Docker dry run reaches the worker entrypoint without relying on the
  spike lifecycle. Live provider authorization remains W39364's operator gate.
