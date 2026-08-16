# Finding: the Codex monitor must run v10 and v11 readiness in parallel

## Parent

`finding-v11-messaging-cutover-gate` — this child depends on the canonical v11
participant-action contract in `finding-v11-participant-readiness`.

## Observed

`tools/codex-event-bridge/src/baton_source.mjs` is a correct v10 adapter, but
its command syntax, output parser, one-head deduplication and compact event
instruction are all protocol-10-specific. The shared stack config also names
one Baton binary/config and one participant per target. During certification,
the same Codex target needs v10 `baton.reviewer` safety readiness and v11
`baton.codex` candidate readiness without running duplicate consumers for
either identity.

## Proposed boundary

- Keep protocol adapters explicit; do not guess a protocol from paths or JSON
  accidents. A named source declares its binary, config and protocol, and each
  monitor mapping declares source, participant and Codex target.
- Uniqueness is `(source, participant)`, while several distinct source/member
  mappings may intentionally feed one target. The event bridge continues to
  serialize that target's turns.
- Preserve the v10 adapter and exact-message claim instruction unchanged.
  The v11 adapter invokes key-value `wait`, parses structured action keys and
  emits compact v11 action locators with v11 standing policy.
- v11 delivery memory tracks every currently present action key: emit a key
  once while it remains level-triggered, remove it when the action disappears,
  and rediscover current actions after monitor restart. Claiming the same Work
  must not create a duplicate event; a genuinely new obligation or deadline
  generation must.
- Monitors remain read-only. The awakened agent uses canonical v11 CLI/JSON to
  claim Work, answer/report obligations, read Threads and pass or close Work.

This boundary requires review after the readiness child fixes the exact JSON
shape; implementation must not race ahead of that contract.

## Decision — 2026-08-16: parallel operation is disposable cutover scaffolding

The proposed generalized multi-source bridge boundary above is superseded.
Running v10 and v11 together is deliberately short-lived: v10 exists only as
the reliable channel while v11 is being certified, and the intended outcome is
to retire it. Do not invest in making v10 and v11 elegant peers or in reusable
multi-protocol bridge machinery.

Use the smallest isolated arrangement that preserves both authorities during
the trial. Two independent app-server/bridge stacks, separate sockets, or
another operationally heavier but simpler temporary arrangement are acceptable.
Each participant identity still has exactly one readiness consumer. Implement
shared machinery only when it is independently required by the permanent v11
system; otherwise remove the temporary v10 path at cutover.

## Decision — 2026-08-16: one bridge, one additional v11 producer

W136 established the projection-4.3 participant action contract. Inspection of
the existing Codex integration then found a still smaller boundary than two
complete stacks: the running v10 stack already owns the app-server, the Codex
thread mapping, the event bridge and its per-target serialization. A standalone
v11 readiness producer can feed the same local event socket and target without
owning or changing any of those components.

The trial topology is therefore:

```text
v10 baton.reviewer wait ── existing v10 monitor ─┐
                                                 ├─ existing event socket
v11 baton.codex wait ── new v11 monitor ─────────┘       │
                                                         ▼
                                               existing bridge/target
                                                         │
                                                         ▼
                                               this Codex thread/TUI
```

The v10 adapter, v10 stack configuration and active app-server remain
unchanged. A second app-server or bridge is not needed unless the live proof
uncovers an actual isolation conflict. The new program is the permanent v11
readiness adapter, launched independently during the overlap. Integrating it
as the stack's sole Baton source belongs to the later v10-retirement cutover,
not to this child.

The v11 adapter contract is:

- invoke the configured absolute v11 binary as
  `--config PATH --participant TEAM.MEMBER wait timeout=SECONDS`;
- require a protocol-11 envelope for the configured participant and a
  structured `result.actionable` array; refuse malformed or wrong-protocol
  output rather than guessing;
- emit one trusted compact Baton event per previously unseen `action_key`,
  with an identity scoped by authority UUID, participant and action key;
- include the action kind/key and the Work, obligation or round locator needed
  for the agent to inspect canonical v11 JSON, but no discussion body and no
  generic external-event instruction block;
- remember the whole currently returned action-key set, not one queue head;
  suppress a key while it remains present, forget it after it disappears, and
  emit it again if it later becomes actionable again;
- rediscover and emit the current set after monitor restart. Claiming routed
  Work does not itself change its stable `work:<id>` action key, so the running
  monitor does not duplicate that wake;
- remain read-only. It never claims Work, answers an obligation, marks New,
  changes phase or advances a cursor. The awakened Codex participant does that
  through the canonical v11 CLI/JSON surface;
- back off after unchanged immediate results and after errors so a persistent
  actionable set cannot create a busy loop.

During the overlap exactly one process owns v10 `baton.reviewer` readiness and
exactly one process owns v11 `baton.codex` readiness. Both may intentionally
name the same Codex target because the bridge serializes turns per target. This
is source separation, not duplicate consumption of one identity.

Acceptance must cover multiple simultaneous action keys, stable claimed-Work
suppression, disappearance/reappearance, a new obligation key, a new deadline
generation, monitor restart discovery, malformed/wrong-protocol output,
forwarding retry without losing a key, and an unchanged green v10 adapter
suite. The live proof then runs both monitors against their real authorities,
shows that each wakes this thread, and confirms that neither source can claim,
suppress or acknowledge the other's work.

## Clarification — 2026-08-16: W148's umbrella record binding is correct

The reviewer's T148 message asking the handler to revise W148's binding to this
nested child-finding directory is superseded. The already-confirmed WS-6 rule
permits exactly `work/records/YYYY/MM/<stable-record>`: a binding identifies the
permanent record root, while files and subdirectories below it are addressed by
dossier-relative artifact references. W148 was therefore created with the
correct binding to `work/records/2026/08/finding-recursive-target-graph`.

Do not widen the binding grammar and do not append a binding revision. This
child directory remains the exact decision/plan location and should be cited as
evidence in implementation and review messages beneath the correctly bound
umbrella record.

## Decision — 2026-08-16: the product is `codex-baton-bridge`, outside Baton

Baton itself remains model-neutral. Its CLI and JSON authority expose the
participant-relative, read-only `wait` operation; they do not contain Codex
app-server transports, event sockets, thread routing or model-specific process
supervision. Other agent integrations may consume the same Baton surface
through ACP or their own adapters without inheriting Codex machinery.

The W148 program is therefore named `codex-baton-bridge` and lives in the
external Codex event-bridge integration, not in the Baton v11 application or
core package. Rename the current `baton-v11-monitor` public entry point and its
implementation/test vocabulary before sign-off; do not ship a compatibility
alias during this unreleased trial. Its responsibility remains narrow:

```text
baton wait JSON -> codex-baton-bridge -> Codex event socket/app-server
```

The distinction is architectural, not merely cosmetic. Baton decides what is
actionable and returns canonical JSON. `codex-baton-bridge` decides how that
readiness schedules a turn in an existing Codex thread. Operator recipes may
start both products together, but the bridge is not a Baton CLI mode and is not
part of the immutable Baton client distribution.
