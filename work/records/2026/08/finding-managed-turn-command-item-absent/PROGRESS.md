# Progress — Managed turns record no commandExecution item

## The reviewer's correction, confirmed — 2026-08-23

Implementer: baton.claude. Evidence:
`evidence/implementer-confirmation-2026-08-23.txt`.

### My headline was wrong

The command ran through a provider `custom_tool_call name=exec` wrapping
`tools.exec_command`, not the built-in shell — so the `ThreadItem` union,
which has no such variant, is behaving correctly. I confirmed it on the W7830
smoke turn as well as on the reviewer's nonce probe: one custom tool call, no
built-in shell call, in both.

**What my probe established was less than I said**: that a command ran, and
that no `commandExecution` item appeared. I read "the server failed to record
it" into the gap between those two facts, and the gap had a third explanation
I did not look for. A nonce proves execution; it does not prove which
execution path.

### A second claim of mine was also wrong

I called the managed traceback "consistent with the read-only database this
Work is about". It is `unable to open database file`, on the READ, from
`Authority.__init__`. The original observation quoted `attempt to write a
readonly database` on a claim — a different error on a different operation,
which I let blur together. It also means the smoke's environment does not
reproduce the original defect's shape at all.

### What remains, and what I did not do

Neither gate can be proven on this deployment and neither is to be relaxed;
the reason is now correctly described. The CLI's unhandled traceback is real,
separable, and now reproducible with no model against both the deployed build
and the current tree, with a wider scope than first recorded.

**I did not run the bounded live probe.** The reviewer put it behind an
operator decision, and running it to make the recommendation look settled
would be choosing the option rather than reporting it.

### State

Superseded by the section below.

## The opt-in repeat, and what it found instead — 2026-08-23

Implementer: baton.claude. Evidence:
`evidence/implementer-live-items-2026-08-23.txt`.

### The pinned check is answered, and the answer is no

Plan item 5 required the probe to opt into the experimental API and repeat
once, because the first operator run had declared `experimentalApi: false` and
so established only the stable surface. I ran it, differing from the reviewer's
probe in one field.

`rawResponseItem/completed` emits ZERO items on BOTH surfaces. The capability
declaration was not the reason. Plan item 6's oracle was gated on a matched
`custom_tool_call` pair that provably cannot occur on this build, so it
cancelled itself — which is the gate doing its job rather than my improvising
a substitute.

### The thread nobody had pulled

The first operator run reported `item/started` 3 and `item/completed` 3
against two stored item types. Three announced, two persisted, and counts
cannot say what the third was. Retaining bounded item payloads answers it: a
structured `commandExecution` ThreadItem, with the exact command, `source`, a
terminal `status`, an `exitCode`, and a correlatable id — everything both
blocked oracles need, and not model-generated JavaScript. `thread/read` with
`includeTurns` then drops it, and drops `reasoning` too.

**So both prior diagnoses are wrong, including the reviewer's correction of
mine.** Mine said the server never recorded the item. The correction said the
deployment used a different item family. On this configuration the server
records it, announces it, and the STORED TURN HISTORY OMITS IT. The defect is
persistence.

I had this result written up once with "never fires" resting on two runs that
both declared `experimentalApi: false` — the exact overstatement plan item 5
existed to prevent. I ran the opt-in before recording anything, which is why
the claim now stands.

### What I did not do

**I did not build a gate on it.** The approved boundary named a transport that
does not exist here, and adopting the one that does also requires configuring
the managed stack to execute through the built-in shell — both probes ran with
no provider custom tool, and the managed deployment runs `custom_tool_call
name=exec`. A gate reading `item/completed` would see nothing under today's
configuration. That is an operator decision twice over, and the configuration
half is untested end to end.

Neither gate relaxed, neither oracle changed, `exec_policy.mjs` and the eight
exact commands untouched.

### State

**Awaiting the operator decision recorded at the end of FINDING.md.** Nothing
outside this dossier was changed; whitespace clean.
