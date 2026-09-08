# Retained deterministic evidence needed — W106673

baton.codex, claim 107091, 2026-09-07. This is an operator evidence-export
request, not a request to repeat the experiment or grant privileges to agents.

The reviewer cannot read these attempted paths (permission denied):

- /tmp/baton-w106673-k65r7btj/result.json
- /tmp/baton-w106673-k65r7btj/runner.json
- /tmp/baton-w106673-k65r7btj/happy/events.json

Please provide a readable, provenance-preserving copy of exactly 18 JSON files
from the existing retained root. Keep the relative paths in the copy:

1. result.json and runner.json at the retained root.
2. events.json and gate.json in each of happy, open-file, cwd, omitted, before,
   after, stop-start-one and stop-start-two.

A suitable destination is this dossier's new
evidence/operator-export-k65r7btj/ directory. Record the source root, export UTC,
exporting operator and per-file SHA-256 values. Preserve original bytes and
protected originals. No broad permission change, recursive export of unrelated
temporary state, credential access, container removal or new runtime is needed.
If a named file is missing, report it explicitly instead of reconstructing it.

runner.json binds the executed script hashes, image and fixture group. The happy
events bind the actual container/process/session/workspace identities, mount
tables, detach outcomes, denied writer probes, reattachment and consumed bytes.
Negative events bind EBUSY, before/after helper loss, closed gates before/after
reload and shutdown preceding consumption. Gate snapshots supply final identity
and generation state; they do not substitute for event history. Stop/start events
bind the comparison and replacement identity. The result file reconciles these
records with the supplied summary.

The operator-transcribed success and timing summary is already preserved, and
the reviewer independently inspected the eight exact retained containers as
exited, PID 0, on the reviewed image. Those observations do not expose historical
kernel topology, exact executed bytes or gate transitions. No mechanism defect
is inferred from the protected directory; independent evidence acceptance is
pending these artifacts. Return the Work for review after export.
