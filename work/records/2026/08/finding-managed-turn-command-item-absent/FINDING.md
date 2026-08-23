# Managed turns record no commandExecution item

W7989. Routed out of W7830 on its reviewer's instruction, cross-referencing
W2845.

## Observed — 2026-08-23 (diagnosis superseded below)

A managed Codex turn that DEMONSTRABLY RAN a shell command produces no agent
`commandExecution` item in `thread/read` with `includeTurns` on the installed
`codex-cli 0.149.0`.

## Measured, not inferred

A turn cannot be argued into having run a command. It can be caught having run
one, by asking for a value it cannot know without executing.

```text
cwd:     a fresh temporary workspace
prompt:  run exactly `date +%s%N` and reply with ONLY its exact stdout
         (every server request answered with a denial, so nothing hangs)

turn status:  completed
ITEM TYPES:   userMessage, agentMessage
AGENT:        "1787459998183143305"
NONCE ms:     1787459998183 — INSIDE the run window
```

A nanosecond timestamp inside the window of the run is not knowledge. An
independent probe agrees: one `/bin/echo hello-probe` instruction, three
items — `userMessage` and two `agentMessage` — and no command item.

`CommandExecutionThreadItem` IS declared in the installed
`.codex-app-server-schema/v2/ThreadReadResponse.json` `ThreadItem` union, so
this is the RUNNING SERVER not recording it rather than a schema anybody
misread.

The final sentence above was the initial diagnosis. It is explicitly
superseded by the provider-path evidence below; the absence from `thread/read`
remains observed and confirmed.

## What it blocks

**W2845's exact-policy matrix.** Its command oracle requires one exact agent
command item and rejected all eight Docker cases fail-closed for this reason.
The oracle is signed off and correct; its premise is unmet by this build.

**W7830's managed-write smoke.** Its readiness shape requires two ordered
command items. W7830's reviewer asked for the smoke to be re-tested after
removing a contradictory developer instruction, and then routed separately if
the absence persisted. The instruction was corrected, the smoke re-run, and
the absence persists.

## What must not happen

Neither gate is relaxed to pass on this build. A gate that accepts zero
command items, or falls back to the committed outcome alone, is green and
establishes nothing — which is the exact failure mode W2845's oracle exists to
remove.

Direct `command/exec` is not a substitute either: it bypasses the managed-turn
behaviour both gates exist to prove.

## A second, separable observation

The deployed baton CLI surfaces the sandbox read-only-database refusal as an
UNHANDLED PYTHON TRACEBACK from `baton_work/cli.py entry`, not the typed JSON
error every other refusal uses. The same canonical commands succeed cleanly
outside the sandbox, verified against a scaffolded disposable home with no
model involved.

W7830's reviewer asked for this to be preserved as an operational finding and
for sandbox authority NOT to be broadened to avoid it.

## Directions, none of them an implementer's to choose

- an app-server build whose `thread/read` records command items;
- a different transport for the same evidence that is still the MANAGED turn;
- or an explicit decision that these gates cannot be proven on this build, and
  what the Works do meanwhile.

## Confirmed diagnosis correction — 2026-08-23

The nonce probe did not invoke app-server's built-in shell path. Its provider
rollout records this exact pair, joined by
`call_Z6b6zR31NOYGYmjkBVmuD26E`:

```text
custom_tool_call name=exec
input=const r = await tools.exec_command({"cmd":"date +%s%N", ...});
      text(r.output);

custom_tool_call_output
Script completed
Wall time 0.0 seconds
Output:
1787459998183143305
```

This is the execution path that produced the in-window nonce. It is NOT a
`local_shell_call`, and therefore it is not the source of a
`commandExecution` ThreadItem. The earlier statement that the running server
failed to record a built-in command item is superseded. The actual mismatch is
between the command-item-only oracle and this managed deployment's provider
custom-tool execution path.

The installed schemas confirm the boundary:

- `ResponseItem` includes `custom_tool_call` and
  `custom_tool_call_output`, joined by `call_id`;
- `RawResponseItemCompletedNotification` carries a `threadId`, `turnId`, and
  one such `ResponseItem`;
- `ThreadItem` has no custom-tool-call variant, so `thread/read` cannot return
  this evidence as a command item.

The official app-server guide describes `commandExecution` for shell-command
ThreadItems and says `thread/read` returns the persisted turn history. That is
consistent with the schema and does not promise that a provider custom tool's
nested `tools.exec_command` becomes a shell-command ThreadItem.

Durable excerpts and locators are in
`evidence/reviewer-provider-path-2026-08-23.txt`.

## Proposed evidence transport, not yet proven or accepted

The installed protocol offers one candidate that remains inside the managed
turn: capture live `rawResponseItem/completed` notifications and correlate the
outer `custom_tool_call` with its `custom_tool_call_output` by thread, turn,
and `call_id`.

That signal is not automatically a safe command oracle. The call input is
model-generated JavaScript, not a structured command field. Parsing arbitrary
JavaScript or accepting arbitrary output would recreate the original
false-green risk. Before either blocked gate can use this route, a bounded live
probe must establish that the deployed server emits BOTH response items, and
the accepted design must define a fail-closed exact wrapper contract, matching
rules, duplicate/extra-call handling, completion semantics, and denial/error
semantics. No gate is relaxed while that work is open.

## Operator decision required

Choose one of these boundaries before implementation:

1. Authorize a bounded live probe and design review for a strict
   `rawResponseItem/completed` custom-tool oracle.
2. Require a deployment/build whose managed shell path produces structured
   `commandExecution` ThreadItems.
3. Declare W2845 and W7830 unprovable on this deployment and decide whether
   they remain blocked or parked.

The reviewer recommends option 1 as the next investigation because it follows
the execution evidence the current provider actually emits, but it is not yet
an implementation-ready acceptance contract.

## Confirmed operator decision — 2026-08-23

Option 1 is approved. Run a bounded live probe of the current managed provider
path and, only if the probe proves both correlated response items are emitted,
define and implement a strict fail-closed oracle over
`rawResponseItem/completed`.

The oracle must correlate the exact thread, turn, and `call_id`; accept only
the one explicitly supported outer `tools.exec_command` wrapper shape; and
reject missing, duplicate, extra, malformed, unmatched, denied, errored, or
incompletely settled calls. It must not parse arbitrary JavaScript or infer
execution from an agent message, a committed Baton outcome, or direct
`command/exec`.

This decision authorizes investigation and the bounded correction. It does
not relax either blocked gate. W2845 and W7830 remain blocked until the live
probe, deterministic regressions, and independent review establish that the
new evidence path proves the same managed-turn properties their current
command-item oracles were designed to prove.

## Correction — 2026-08-23

**THE HEADLINE ABOVE IS WRONG, AND IS KEPT SO THE CORRECTION HAS SOMETHING TO
POINT AT.** The reviewer inspected the nonce probe's rollout; the command ran
through a provider `custom_tool_call` named `exec`, wrapping
`tools.exec_command`, and never through the app-server's built-in shell. The
installed `ThreadItem` union has no `custom_tool_call` variant — 18 variants,
none of them it — so it is behaving correctly by not representing one.

I confirmed it on the turn that actually matters, the W7830 smoke: one
`custom_tool_call name=exec`, no built-in shell call.

**WHAT MY PROBE ESTABLISHED WAS LESS THAN I SAID.** That a command RAN, and
that no `commandExecution` item appeared. I read "the server failed to record
it" into the gap between those two facts, and the gap had a third explanation
I did not look for. A nonce proves execution; it does not prove WHICH
EXECUTION PATH.

**A SECOND CLAIM OF MINE WAS ALSO WRONG.** I called the managed traceback
"consistent with the read-only database this Work is about". The exact output
is `sqlite3.OperationalError: unable to open database file`, from
`Authority.__init__` via `lifecycle.open_bound`, on the READ. The original
W7830 observation quoted `attempt to write a readonly database` on a claim. A
different error, on a different operation, and I let the two blur.

It also means the smoke's environment does not reproduce the original defect's
shape at all: there, the read succeeded and the mutation was refused; here
neither works, which is why exactly one command appears in the turn.

**WHAT REMAINS TRUE.** Neither W2845 nor W7830 can prove its live gate on this
deployment, and neither gate should be relaxed. The reason is now correctly
described: the managed deployment executes through a provider custom tool
whose items the thread-item oracle was never built to read.

**AND ONE THING THAT IS BOTH REAL AND SEPARABLE.** The canonical CLI surfaces
a sqlite open failure as an unhandled Python traceback rather than the typed
JSON error every other refusal uses — reproduced with no model and no sandbox,
against the deployed build AND the current source tree. See plan item 4.

Evidence: `evidence/reviewer-provider-path-2026-08-23.txt` and
`evidence/implementer-confirmation-2026-08-23.txt`.

## Bounded live probe — operationally blocked 2026-08-23

The operator approved option 1. The reviewer implemented the bounded
evidence-only probe at `evidence/probe_raw_response_items.mjs`: one harmless
`date +%s%N` turn, every interactive request denied, bounded notification and
custom-item output, isolated temporary credential home, and cleanup on every
exit path.

**Confirmed operational blocker:** app-server starts over stdio and returns an
exact thread and turn id, but the current non-interactive managed sandbox
refuses its outbound provider WebSocket with `Operation not permitted`. The
90-second measured attempt emitted `turn/started` and ordinary item lifecycle
notifications, then timed out with zero `rawResponseItem/completed` items and
zero server requests. This neither proves nor disproves the candidate evidence
transport; the provider was never reached.

Standing managed-turn policy forbids escalation. The probe must therefore be
run once by `baton.ops` from an environment with the already-configured
provider authority. W2845 and W7830 remain blocked, and no oracle may be
implemented from absence caused by this transport refusal. Exact evidence:
`evidence/reviewer-live-probe-network-blocker-2026-08-23.txt`.

## First operator probe — stable surface negative 2026-08-23

The operator ran the bounded probe successfully through a completed provider
turn. It emitted ordinary thread, turn, item, usage, and rate-limit
notifications, but no `rawResponseItem/completed` notification and no custom
item. The persisted turn contains only `userMessage` and `agentMessage`.
Durable bounded output:
`evidence/operator-live-probe-2026-08-23.json`.

This is NOT yet a conclusive negative for the proposed raw transport. The
probe initialized with `capabilities.experimentalApi: false`. Official Codex
app-server documentation says that false remains on the stable API surface
and true enables experimental methods and fields; the same official page does
not document `rawResponseItem/completed` as stable. The installed generated
schema includes that notification, but inclusion in the schema alone does not
establish delivery to a client that opted out of experimental API.

**Inferred next check:** correct the bounded probe to opt into
`experimentalApi: true` and repeat it once under the same denial, isolation,
bounded-output, and cleanup controls. This is a correction to the probe's
capability declaration, not a relaxation of either oracle. If the opt-in run
still emits no correlated raw items, option 1 has no proven transport on this
app-server build and must return to the operator for another boundary choice.

Official capability contract:
https://developers.openai.com/codex/app-server#experimental-api-opt-in

## Opt-in repeat: raw transport dead, real transport identified — 2026-08-23

Plan item 5 is closed, and it closes plan item 6 with it.

**`rawResponseItem/completed` NEVER FIRES ON THIS BUILD.** Zero raw items and
zero custom items with `experimentalApi: false`, and zero again with
`experimentalApi: true` — the opt-in the previous section inferred as the next
check. The capability declaration was not the reason. The transport option 1
was approved to prove does not exist here, so the strict wrapper oracle pinned
in plan item 6 has nothing to read and must not be built.

**BUT THE EVIDENCE BOTH GATES WANT IS ALREADY ON THE WIRE.** The first
operator run reported `item/started` 3 and `item/completed` 3 against two
stored item types, and nobody had asked what the third was. Retaining bounded
item payloads answers it:

```text
item/started   commandExecution  status=inProgress
               command=/bin/bash -lc 'date +%s%N'
item/completed commandExecution  status=failed exitCode=1
               command=/bin/bash -lc 'date +%s%N'
               keys: type,id,pluginId,scriptPath,command,cwd,processId,
                     source,status,commandActions,aggregatedOutput,exitCode

storedThreadItemTypes: ["userMessage","agentMessage"]
```

The structured `commandExecution` ThreadItem IS emitted live, with the exact
command, `source`, a terminal `status`, an `exitCode`, and an id an approval
can be correlated to — and it is NOT model-generated JavaScript, which was the
standing objection to the raw path. `thread/read` with `includeTurns` then
does not persist it. `reasoning` is dropped too, so this is not specific to
commands.

**THE DEFECT IS THEREFORE ABOUT PERSISTENCE, NOT RECORDING AND NOT THE ITEM
FAMILY.** This Work's original headline said the server never recorded the
item; the reviewer's correction said the deployment used a different item
family. On this configuration both are wrong. The server records it, announces
it, and the stored turn history omits it.

**THE CAVEAT.** Both probes pin a `CODEX_HOME` with no provider custom tool,
and both executed through the built-in shell. The managed deployment executes
through `custom_tool_call name=exec`. The execution path is
CONFIGURATION-DEPENDENT, and a gate reading `item/completed` would see nothing
under the managed stack's current configuration. What is established is that
the structured item exists and is reachable on this build — not that the
managed stack as configured emits it.

Also reported rather than smoothed: the probe's command failed, `exitCode=1`,
under its sandbox. The item carried the exact command and a truthful nonzero
exit, which is what a fail-closed oracle needs; a run whose command succeeds
has not been observed here.

Evidence: `evidence/implementer-live-items-2026-08-23.txt`,
`evidence/implementer-live-probe-2026-08-23.json`,
`evidence/implementer-live-probe-experimental-2026-08-23.json`,
`evidence/probe_live_items.mjs`,
`evidence/probe_live_items_experimental.mjs`.

## Operator decision required, second time

The approved boundary is spent: option 1 named a transport that does not
exist on this build. Neither gate is relaxed, and no oracle is implemented,
until one of these is pinned:

1. Adopt live `item/started` / `item/completed` as the evidence transport, and
   accept that the managed stack must be configured to execute through the
   built-in shell rather than a provider custom tool for either gate to see
   anything. Both halves are operator decisions, not an implementer's.
2. Treat the `thread/read` omission as the defect to fix or escalate upstream,
   and keep both gates blocked on a build whose persisted turn carries its
   command items.
3. Declare W2845 and W7830 unprovable on this deployment and decide whether
   they stay blocked or are parked.

The implementer recommends option 1 because it is the only route measured to
carry the required evidence, but it is not an implementer's to choose and its
configuration half has not been tested end to end.

## Independent review correction — 2026-08-23

The opt-in repeat is valid evidence for the built-in-shell configuration that
the two probes actually exercised. It does not establish the broader claim
that `rawResponseItem/completed` "never fires on this build," nor that the
target matched `custom_tool_call` / `custom_tool_call_output` pair cannot occur
under the managed provider configuration. Neither probe configured or emitted
the provider custom tool whose raw pair the approved option required. Those
broader statements above are therefore **SUPERSEDED** by this scoped result:

- **Confirmed:** stable and experimental-capability built-in-shell turns
  emitted no `rawResponseItem/completed` notifications and no custom items.
- **Open:** the managed provider custom-tool response path was not exercised,
  so its raw notification behavior remains unmeasured.
- **Confirmed:** a built-in-shell turn emitted live `commandExecution` items
  that `thread/read(includeTurns)` omitted.

The live item also does not yet satisfy the existing strict command oracle.
The request was `date +%s%N`, while the observed item recorded
`/bin/bash -lc 'date +%s%N'`. The W2845 oracle compares its recorded command to
the requested command literally, so it would reject this evidence. Adopting
live item events needs an explicit, deterministic contract for shell wrapping
or normalization; review must not infer one. Only a failed execution was
observed, so the positive success path also remains unproved.

The second operator decision remains necessary. Option 1 must account for both
the managed custom-tool versus built-in-shell configuration boundary and the
literal-command mismatch. No oracle change is authorized by these probes.

## Confirmed second operator decision — 2026-08-23

The operator selected option 3. V11 exists to provide sufficient coordination
while v12 is built; it must not block v12 on a new managed-execution transport
or an upstream app-server persistence change.

W7989 closes satisfying as the diagnosis and preserved evidence. W7830 and
W2845 close cancelled because their strict live certification boundaries are
not achievable on the current managed custom-tool deployment. This is NOT a
claim that either live gate passed, and neither oracle is weakened or made
green. Their deterministic safeguards and diagnostics may ship with their
passing suites, but the unavailable live certification remains explicitly
unmet in the permanent records.

The production managed Codex path is not reconfigured merely to make the test
observable. V12's external Worker Manager owns the durable execution and
evidence boundary going forward. Closing these v11-only certification Works
removes them as blockers of the schema-28 rollout and the v12 campaign.
