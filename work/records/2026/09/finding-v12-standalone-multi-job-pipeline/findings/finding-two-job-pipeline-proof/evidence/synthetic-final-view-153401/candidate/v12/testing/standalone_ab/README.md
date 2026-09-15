# Deterministic standalone A/B coordination test

Run from `v12/python`:

```sh
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 ../testing/standalone_ab/scenario.py
```

The command builds two local images from the fixed, already installed base,
creates a unique retained `~/.local/state/baton/v12/synthetic-ab-*` root, prepares disposable
Git repositories, provisions fresh public owners, submits once and serves the
ordinary `tools.stage_execution:factory`. It invokes `sudo chown` only for the
new target's initial uid65532/gid1001 ownership. Run as the normal operator with
Docker access, supplementary gid1001 and permission for that initial ownership
step. The root must pass the public disk-backed filesystem check before image
or repository preparation begins; an explicit tmpfs root refuses immediately
and records the setup failure. The existing resource thresholds and 1200/240/180/120-second limits apply.
`--root /absolute/new/path` chooses an explicit fresh root; existing roots refuse.

The provider executable is **synthetic**, selected only in these test images.
The unmodified ClaudeAgent invokes it through the usual subprocess boundary.
It matches the explicit scenario, role and fixture bytes, performs prescribed
workspace edits, and writes ordinary provider reports using current operands.
The worker still runs real subprocesses in real containers, freezes outputs,
executes tests and delivers actual evidence. Coordination, private lines,
review sessions, merge/reconciliation, causal tests, authorization receipts,
leases, integration and terminal observation use their normal implementations.
B has three separate derived-judgment containers; its reconciled import has no
model runtime. All provider judgments are simulated and labelled in findings.

No real credentials or model calls are used. The command creates a private
registry containing explicitly synthetic bytes; both test profiles use network
`none`. Image construction also uses network `none` and a local immutable base.
The base contains a provider installation, but the test image replaces its
executable. Production images and historical run10 artifacts are untouched.

Success requires both Jobs' stages completed, all three derived judges accepted,
no remaining labelled runtime, a clean unchanged original source, a clean final
committed final view and successful A/B behavior checks plus whole-view tests.
Integration advances objects/reference without updating the target checkout or
index. Those original files remain diagnostic evidence. The runner reads the
Authority canonical target, exports that exact commit to `final-view/`, records
its commit/tree/blob/content manifest, runs both behavior scripts and all tests,
and requires the view to remain byte/mode clean and the committed reference
unchanged. See `evidence/final-view.json`, `evidence/run-result.json`,
`evidence/terminal-status.json`, `evidence/samples.jsonl`, `evidence/serve.log`,
`evidence/final-tests.log`, `evidence/final-greeting.log`,
`evidence/final-hours.log` and `scenario-result.json` under the printed root.
Canonical preparation/start failures are read through the read-only manager
owner and correlated to the current stage assignment without requiring a runtime
or exchange. Failures retain the root and exact owner evidence; containment stops only this
run's serving process and Authority-labelled containers. There is no retry,
state repair or fabricated independent-review marker.

This proves simulated-provider coordination, not live-provider acceptance.
The original run10 stays interrupted. The first scenario is one happy path;
separate invocations isolate all mutable identities and roots, but concurrent
runs must fit the existing capacity requirements. No parallel agents are needed.

`provenance.json` identifies the historical helper and baseline sources. The
new `fixtures/scenario.json` contains explicitly authored synthetic effects.
The retained image context and recipes identify the actual test image inputs.
