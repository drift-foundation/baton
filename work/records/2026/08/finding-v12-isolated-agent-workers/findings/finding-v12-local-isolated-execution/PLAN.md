# Plan: prove v12 local isolated execution

1. [done 2026-08-22] Bind W1425 to this canonical record and revalidate
   the assignment against the campaign decisions, W151 state machine, frozen
   M1 contracts, current `v12/` proof and available local OCI tooling.
1a. [implementation active as top-level W2845; live policy verified 2026-08-22]
   Provision and independently verify exact read-only
   managed policy rules for `docker version`, `docker info`,
   `docker inspect`, and `docker image inspect`. Keep every mutable Docker
   operation behind the future trusted Worker Manager adapter.
2. [done 2026-08-22] Pin the smallest implementation slices and their dependency order
   for the OCI reference worker, trusted Worker Manager/local runtime adapter,
   the required v12 assignment-authority substrate, and one complete local
   lifecycle proof: authority -> manager -> OCI worker/adapter -> conformance.
3. [done 2026-08-22] Define exact implementation ownership, acceptance evidence,
   positive/negative/race/restart tests and focused verification for each
   slice without pulling M3 proposal integration or M4 provider certification
   into M2.
4. [done 2026-08-22; approver message 2914] Keep M2 self-contained under
   `v12/`: its disposable v12 authority exclusively owns W151 state. Do not
   modify `src/baton_work/`, v11 behavior, or release surfaces.
5. [done 2026-08-22] Created and bound W2928 authority, W2929 manager,
   W2930 OCI worker/adapter and W2931 local proof. Established the explicit
   W2928 -> W2929 -> W2930 -> W2931 dependency chain; W1425 waits on W2931,
   and only W2928 is runnable at `baton.impl`.
6. [pending after children] Reconcile independently reviewed child results
   against the frozen M1 contract and return M2 for approval.
7. [confirmed 2026-08-23; review next] Replan the remaining M2 children for a
   Python host. Freeze the host-side Node tree as executable-reference
   evidence; revise W4 to implement the Worker Manager in Python, revise W5 to
   separate its Python OCI runtime adapter from provider-native code inside
   the worker image, and make W6 certify the portable composition. Preserve
   the dependency chain while these boundaries are reviewed; do not route new
   host-side JavaScript implementation.
8. [approved 2026-08-24; prerequisite creation active] Use one self-contained
   `v12/python/` distribution with Python `>=3.13`, its own disposable
   `.venv`, `pyproject.toml`, and a hash-locked `requirements.lock`. Add a
   separately owned Python assignment-authority prerequisite before W4. Authority
   and manager may share the distribution but never modules, SQLite stores,
   connections, schemas or transactions; W4 receives only an already-minted
   participant-bound authority session.
9. [confirmed 2026-08-24] Retain the superseded Node authority and Worker
   Manager as a frozen executable oracle throughout the Python port. Retire it
   only through an explicit post-parity step after independently reviewed
   Python coverage of every portable obligation and a production import audit;
   never delete it as incidental cleanup while the replacement is incomplete.
10. [confirmed 2026-08-24] Keep dependency distributions out of Git. The
    self-contained Python distribution owns `pyproject.toml` and the exact
    hash-locked `requirements.lock`, while each checkout creates its disposable
    venv and downloads the permitted artifacts from its configured package
    index. A wheelhouse, offline mirror or certified artifact bundle is
    operator infrastructure outside the source tree, not a repository payload.
    Enforce the generated wheelhouse boundary with the exact
    `v12/python/wheelhouse/` `.gitignore` entry.
11. [done 2026-08-28] Revalidated the umbrella after W6. W6's satisfying
    closure is a bounded, formally `not-certified` proof result and does not
    complete M2 while W16823, W32382 and W32391 remain open.
12. [coordination 2026-08-28] Block W3 explicitly on W32382 and W32391.
    W32382 already waits transitively on W16823 through W32649; W32391 is
    parked pending a real Podman engine. Re-run item 6 only after both direct
    gates close.
