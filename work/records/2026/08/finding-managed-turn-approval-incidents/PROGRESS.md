# Progress

Implementer-owned. One writer (`baton.claude`).

## Status

**Round 7 — the pinned exact-set ruling implemented.** `W415` was
reclaimed 2026-08-21T00:58Z and is being passed back to `baton.bug`
(`rview`).

Gate green: **2777 + 52** Python, **55** ACP, **167** dispatcher. The
live exact-policy matrix was re-run after the change and still passes
8/8 with clean teardown.

### Still outstanding for the operator

Unchanged: install the exact rules **and remove the broad one** (a
half-finished upgrade is refused by name), and rule on `SCHEMA_VERSION`
25 → 26.

## Root cause — corrected in round 2, from live evidence

Round 1 of this record diagnosed the failure as the execpolicy allow
rule failing to match because Codex wrapped the command in
`/bin/bash -lc`. **That was wrong, and so was the pinned finding's
version of it.** The reviewer was right that declaring an approval
policy is not the fix; the evidence shows why, and it is not what either
of us thought.

I read the live reviewer rollout
(`~/.codex/sessions/2026/08/20/rollout-2026-08-20T11-38-55-*.jsonl`) and
counted every Baton invocation in the session that produced the
incidents:

| Baton calls in the incident session | Outcome |
| --- | --- |
| 19 — `detail`, `thread`, `work-events` | ran; no approval, no escalation |
| 9 — `mark-seen`, `phase`, `say`, `claim` | `sandbox_permissions: require_escalated` |

The split is exactly reads versus writes. The turn context says why:

```json
"sandbox_policy": { "type": "workspace-write" },
"workspace_roots": ["/home/sl/src/baton"],
"permission_profile": { "file_system": { "entries": [
  { "path": "/home/sl/src/baton", "access": "write" },
  { "path": "/tmp",               "access": "write" } ] } }
```

The coordination home `/home/sl/baton-v11.8835cd5/` is **outside** those
writable roots. Every mutating Baton verb writes `work.sqlite3` there,
so every one needed a sandbox escalation — and an escalation is what
asks a human.

The allow rule was never the problem, and neither was the shell wrapper:
the executable ran fine, nineteen times, through a shell.
`~/.codex/rules/default.rules` is a red herring for this defect, and the
rule appended at 17:50:36Z did not help because nothing was wrong with
command matching. The managed turn simply had no write access to the
authority it exists to update.

**`FINDING.md`'s "Observed" section is inaccurate on this point.** It is
the reviewer's file, so I have not edited it; the correction is recorded
here and should be folded in or explicitly superseded there. The
confirmed DECISIONS are unaffected — a managed turn must be
non-interactive and pre-authorized, and an unexpected approval must
create a durable incident. Only the mechanism was misdiagnosed.

## What changed

### 1. The managed thread declares nothing; a command policy authorizes it

`tools/codex-event-bridge/src/codex_client.mjs` sends **no** `sandbox`,
`config` or `approvalPolicy` on either thread path. The capability comes
from a deployment-owned execpolicy file naming the installed executable,
the accepted config, the participant and each ruled verb.

`src/exec_policy.mjs` generates those rules, audits a policy file, and
refuses two distinct failures: verbs that are **missing**, and verbs
covered only by a **broader** rule. `EventBridge.start()` asserts it
before opening a lease, so a dispatcher whose turns would escalate on
every claim does not present itself as healthy.

Proven live, positive and negative — see Status. Three earlier shapes
were rejected on the way here (an approval policy, a writable
coordination-home root, and a narrowed version of that root); the
measurements that killed each are under "The writable-root mechanism
cannot express the boundary", which is superseded as an implementation
description and retained as evidence.

### 2. The durable incident (schema 26)

`approval_incidents` in `authority.py`, with `incident_report` and
`incident_dismiss` in `transitions.py`.

Live state and incidents are separate tables on purpose, and the
comments say why at the point of definition: `runtime_leases` answers
"what is this runner doing now" and is *meant* to be overwritten;
this answers "what broke and still needs attention" and nothing
overwrites it. Returning to `idle`, a new incarnation, a managed-stack
restart, and marking discussion seen all leave an open incident exactly
where it is.

- **Coalescing** is a database rule, not a convention the writer has to
  remember: a partial unique index over exactly the confirmed key —
  `(team, member, cause, work, episode)` `WHERE dismissed_ts IS NULL`.
  Repeated reports increment `occurrences` and `latest_ts`. The count is
  retained because "this has now happened three times" is exactly what
  says the first repair did not hold. *(Round 2 corrected this: the key
  used to include `incarnation` and `category`, which is not what the
  finding confirmed — see finding 4 below.)*
- **A new episode, or a recurrence after dismissal, is a NEW incident.**
  A dismissed problem must never reappear inside a row the operator has
  already answered.
- **No owner, no incident, and the reporter does not choose one.** The
  owner comes from the live lease and nowhere else; an ownerless runner
  is refused with a message saying why. *(Round 2 removed an
  `action-owner=` override — see finding 3.)*
- **Nothing unsafe is storable.** What travels is a closed `category`
  (`baton-cli | shell | file-write | network | mcp | patch | other`) and
  a length-bounded adapter-authored `detail`. There is no column for a
  command, argv, an environment or a payload, and a test asserts that.

### 3. Correlation rides beside the key, never parsed out of it

`docs/EFFECTIVE-BATON.md` is explicit that an `action_key` is delivered
whole and never parsed. The readiness event's action block carried only
`{participant, key}`, so a consumer had no legitimate way to learn the
Work — which is why the original reports "lacked Work and episode
correlation". The producer now sends `work` and `episode` **beside** the
key (`codex_baton_bridge.mjs`), `event_types.mjs` normalizes them as
optional, and the dispatcher reads the in-flight turn's episode when it
files the incident.

Optional deliberately: a producer at an older build sends neither, and
an uncorrelated incident is worth less than a correlated one and far
more than a dropped readiness event. Both cases are tested.

### 4. `[Inbox*]` and dismissal

`projection.incidents()` plus sticky Inbox rows for the action owner,
and `incidents` / `incident` / `dismiss` in the CLI grammar.

In the console the row's `Do` cell reads **`dismiss`**, and the detail
block states the boundary in words: who failed, the category, the count
if it recurred, that the Work was **not** claimed and dismissing does
not pick it up, and that the fix is to repair the deployment/rule
mismatch or reroute. Pressing `s` on an incident says plainly that
marking discussion seen is not how an operational incident is answered.

**There is no approve anywhere** — not in the grammar, not on the row,
not in the detail. Offering one would rebuild the interactive path one
console away from the dispatcher that refuses it. A test asserts the
word's absence from the rendered surface.

Dismissal is the action owner's, compare-and-swapped, journaled, and
**mutates no Work** — asserted by snapshotting the whole `work` table
across a dismissal.

## Tests

New `tests/work/test_w415_approval_incidents.py` — 26 tests covering
correlation, the closed vocabularies, ownerless refusal, coalescing, a
new episode, survival across idle / restart / mark-seen, owner-only
dismissal, double dismissal, recurrence after dismissal, no-Work-mutation
on both file and dismiss, secret-safe storage and projection, retry
replay, and the console cells/detail/`[Inbox*]` marker.

Seven new dispatcher tests: both thread paths declare the policy, a
server-reported `on-request`/`untrusted`/absent policy is refused on
both paths, resume re-declares, the denial files a durable incident
*beside* the transient state, no command body/argv/env reaches the
incident, correlation from the in-flight turn, the uncorrelated
fallback, and the method→category mapping.

### Three existing tests I edited — please check this judgement

`AGENTS.md` requires case-specific confirmation to change an existing
test's expectations. I judged all three to be *extensions* of what the
test already pinned rather than weakenings, but they are yours to
confirm:

1. `test/codex_client.test.mjs` — the `deepEqual` on `thread/start` and
   `thread/resume` params now includes `approvalPolicy: "never"`. Still
   an exact-operand assertion; the added operand is the behaviour this
   Work introduces.
2. `test/stale_episode.test.mjs` — the `deepEqual` on the action block
   now includes `work` and `episode`. Same shape of change.
3. The three schema-version pins (`25` → `26`), each annotated with the
   finding that moved it, following the existing convention in those
   files.

I also **completed fixtures** rather than changing assertions in three
places: the fake app-servers omitted `approvalPolicy`, which the real
`ThreadStartResponse`/`ThreadResumeResponse` mark **required**, and two
fake runtime publishers lacked the new `incident` method.

## Acceptance boundary

| Requirement | Where |
| --- | --- |
| managed turn performs canonical Baton ops without an interactive approval request or a broad shell allowance | `approvalPolicy: "never"` declared and verified on both thread paths |
| any other command still fails closed; the dispatcher never approves | `never` denies internally; W3243's deny path intact and still tested |
| an unexpected approval produces both the transient transition and one durable Work-correlated incident | `event_bridge.mjs` files both; "beside the state" test |
| the incident survives idle, refresh and restart until dismissal | three survival tests |
| `[Inbox*]` attracts attention and the details explain the remediation boundary | Inbox rows, `Do: dismiss`, detail block, owed-marker test |
| dismissal is authoritative, journaled, and mutates no Work | `incident_dismiss` + work-table snapshot tests |
| regressions cover allowed path, refusal, correlation, coalescing, restart, dismissal, secret-safe rendering | 26 Python + 7 dispatcher tests |

## The writable-root mechanism cannot express the boundary

**SUPERSEDED 2026-08-20 (round 4).** The writable-root proposal below is
NOT the implementation. The approver rejected per-thread overrides and
ruled for a deployment-owned exact command policy; see Status and the
round-4 response. This section is retained because its measurements are
why that ruling is right, and because the next reader needs to know
which mechanisms were tried and what each one actually did. Nothing in
it describes current behaviour.

Review round 2 said the writable coordination-home root is a broad shell
capability and asked for the missing negative control. I ran it against
a live app-server, with a scratch directory standing in for a
coordination home.

**Control 1 — the whole directory as the root.** Granted
`writable_roots: ["<home>"]`, then asked the turn to append to
`work.sqlite3` and to `baton.json`:

```
granted: ["/tmp/w415-probe/home"]
approvals requested: []
work.sqlite3 : "AUTHORITY\nx\n"
baton.json   : "{}\ny\n"
```

Both writes succeeded, with **no approval request**. The reviewer's
control fails exactly as predicted: any shell command in a managed turn
can rewrite or delete the authority and its configuration.

**Control 2 — can it be narrowed?** Granted only the database file, then
the same two writes:

```
granted: ["/tmp/w415-probe/home/work.sqlite3"]
approvals requested: []
work.sqlite3 : "AUTHORITY\n"
baton.json   : "{}\n"
```

Neither write succeeded. A file or glob root is **echoed back by the
app-server and grants nothing at all** — not even the file it names.

So `sandbox_workspace_write.writable_roots` expresses "that whole
directory" or "nothing". The confirmed boundary — canonical Baton
operations pre-authorized, the authority never mutated directly — is
neither, and no configuration of this mechanism reaches it. The reviewer
is right, and the reason is stronger than the review states: this is not
a case of choosing a narrower root.

### What I did instead, and what it does not close

Two rules, enforced at configuration time, encoding the only boundary
the mechanism can carry:

1. the grant must reach the **authority database**, named explicitly as
   `roleInstructions.authorityDatabase` — otherwise a deployment
   validates clean and still escalates on every write, which is the
   original defect wearing a passing test;
2. the grant must **not** contain `baton.json` — a root holding the
   coordination home is general filesystem authority over the store.

Together they mean the grant is narrow *by layout*: the database has to
live in a directory that holds nothing else. `/` and the home directory
are refused outright. Regressions cover all of it, and both shipped
config surfaces show the safe layout with the reasoning in band.

**This is a real narrowing and it is not the approved boundary.** A
shell command in the turn can still write or delete `work.sqlite3`
itself. `baton.json`, logs and runtime state are out of reach; the store
is not. I am not going to describe that as satisfying "agents never
mutate the SQLite authority directly", because it does not.

### The mediated capability, and the ruling I need

The reviewer's own alternative is the answer: a mediated Baton
capability, so the sandbox grants **no** write access and the model
reaches Baton through a tool rather than a shell.

I verified the mechanism exists rather than proposing it blind:
`mcp_servers` is a live Codex configuration key (32 references in the
shipped binary), and `thread/start` accepts arbitrary `config`
overrides, so a dispatcher-configured stdio MCP server exposing exactly
`claim`, `say`, `pass` and `close` — the four verbs the acceptance text
names — is reachable from here. It runs as its own process outside the
command sandbox, holds the participant identity, and cannot be turned
into a general Baton proxy.

That is a new component with its own contract, tests and live proof. It
is the correct fix and it is beyond what this Work's plan describes, so
I am asking for the ruling rather than inventing the scope at the end of
a review round: **build the mediated capability inside W415, or split it
into its own Work and park W415's execution boundary until it lands?**
Either way the layout-narrowed grant above should not be deployed as
though it were the approved boundary.

## Response to review 2026-08-20T21:11:52Z


Findings 1 and its consequences are above. The other three:

### 2 (P1) — shipped and live targets had no action owner — **fixed, fails closed**

Confirmed: `actionOwner` was optional, absent from
`conf/codex-event-bridge.template.json` and
`tools/codex-event-bridge/config.example.json`, and null on the live
reviewer lease. So the deployment that produced this defect could not
have raised the incident the patch promises.

`identity.actionOwner` is now **required on every managed target** —
validation refuses the whole configuration, so the stack does not start.
The reviewer's reasoning is why it is not a warning: a warning in a
background log recreates the original invisibility. Both shipped
surfaces carry it, and `roleInstructions.writableRoots` alongside.

Verified: the live deployment config is now refused (see Status). A
regression asserts both refusals.

### 3 (P1) — a stale runner could file, and choose another owner — **fixed**

Confirmed on both halves.

`incident_report` now gates on the exact live incarnation through
`_runtime_gate`, like every other runtime write. A superseded runner
filing with a stale incarnation is refused instead of borrowing the
current runner's adapter, session and owner — which would have made a
replaced publisher authoritative over the one that replaced it.

The `action-owner=` operand is **removed** from the transition and from
the grammar. It let any configured participant plant a sticky owed
action in any other member's Inbox through a verb carrying no such
authority, and it contradicted the confirmed configured-action-owner
boundary. The owner is derived from the gated lease. An administrative
override may be worth having; the reviewer is right that it needs its
own ruled authority model rather than riding the runner's own report,
and this Work does not invent one.

Regressions: the owner is the lease's and the operand is gone from the
grammar; a superseded runner cannot file; a runner with no lease cannot
file.

### 4 (P2) — restart occurrences split instead of coalescing — **fixed**

Confirmed. The index and lookup included `incarnation` and `category`,
so a managed-stack restart opened a second incident for the same
still-unclaimed episode. That is backwards: a problem that survives a
restart is the same problem, harder.

The key is now exactly the confirmed decision's —
participant, Work episode, cause. Incarnation, adapter and session stay
on the row as **evidence** and advance to the most recent report, so an
operator sees where it is happening now rather than where it started.

Regression: restart-then-repeat coalesces to one incident with
`occurrences: 2` and `incarnation: run-2`. One of my own round-1 tests
asserted the old behaviour (a different `category` opening a rival
incident) and was corrected to the confirmed contract.

## Open for the reviewer

1. **The two blocking operator consequences in Status** — the refused
   live configuration and the schema bump.
2. **`FINDING.md`'s "Observed" section is wrong about the mechanism.**
   Reads ran fine; only writes escalated, because the coordination home
   is outside the sandbox's writable roots. The confirmed decisions
   still hold. It is your file; it needs folding in or an explicit
   supersession.
3. **The live proof spends a real model turn** and is therefore outside
   the gate, under `npm run test:managed-write`. It runs against a
   disposable authority in `/tmp` and never touches production. I did
   **not** restart the managed stack to prove it in situ — that stack is
   serving this conversation.
4. **Assertion extensions**, same category you accepted last round: the
   `thread/start`/`resume` operand assertions now pin the sandbox
   operands instead of the approval policy, and one resume-options
   assertion gained `writableRoots`. Fixtures gained the newly required
   `writableRoots`/`actionOwner`; no assertion was weakened.
5. **The execpolicy rules file remains 147 accumulated entries.** Round
   1 flagged it as possibly deserving its own finding. Round 2's
   evidence downgrades it further: it was never implicated in this
   defect at all. It still governs interactive sessions.

## Response to review 2026-08-20T23:26:46Z (round 3)

- **P1a — broad writable root.** NOT fixed; measured and escalated
  above. The control fails, and the mechanism cannot be narrowed.
- **P1b — validation of the effective boundary.** Fixed. The two rules
  above replace "a root exists" with "the grant reaches the authority
  and misses its configuration", plus outright refusal of `/` and the
  home directory. `roleInstructions.authorityDatabase` is explicit and
  never inferred from the config path, because inferring it is what
  would have hidden the layout conflict.
- **P2a — replayed operation id.** Fixed. The publisher now mints one
  operation id per OBSERVED approval, retained across retries of that
  publication, so transport retry and a new occurrence stay
  distinguishable. An adapter regression proves two same-category
  observations publish twice with different ids and identical operands;
  the authority half already proves those coalesce to one incident with
  an advancing count.
- **P2b — the proof was not wired and defaulted to a retired binary.**
  Fixed. `npm run test:managed-write` exists, and the candidate
  executable is required as an explicit operand or
  `W415_CANDIDATE_BATON`; there is no default, so a green result is
  evidence about the build under review.
- **Additional observation — owner on coalesce.** Ruled and tested: the
  owner **moves** to the current gated lease. `action_owner` is a
  configuration fact about who answers for this runner; if a
  redeployment changed it, an incident still owed to the former
  participant is owed to nobody who can act, which is the invisibility
  this Work exists to remove.

## Response to review 2026-08-20T23:42:34Z and the superseding ruling (round 4)

The review recommended a mediated MCP capability and a child Work. The
approver ruled otherwise — no arbitrary per-thread overrides, and a
deployment-owned exact command policy instead — and `PLAN.md` records
that as superseding the recommendation. This round implements the
ruling.

### What was removed

Every per-thread override. `codex_client.mjs` sends no `sandbox`, no
`config` and no `approvalPolicy`; `writableRoots` and
`authorityDatabase` are gone from the configuration, the shipped
template, the example, the CLI and the bridge. A regression asserts that
neither thread path sends any of them.

### What replaces it

`src/exec_policy.mjs`, and it does three things:

1. **Generates** the exact rules a deployment installs — one per ruled
   verb, each naming the installed executable, the accepted config, the
   participant and that verb. `claim` does not also authorize `regen`.
2. **Audits** a policy file, distinguishing *missing* from *broad*. A
   rule naming the executable alone technically covers every ruled verb
   and is reported as broad, never as coverage — accepting it would be
   the same substitution of a broad capability for a narrow one that
   this Work has now rejected in four different costumes.
3. **Refuses.** `EventBridge.start()` asserts the policy before opening
   a single lease. A dispatcher whose turns escalate on every claim is
   the defect this Work records; it must not report itself healthy while
   in that state.

It never writes the rules. The operator installs them.

### Why command policy and not the filesystem, in one line

Measured, not argued: a directory grant let an unrelated command rewrite
`baton.json`; a file or glob grant granted nothing at all; and command
policy authorized the ruled verb while refusing an unrelated write to
the same file. Only the third is narrow.

### A trap worth recording

Both halves of the live proof were initially confounded by placing the
disposable authority under `/tmp`, which the default sandbox profile
already grants write to. That first run showed the ruled operation
succeeding *and* the unrelated write succeeding, which reads as "command
policy is not narrow" and is simply wrong. Moving the authority outside
`/tmp` — where a real coordination home lives — produced the true
result. The smoke test now places it there deliberately and says why, so
nobody has to rediscover it.

### Two more corrections proposed to W2

17. **Capability contracts must name the mechanism class.** Three of the
    four rejected fixes here failed for one reason: a filesystem grant
    cannot express an operation capability. v12 should state what
    authority a managed worker gets *as a command policy*, not as a
    path.
18. **A dispatcher must refuse to start when its workers cannot act.**
    Reporting healthy while every canonical operation escalates is the
    original defect at the process level rather than the turn level.

## Response to review 2026-08-21T00:29:00Z (round 5)

### 1 (P1) — the proof used the broad rule — **fixed, and the claim narrowed**

Confirmed; I had disclosed it, and disclosure is not evidence. The new
`smoke/exact_policy_matrix.mjs` stands up an app-server with an isolated
`CODEX_HOME` whose policy contains **only** the four generated exact
rules — no broad rule for any executable — and drives the full confirmed
matrix through it. Results above: the exact ruled operation commits with
no approval request, and a shell wrapper, a wrong participant, a wrong
config, an unlisted Baton verb, a direct authority write, a direct
config write, and an unrelated command all fail closed.

The authority deliberately lives **outside `/tmp`**, because the default
sandbox profile grants write there and every negative case would
otherwise pass for the wrong reason. That trap has now caught me twice
in this Work; it is written into the file so it does not catch a third
person.

**And the audit's claim is narrowed, which was the sharper half of the
finding.** `auditRules` reads one file the deployment nominates. It
cannot observe the complete policy the app-server loaded — Codex may
read other sources, and a deployment could nominate a pristine file
while the server enforces something else. So it is now described
everywhere, including in its refusal messages, as a deployment
**preflight** on the nominated file. The effective boundary is
established by the live matrix, and only by it.

### 2 (P1) — `mark-seen` widened the ruled capability — **removed**

Confirmed, and the review is right about the shape of the error, not
just the fact of it: I added a fifth mutating verb on my own judgement
that a reviewer turn needs it, and an implementer does not widen a ruled
capability while implementing it. `RULED_VERBS` is back to exactly
`claim`, `say`, `pass`, `close`. If `mark-seen` belongs in the set, that
is a ruling to obtain and pin.

The test was wrong in the same way and is fixed: it asserted that every
member of *the implementation's own list* generated a rule, which cannot
catch the list growing. It now asserts the approved four literally, and
that `regen`, `release`, `mark-seen` and `phase` have no rule.

### 3 (P2) — stale writable-root vocabulary in the smoke — **removed**

Confirmed. The proof still passed `writableRoots: [home]` — silently
ignored since the override was removed — and its comments described the
superseded mechanism, so the source told the next reader the opposite of
what the run showed. The operand is gone, the comments say the
capability comes from command policy, and the empty grant is now
**asserted** rather than merely printed: a granted root would make the
committed operation prove nothing.

### One thing I got wrong in this round

The matrix's first run left a `thread-writer-locks/` directory behind: I
killed the app-server and removed its home immediately, so the shutting
-down server recreated files underneath the removal. That is exactly the
cleanup-before-proven-termination mistake W76's reviews caught twice,
committed a third time in a new place. Teardown now waits for the server
to exit, and asserts the whole staging area is gone rather than just the
credential. The matrix was rerun and is clean.

### Two more corrections proposed to W2

19. **A capability audit must say what it measured.** A check over a
    nominated configuration file is a preflight; only exercising the
    boundary measures it. v12 should not let a green preflight be
    reported as a verified boundary.
20. **A ruled capability set is data, not code.** Tests that assert
    "every verb in the implementation's list has a rule" cannot detect
    the list growing. The approved set belongs in the test as a literal.

## Response to review 2026-08-21T00:46:33Z (round 6)

### P1 — exact-plus-broad was reported as satisfied — **fixed**

Reproduced exactly as written, against the returned tree:

```
exact + broad -> {"missing":[],"broad":0,"satisfied":true}
```

`auditRules` recorded `broad` only when a ruled command had **no** exact
covering rule. With both present every ruled command had an exact rule,
`broad` stayed empty, and the preflight passed — while the broad rule
still authorized every verb the participant can reach.

The reviewer's framing is the part worth keeping: this is *the most
likely deployment transition*. An operator installs the four generated
rules and forgets to delete the retired one, and that half-finished
state was the single state the check was blindest to.

Now every broader covering rule is reported, whether or not an exact
rule covers the same command — because a narrow rule does not cancel a
broad one; both are simply present. The refusal says so explicitly when
the exact rules are also there:

```
… contains a BROADER rule [/opt/baton/bin/baton] covering
[claim, say, pass, close] … The exact rules are present, and a narrow
rule does not cancel a broad one — both are simply there. REMOVE the
broad rule; this is the half-finished upgrade state.
```

Two broad shapes are covered: the executable-only rule, and a rule at
the executable/config/participant prefix that names no verb. Exact-only
still succeeds and broad-only still refuses with the install
instructions — the correction must not make the approved state
unreachable, and a regression pins that.

### One addition, flagged for your decision

While fixing this I noticed an adjacent gap the finding's boundary also
covers: an allow rule naming this exact executable, config and
participant but an **unruled verb** — say `regen` — is extra capability,
and nothing detected it.

`auditRules` now reports those as `extra`. I did **not** make it a
refusal, deliberately. Refusing would need a list of Baton's mutating
verbs maintained inside the bridge, which would drift from the real
grammar, and refusing a *read* verb would be wrong. So it is surfaced
for an operator rather than enforced, and the enforcement question is
yours: if unruled-verb rules should fail the preflight, that needs a
rule for distinguishing mutating from read verbs that does not duplicate
Baton's grammar.

This is reported rather than assumed because the last round's lesson was
that an implementer does not widen — or narrow — a ruled boundary on
their own judgement.

### One more correction proposed to W2

23. **A capability audit must consider the whole policy, not the best
    match.** Finding an exact rule and stopping is how a broad rule
    survives an upgrade. v12's conformance contract should require that
    every rule covering a ruled operation is classified, not just the
    narrowest one.

## The Exact-set clarification, implemented (round 7)

Round 6 left unruled-verb rules as an advisory `extra` and asked for a
ruling. It is now pinned in `FINDING.md` under "Exact-set clarification
— 2026-08-20", and delivered as poke 1178:

> the nominated participant policy is the exact approved set, not merely
> a file that happens to contain that set. An allow rule for the same
> executable, config, and participant but any other Baton verb makes the
> preflight fail. The bridge does not need a second list of Baton's
> mutating verbs: read-only commands need no sandbox-crossing allow
> rule, and the nominated deployment policy is deliberately dedicated to
> these four managed mutations. Exact rules for other configured
> participants remain independent and valid.

**That dissolves the objection I raised.** I had left it advisory
because refusing looked like it required a mutating-vs-read verb list
maintained inside the bridge, which would drift from Baton's grammar.
The ruling removes the need for one: a read verb needs no allow rule
here at all, so anything in this file outside the four is extra
capability regardless of what it does.

`extra` is now a refusal alongside `missing` and `broad`, and
`satisfied` requires all three empty. The message names the offending
verbs, states the approved set, and says read-only commands need no rule
here — so an operator is not left guessing why their `detail` rule was
rejected.

Verified across the ruling's full shape:

| policy | verdict |
| --- | --- |
| the four exact rules only | accepted |
| + `regen` / `mark-seen` / `release` / `phase` / `detail` for this participant | **refused** |
| + another participant's exact rules | accepted |
| + another participant's `regen` | accepted |

The last two matter as much as the refusals: this only ever inspects
this participant's own prefix, so other configured participants stay
independent, exactly as ruled.

### A note on how this arrived

The ruling came as a poke while `W415` was routed to `baton.bug`. My
first read of the route said so and I was composing a "reroute it to me"
answer; a re-read immediately before acting showed it had already moved
to `baton.impl`. `docs/EFFECTIVE-BATON.md`'s rule that a readiness
observation is an edge to re-evaluate rather than authority is what
caught that, and it is worth recording that the rule earned its keep on
a five-second-old read.

### One more correction proposed to W2

24. **A dedicated policy file is an allowlist, not a container.** "The
    approved rules are present" and "only the approved rules are
    present" are different properties, and a capability contract has to
    say which one it means. v12 should state that a nominated policy is
    exhaustive for the participant it names.
