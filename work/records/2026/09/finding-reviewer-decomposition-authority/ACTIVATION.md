# W285507 owner activation packet — 2026-09-27

Prepared, not activated. The owner handoff285547 reserves configuration
acceptance and safe launcher refresh. Run from `/home/sl/src/baton`.
Each command below is a separate operator action; do not paste the entire
procedure as an unattended batch. Owner commands intentionally name baton.slaw;
the instruction read names the actual launcher's reviewer identity.

## Review and accept the exact role change

`prepare-role.py` defaults to read-only preview. It binds the entire generation
12 configuration and ROLE-ADDITION.txt by SHA256 (see PLAN.md), preserving the
existing reviewer instructions verbatim and appending the approved paragraph.
The only semantic changes are generation 12 → 13 and
`teams.baton.roles.rview.instructions`. It refuses drift, including a generation
accepted by other work; obtain a freshly reviewed proposal in that case.
This durable helper supersedes the temporary `/tmp/baton-reviewer-role-W285507.py`.

```sh
python3 work/records/2026/09/finding-reviewer-decomposition-authority/prepare-role.py
```

After owner review, prepare the on-disk configuration, then separately accept it:

```sh
python3 work/records/2026/09/finding-reviewer-decomposition-authority/prepare-role.py --apply
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw regen
```

If acceptance fails, retain the error and stop activation: an edited JSON file
is not accepted state. Do not increment again or infer successful delivery.
Read back accepted instructions for the active reviewer launcher:

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.rvpc instructions role=rview
```

Require configuration_generation 13 and the exact preserved prefix plus
ROLE-ADDITION.txt. This read proves accepted configuration, not delivery into an
existing conversation. Both baton.rvpc and baton.codex hold the same role;
only rvpc currently serves the review Route. No role membership or Route changes
are proposed.

## Owner-selected safe refresh

Sources: docs/BATON-SETUP.md (Role instructions; explicit single-stack
maintenance), tools/codex-event-bridge/README.md (accepted role instruction
startup), and tools/infra.py. Dispatcher startup re-resolves role instructions.
`runtime-refresh` publishes runtime facts; it does not refresh role instructions.
The supported isolated stack lifecycle below creates a fresh context. Preserve
its durable continuation checkpoint first; do not replace a claimed worker.

Select a maintenance boundary. Request drain and read until mode is `paused`
with zero active claims; allow active work to finish and release normally.

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw drain reason='W285507 safe reviewer instruction refresh'
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw dispatch history=false
```

Inspect the selected isolated stack:

```sh
python3 tools/infra.py status /home/sl/baton-v11.14aecfb/rview-pc
```

Revalidate the manifest still selects only baton.rvpc with role rview and the
specified binary/config. Its version-1 manifest has no control stanza, so
`stop-drained` is not available for it. Plain stop is immediate: use it ONLY
after the canonical paused/zero-claims check above and checkpoint preservation.
Do not modify its manifest to work around that distinction.

```sh
python3 tools/infra.py stop /home/sl/baton-v11.14aecfb/rview-pc
```

```sh
python3 tools/infra.py start /home/sl/baton-v11.14aecfb/rview-pc
```

```sh
python3 tools/infra.py status /home/sl/baton-v11.14aecfb/rview-pc
```

Require successful startup, one readiness consumer for baton.rvpc, and launcher
instruction-resolution/readback evidence matching accepted generation 13 and the
exact role addition. Record the new context/start identity and evidence in this
dossier; service liveness alone is not proof of instruction delivery. If evidence
is missing or startup fails, keep dispatch paused and record the concrete failure.
Once delivery and exclusive readiness are verified, the owner may resume:

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw resume reason='W285507 reviewer generation 13 delivery verified'
```

The registered baton.codex context belongs to the shared main stack. Its current
session is not updated by restarting rview-pc. Keep it off the review Route until
its next separately selected safe launcher refresh and matching readback; do not
restart the main stack just to refresh this idle reviewer. Record that delivery
as pending. These instructions do not authorize concurrent consumers or changes
to ongoing implementation allocation.

## Completion evidence

Record config acceptance receipt, active-reviewer context/start identity,
accepted/delivered instruction evidence, dispatch recovery and any deferred
consumer explicitly. W285507 remains open until the owner accepts the outcome.
Human Git checkpoint remains pending. Suggested commit message:
`docs: grant reviewers bounded decomposition authority`.
