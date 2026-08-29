# Build the real Claude worker adapter and image

Work: W39357  
Parent: W38956

## Purpose

Turn the provider-neutral worker into one real Claude-backed dogfood image
without importing W17110's spike protocol or direct Docker lifecycle.

## Confirmed boundary

- Inject the provider through `baton_worker.main(agent=...)`; the worker-entry
  framing and assignment contract remain the authority.
- Reuse only W17110's pinned Claude installation facts. Do not run
  `trial.mjs`, publish its result shape or make the worker own Docker.
- Read the explicit attempt-scoped `claude` credential slot at the fixed
  `/run/baton/credentials/` mount. No home-directory fallback, environment or
  argv secret, workspace copy, hashing, printing or semantic inspection.
- Copy exactly `/input/source` into bounded container-private scratch below
  `/tmp`. The canonical/source bind stays read-only; the declared proposal is
  the only host-writable output.
- Invoke Claude through a closed, golden-tested argv. Provider prose is input
  to the adapter, never worker-control framing or success identity.
- Write `proposal/{result.json,candidate,change.patch,verification.txt}` with
  cooperative group-readable modes, then let the existing worker publish the
  measured `/output/output.json` last.

## Initial file ownership

This child owns new worker-side files such as a Claude agent module, its
dogfood entrypoint/Dockerfile and focused provider-image tests. It does not own
the Python manager transport files held by W39356 or operator files held by
W39358. Any necessary edit to shared `baton_worker.py` requires an explicit
handoff first; prefer its existing injection seam.

## Acceptance

- Provider argv, prompt/document conversion, bounded response handling,
  explicit credential path, source copy and declared proposal writes have
  focused tests with no live secret.
- Missing credential, nonzero Claude exit, malformed/bounded response or no
  candidate cannot report `completed` or publish a useful proposal.
- The image is pinned/reproducible at the level already proven by W17110 and
  starts the ordinary worker-entry program with the real adapter injected.
- A no-secret image gate proves the CLI/entrypoint is present. The first live
  provider invocation waits for the operator's exact credential and network
  grants and belongs to W39364.
