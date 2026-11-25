# I2 independent source preflight

Claim E386165; base 2d9a1f5afd84bfdcef461798d2418be3e6d65a9d.
Both checkpoint gates satisfied. M386161 I1 source review consumed. Ownership
confirmation requested from K in M386162/M386166 and poke386163; implementation
edits have not begun. This checkpoint is not a preparation-only handoff.

Paired boundaries to implement after ownership confirmation:

- provider_policy REALIZATIONS/MANAGED: Codex 0.169.0 exec flags from inventory,
  HOME /run/baton/provider-home, CODEX_HOME HOME/codex, auth codex/auth.json,
  instructions instructions/WORKER.md. Closed Codex-only environment; retain
  fresh implementation role, R1, configured-model labeling, Claude requirements.
- tools.user_credentials currently decodes/strips source text; credentials
  materialize/adopt use MAX_BEARER=4096. Introduce explicitly selected byte-file
  handling with 1048576 inclusive byte limit, preserving legacy token API/limits.
  Preserve live-secret checks for byte files; do not bypass safety with decoding.
  Pair single_worker seeded path and OCI adoption with trusted file selection.
- provider_policy.home: bound first copy and retained-file stat validation,
  zero length refusal, exact bytes and no source read after initialization.
  tools.qualification_credentials must share the same bound and empty refusal.
- provider_home: new first-initialization receipts need an unchanged-home
  baseline and immutable identity. Explicit locked recovery must preserve the
  failed receipt/audit, prove no success and unchanged home, and use host-owned
  runtime cessation/fencing. Legacy incomplete receipts without proof stay held.
  Withdrawal alone must not authorize retry; later initialization needs explicit
  authorization and a new receipt. No automatic deletion/reset/reseed.
- C5: contain image-evidence recording failures so lifecycle observation can
  proceed without false acceptance. C8: normalize engine-field bare SHA256 IDs.
  C6 resolution ordering and C7 changed StartedAt require explicit dispositions
  preserving immutable frozen outcomes and actual execution identity; no silent
  evidence upgrade or assumption that same-container restart is authorized.

Required synthetic acceptance: D2 below/at/above + multibyte + exact bytes and
secret-free refusals at delivery, seed, retained validation and qualification;
legacy token unchanged; D1 allowed/refused/idempotent/concurrent withdrawal and
new authorized receipt; refreshed credentials survive absent source, initialized
missing refuses; paired production Codex implementation/Claude review simulation.
Use prepared interpreter, focused manager-pure/tools-pure/job_manager, external
Git-isolated fixture roots. No build, engine, real credential or provider call.
