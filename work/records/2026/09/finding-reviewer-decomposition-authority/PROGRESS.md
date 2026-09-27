# W285507 preparation progress

## 2026-09-27 — baton.prompt

Pinned the confirmed version-neutral ruling, exact role addition and current
plan; added supporting procedure to AGENTS.md. Reviewed the deployed rview role
and docs/BATON-SETUP.md: role instructions belong to accepted configuration;
existing sessions need supported launcher refresh to receive a changed role.

Prepared `/tmp/baton-reviewer-role-W285507.py` for the owner, with exact config
and addition digest checks and an atomic file replacement. The intended JSON
changes are generation 12 to 13 and appending ROLE-ADDITION.txt to the baton
rview instructions. Script syntax checked; semantic delta inspected;
`git diff --check` passed. No product tests run.

The helper has NOT been executed. No live config edit, regen, worker restart,
Git mutation or independent acceptance is claimed. Owner selected tuner to
finish this existing Work. Prompt releases the documented file ownership on
handoff; tuner revalidates the proposal and supplies owner acceptance steps.

## 2026-09-27 — baton.tuner, claim285549

Revalidated AGENTS.md supporting procedure, approved role addition and current
configuration. Added durable prepare-role.py with default read-only preview and
explicit owner-only --apply, plus ACTIVATION.md with exact acceptance, isolated
reviewer refresh and readback steps. Preserved prompt's role wording and AGENTS
change. No application, protocol or test paths changed.

Verification: helper compiled without executing its write branch; read-only
preview passed exact config/addition digest guards and showed only generation
and reviewer-instructions changes. Whitespace and final configuration-digest
checks are recorded in VERIFICATION.md. Product tests and live execution are
not applicable to this documentation/preparation slice. No config mutation,
acceptance, worker restart or instruction delivery is claimed. Owner activation
and human Git checkpoint remain pending; return to baton.decide per handoff.
