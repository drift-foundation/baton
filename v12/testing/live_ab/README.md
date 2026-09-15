# Fresh live-provider A/B confirmation

From `v12/python`, the operator runs:

```sh
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 ../testing/live_ab/scenario.py
```

This command executes a **live Claude-provider run**. It creates a unique
`~/.local/state/baton/v12/live-ab-*` root, checks disk-backed storage, verifies
prepared source hashes and the existing pinned provider/integration images,
prepares disposable source/target repositories and their initial ownership,
provisions fresh owners, submits once, and serves the normal stage factory.
No image is rebuilt. `--root /absolute/new/path` selects an explicit fresh root;
existing roots refuse. The operator needs Docker access, supplementary gid1001
and the established initial-target `sudo chown` permission.

The package reuses the validated synthetic scenario's control flow, final
committed view and early failure observation, with live-only provider inputs:
the unchanged live images in `live-images.json`, bridge networking, and the
existing registry `/home/sl/.baton/credential-sources.json`, selecting
`operator-file` / `w64268-run1` for the `claude` slot. Registry and credential
payloads are read only by the normal execution owner when delivering attempts.
The package creates no substitute credentials and includes no synthetic provider
executable or response/effect fixture. Task IDs use the fresh incarnation for
correct attribution of published provider diagnostics.

All original and derived judgments must come from actual fresh live provider
turns under their distinct role principals. Normal worker/container framing,
private lines, tests, custody, policy, receipts, causal checks, merges, leases,
both-terminal observation and final committed-output verification remain.
The whole-run1200s, implementation240s, review/judge180s and integration120s
limits remain; integration excludes only the already-defined bound judge claim
intervals. Resource limits and first-failure containment remain unchanged.
There is no automatic retry, repair, deadline increase or manual transition.

The result is retained under the printed root: `scenario-result.json`,
`evidence/run-result.json`, `evidence/terminal-status.json`, `evidence/samples.jsonl`,
`evidence/final-view.json` and the three final test logs. `final-view/` is the
clean output at the exact Authority canonical commit/tree; the original target
checkout/index remain diagnostic evidence of reference-only integration.
Both behavior scripts and the full test suite run against the committed view.
Preparation/start failures are read from public owners immediately, even when
no container or exchange exists.

`provenance.json` records the copied, validated helper sources. `input-bindings.json`
binds the current executable inputs mechanically; it is not an independent-review
or acceptance marker. A changed input refuses before setup proceeds and must be
reconciled through the owning Work. Historical live and synthetic roots remain
untouched. The preparation handoff does not itself execute this command or claim
live-provider success.
