# Successor shared-output preparation

This is a new preparation under W370688, not a repair to the accepted W366962
packet or its installed Job. `prepare.py` consumes those historical inputs
read-only, checks the accepted bindings and policy inventory, and emits a new
two-role bootstrap document. It refuses the historical destination.

The shared declarations are proposal, findings and logs, all optional because
each role answers the other role's outputs absent. Proposal retains its original
constraints. Findings and logs each permit at most 1 MiB and 100 entries, forbid
links and allow `application/octet-stream`, the host collector's measured type.
The selector fixture's `text/plain` alone is insufficient for actual collection.
Mandatory proposal transport metadata and review findings/logs/verdict validation
remain unchanged in their owning consumers.

The task, source base, seven selected default policy artifacts and their inventory
remain byte-identical. They do not encode this output list. Both lanes receive
the same newly sealed manifest, with this successor's record binding. The
enclosing bootstrap document receives its own new byte digest. Image, adapter,
package and credential references remain inherited pins, not requalified facts.

## Reproduce the deterministic evidence

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 120 python3 work/records/2026/10/finding-v12-shared-output-template-preparation/prove.py
```

This creates and retains a unique `/tmp/w370688-proof-*` fixture. It runs the real
Claude adapter branches, the exact selected guide verification command, worker
measurement/completion, host sealing/result validation, collection comparison,
and proposal/review claim readers. Provider and Git subprocess responses are
simulated at the process seam; no Git executable, provider, engine, installation
or authority mutation runs. The fixture transport is explicitly not a Git bundle.
Consequently this proves the shared output contract, not source checkout/transport,
manager scheduling, independent review quality, deployed image equality or cleanup.
The fixture's `accepted` report is simulated evidence, not an owner/native verdict.

`candidate/COMPOSITION.json` is an illustrative composition using an explicitly
synthetic UUID and `/tmp` destination. It must not be installed. The matching
task and bootstrap documents are provided for inspection, bound by INVENTORY.

## Later selected operation

After independent review and a separate owner selection of a fresh destination
and mint, read its actual authority UUID through the supported interface. Then
compose with those explicit operands, from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 work/records/2026/10/finding-v12-shared-output-template-preparation/prepare.py --authority-uuid "$MINTED_UUID" --destination "$FRESH_DESTINATION"
```

The command prints only and does not mint, install, stage tasks or start a Job.
Its `document` is the successor phase-two input and `task_bytes` are the exact
bytes to stage at each worker's `task_document`; `document_sha256`, `task_sha256`
and `manifest_digest` bind them. Do not feed the historical composition command
to a successor installation: it still intentionally describes the old packet.
No executable install/retry/cleanup procedure is selected by this preparation.
Source drift or historical pin drift refuses instead of guessing a new base.

After independent acceptance, the human Git checkpoint remains due. Suggested
commit message: `Prepare shared-output template Job inputs`.
