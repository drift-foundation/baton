# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — claimed and implemented

Claimed W28681 at seq 29646. Read the thread, the finding, the plan and the
reviewer research, then revalidated every pinned claim against the tree before
acting on it.

### Revalidation

The reviewer's code boundary still holds exactly as recorded.
`AcpAgentSession.setup` spawns with no descendant-owning domain; `promptText`
raced only the prompt against the agent's death; `stop()` signalled the direct
child alone; `runBridge` retained a healthy session across turns, so a
persistent process accumulated tool children no later turn could attribute or
destroy; and the shipped launcher passed mount bindings only. The approver
ruling of 2026-08-28 approved the proposed boundary in full, so what follows
implements it rather than re-deciding it.

### The three parts of the boundary

**The deadline is mandatory and has no default.** That is the one design point
I would most want a reviewer to look at, because every other timeout in this
program has a default. A wrong default elsewhere is merely slow; a wrong
default here either kills legitimate long work or leaves this defect open, and
neither is a choice a repository may make for a deployment. An absent value is
a deployment that has not decided how long its only delivery lane may be held,
and it does not start.

It is WALL-CLOCK rather than an activity reset, and the matrix drives why: a
fake agent that is hung AND emitting session updates every 20ms still reaches
its deadline. An activity-reset watchdog would have kept the incident's turn
alive forever.

**One domain per delivered turn, destroyed before anything is settled.** A
prompt that returned says the model stopped talking; it says nothing about
what its tools left running. So the teardown runs before `idle` on success and
before `failed` on failure, and the ordering is asserted by recording what had
been published at the moment teardown was entered. The next delivery builds a
fresh process that resumes the retained ACP session id — session continuity is
not process continuity, which is what makes the per-turn domain legal without
touching any rotation rule.

**Teardown is proved, and an unprovable one fences the lane.** The previous
`stop()` awaited the child's exit after SIGKILL with NO bound: a child in
uninterruptible sleep would have hung the bridge inside its own recovery,
which is the same shape as the defect one layer down. It is now bounded, and a
domain that cannot be shown to have exited raises rather than returns. The
caller then publishes correlated `failed`/`internal`, retains the readiness
key, publishes no `idle`, starts no replacement, and ends the run.

### What the bridge cannot check, and who does

The kernel boundary is the launcher's, not the bridge's. A `setsid` call
escapes a process group and a session and does not escape a PID namespace, so
the shipped launcher now passes `--unshare-pid` (bubblewrap becomes the
namespace's PID 1 reaper) and `--die-with-parent` beside its existing mount
bindings.

The bridge deliberately does not parse `agent.command` — it is ACP-generic and
that rule is load-bearing — so it cannot refuse a mount-only launcher. The one
place that can is the deployment's own staged-set verifier, and `verify.mjs`
now refuses a launcher missing either flag and requires the preflight to ship
beside it. Putting that check in the bridge would have meant the bridge
understanding one deployment's command vocabulary, which is the thing this
program is built not to do.

### What I could not establish, reported rather than worked around

`preflight-process-domain.sh` refuses from this managed turn:

```text
bwrap: No permissions to create new namespace, likely because the kernel does
not allow non-privileged user namespaces.
exit 3
```

That is the same refusal the reviewer's probe got, and it neither proves nor
disproves host support — a nested sandbox cannot certify the launch context.
The script is written to refuse rather than pass vacuously, and running it in
the SERVICE launch context before installing the changed launcher is an
operator step named in PLAN.md. Installing the staged set at all is INSTALL.md
cutover work, not something a turn performs.

The real-descendant regression is written the same way. It asserts
unconditionally what is portable — the domain owner is gone, by the exit the
bridge waited for — and REPORTS, as a test diagnostic, that this environment
gave the agent no PID namespace so a `setsid` descendant survived. A case that
passed silently there would be claiming a boundary it never crossed; the
diagnostic names the missing half and points at the preflight.

### Gates

- `tools/acp-baton-bridge` — **87 tests, 87 pass** (was 77; ten added)
- `tools/codex-event-bridge` — 419 tests, 419 pass, unaffected
- the staged deployment set's own `verify.mjs` — passes, and now reports the
  process domain and the configured turn deadline
- that set's `verify.py` — FAILS, and it failed before this Work touched
  anything. It compares the staged `infra.json` against the LIVE installed one,
  and the two now name different Baton candidates: staged `14aecfb`, live
  `dd1dc3e`. That is the pre-cutover comparison INSTALL.md already says stops
  holding once the stack is installed and the candidate moves. I changed no
  `infra.json`, and the divergence is one field with no relation to the tool
  lifetime. Reported rather than repaired: rebasing another record's successor
  set onto a newer candidate is that record's work, not this one's.
- `preflight-process-domain.sh` — refuses from this context, exit 3, as
  described above

No version-control history or index was mutated. Awaiting independent review.

### For review

- The v11 half is complete; the v12 half is recorded in W6636's `FINDING.md`
  and deliberately NOT implemented here. W6636 owns the destroy/settlement
  crossing, and implementing it from this Work would give one rule two owners.
- `TERM_GRACE_MS` (500) and `KILL_PROOF_MS` (5000) are constants of this
  supervisor rather than a fifth operator-facing timeout. That is my judgement
  and is the kind of thing worth disagreeing with: the argument is that they
  describe how long THIS component waits for a signal it sent, not anything
  about a deployment's workload.
- The five stale process groups the finding named are gone, but by an unknown
  external mechanism observed during reviewer research — not by anything this
  Work did and not by anything that establishes a lifecycle guarantee. Nothing
  here claims that recovery; the acceptance's "exact scoped recovery" clause is
  satisfied by the launcher domain making such groups impossible to create
  rather than by a reaper this Work does not add.

## 2026-08-28 - the reviewed findings, corrected

Reclaimed W28681 at seq 29864. Every one of the five findings is real and four
of them are defects I introduced; the fifth is a fixture that proved less than
it claimed. Reproduced each before touching anything.

### [P0] My own comments made the launcher gate vacuous

The check searched free text for the two flags, and the launcher's explanatory
comments -- which I wrote, and which name both flags repeatedly -- satisfied
it. Removing them from the executable ARGS line left both predicates true:

```text
functional flags removed from ARGS; free-text predicates still say: [True, True]
```

That is the worst kind of gate: the one enforcer the design assigns, admitting
exactly what it exists to refuse, while reading green. The correction RUNS the
staged launcher against a recording stand-in for bwrap and reads the argv it
actually composed -- both flags present, both before the agent executable (a
bubblewrap option after the command is an argument to the command), and the
read-only bind still there. Prose cannot satisfy it.

And it proves its own reachability on every run: a copy with the ARGS line
gutted and every comment kept must be refused, and the probe first checks both
flag names still appear in that copy -- otherwise it would pass a free-text
check too and would be proving nothing. Measured:

```text
exit 1  the composed launch does not pass --unshare-pid
```

### [P0] The procedure could not install what the template required

I added the preflight to the template's required policy resources and never
touched INSTALL.md. Following the documented cutover would have installed a
configuration the bridge refuses to start on a missing resource -- discovered
by an operator mid-cutover, which is exactly where it costs most.

INSTALL.md now installs it in both the fresh path and the reconciliation path,
byte-compares it and the launcher, backs the launcher up before overwriting it,
restores it and removes the preflight on both rollbacks, and carries a
mandatory service-context process-domain section whose nonzero result keeps
dispatch paused.

I also made the class of defect non-recurring: verify.mjs refuses a staged set
where any template-required policy resource is missing from the staged
directory or has no INSTALL COMMAND whose destination is that path.

**And I got that check wrong the first time in the same way.** My first version
searched for the path as text, which a byte-comparison line or a rollback
removal satisfies. It now matches an actual install command by destination. My
first reachability probe was also wrong -- it removed one of the two install
lines and the gate correctly still passed. Removing every satisfying line is
what makes the probe honest:

```text
no install command anywhere -> exit 1
INSTALL.md has no install command whose destination is .../preflight-process-domain.sh
```

### [P1] The preflight proved numbering, not reaping

It ran a pid echo inside bubblewrap and accepted 1 or 2. That establishes a
namespace exists and says nothing about the acceptance invariant -- that
killing the domain owner removes a setsid descendant. The incident's four
surviving shells had each called setsid; a probe that never makes one is not
evidence about them.

It now runs the trial: an escaped (setsid) descendant and a busy descendant
inside the domain, an unrelated process of the same shape outside it, the owner
terminated and awaited, and then both descendants required absent while the
control survives. Typed exit codes name which half failed. It matches its own
processes with a bracketed first character so the matcher cannot match itself
-- which is not decoration, it is the exact mechanism that left four polling
shells running for 36 hours.

**And I proved the trial can fail for the right reason**, since it cannot pass
here. Running the same trial with a plain shell as the owner -- a mount-only
launcher, in other words -- gives:

```text
exit 6  the setsid descendant and busy descendant survived the domain owner's
        exit; this context creates a namespace that does not reap
```

That is the false positive the reviewer warned about, detected. From this
managed turn the real probe still refuses with exit 3, and it cleans up
everything it started.

### [P1] A valid deadline could become its opposite

Validation accepted every positive safe integer, and a Node timer interval is a
signed 32-bit millisecond value: 2147483648 validated and then ran as ONE
millisecond. The longest deadline an operator can express became the shortest
there is, silently.

Refused rather than clamped. Clamping would substitute this repository's number
for the operator's, which is the whole reason the operand has no default; and
chaining short timers would be this program inventing a scheduler to make an
unreasonable value work. Both boundary values are driven, and the case measures
the runtime's own truncation rather than trusting the constant I pinned -- if a
later runtime stops truncating there, the case says so instead of quietly
guarding the wrong number.

### [P1] The chatty fixture was not chatty

Its tool_call_update was missing toolCallId, its one required member, so the
SDK refused every update and none reached the bridge. The case reached its
deadline over a SILENT agent and therefore proved the timer works and nothing
about whether real streamed activity extends it -- which was its only job.

The fixture now emits valid updates and logs each acceptance and each refusal.
The case requires zero refusals, at least two beats, at least one update
reaching the bridge's handler, and only then the same deadline outcome.

### Gates

- tools/acp-baton-bridge -- **88 tests, 88 pass** (one added)
- tools/codex-event-bridge -- 419/419, unaffected
- staged verify.mjs -- passes, and both of its new gates were driven to failure
  and back
- preflight-process-domain.sh -- exit 3 here, and exit 6 with the domain
  removed, which is the evidence that it can fail for the right reason
- the repository whitespace check -- clean

### The one thing that is still not done, and cannot be done from here

The service-context descendant teardown trial. The strengthened preflight IS
that trial, and this managed turn refuses with exit 3 because it cannot create
a namespace. The reviewer is right that a green suite here cannot substitute
for it, and I am not claiming otherwise: acceptance needs an operator to run
that script where the service starts and record the result.

No version-control history or index was mutated.

## 2026-08-28 - the second review, corrected

Reclaimed W28681 at seq 30135. Three findings, and the P0 is the same mistake
the incident itself was about -- made by me, in the correction for it.

### [P0] The gate passed a launcher that started nothing

My descendant-reaping preflight identified its two descendants with pgrep
tokens. Those tokens sit inside the shell program passed as an ARGUMENT to
bubblewrap, so the OWNER'S OWN ARGV satisfied both "the descendant started"
checks -- and when the owner exited, the tokens went with it and the script
called that reaping. Reproduced with the reviewer's stand-in, a bwrap whose
entire body is a sleep:

    preflight-process-domain: ok -- this context creates a PID namespace,
    reaps both an escaped (setsid) and a busy descendant ...
    exit 0

I had written a comment in that script congratulating itself on bracketing the
pattern so the matcher could not match itself. Bracketing stops the MATCHER
matching itself. It does nothing about the OWNER carrying the token, which is
the leak that was actually there -- and self-matching predicates are exactly
what left four polling shells running for 36 hours in the incident this Work
exists to close. I reproduced that class of defect while fixing it.

Nothing is proved by matching a command line any more. The descendants publish
liveness by APPENDING to their own files, which no argv can do, and their
exact host-visible pids are read out of the process tree below the owner --
required alive before termination and absent afterwards, with the files
required to stop growing as an independent second statement. The control
process outside the domain is started by the script itself, so its pid is
known rather than matched.

Measured three ways, since it cannot pass in this context:

  exit 4  the reviewer's sleeping stand-in: no descendants ever ran
  exit 3  real bwrap here: no namespace, as before
  exit 6  a stand-in that starts the descendants but owns nothing: it names
          the exact host pids that survived

And the reviewer's stand-in is now a GATE rather than a one-off: verify.mjs
runs the staged preflight against it on every invocation and requires a
refusal. That needs no namespace, so the mandatory gate's own non-vacuity is
checked wherever the verifier runs.

### [P1] The fresh rollback restored a backup only the other path made

Section 6 restored a launcher backup that only section 7 created, so a failed
mandatory preflight on the documented fresh path reached a rollback command
that fails before restoring anything. The fresh path now backs the launcher up
before overwriting it, guarded because a genuinely fresh install has none, and
both rollbacks are guarded symmetrically with the absent-backup case defined:
remove the launcher this cutover installed rather than leave it behind.

verify.mjs now establishes that every backup a rollback restores is PRODUCED
ON THAT SAME PATH, holding the fresh sections apart from the reconciliation.
Finding an install command somewhere in the document was the free-text mistake
one level up, and I had already made it once in this Work.

### [P1] A failure could name the preceding action's episode

`correlation` was declared per envelope and set only after the session was
established, so after one delivered action a later one failing during
revalidation or replacement setup published the FIRST action's work, episode
and session. Before this Work those failures were uncorrelated; my merge
turned a stale local into affirmative but false operator evidence, which is
worse than none. It is reset per action now.

**The regression took three attempts and I measured every one.** The first
used two envelopes -- and `correlation` was per envelope, so it passed against
the broken source. The second used two Work actions in one envelope, and the
second Work never delivers because it waits behind the first's claim slot. The
third pairs a Work action with a POKE, which delivers beside Work and carries
no work or episode of its own, so anything it publishes came from somewhere
else. Only that version fails against the pre-fix source:

    AssertionError: a failure named a Work it did not serve

A regression that passes against the defect it names is worth less than no
regression, because it reads as coverage. I ran it against the broken shape
before trusting it, which is the only reason the first two versions did not
ship.

### Gates

- tools/acp-baton-bridge -- 89 tests, 89 pass (one added)
- tools/codex-event-bridge -- 419/419, unaffected
- staged verify.mjs -- green, and both new gates driven to failure and back
- the preflight -- exit 4, 3 and 6 as described above, cleaning up after itself
- the repository whitespace check -- clean

### Unchanged, and still the acceptance gate

The service-context run of the preflight. It cannot happen from a managed
turn, and none of the three measurements above substitutes for it.

No version-control history or index was mutated.

## 2026-08-28 - the third review, corrected

Reclaimed W28681 at seq 30367. One finding, and it is the OPPOSITE timing
defect to the one before it.

### [P1] A successful reaper was rejected

The preflight captured its heartbeat counts while both descendants were still
running, then signalled the owner, then waited for positive pid absence -- and
compared the post-teardown files to those PRE-SIGNAL counts. A descendant that
appended one last heartbeat between the count being read and the kernel
tearing it down therefore read as a process that survived. Reproduced with the
reviewer's stand-in, which runs both descendants and reaps the complete
recorded tree on SIGTERM:

    preflight-process-domain: the busy descendant is still writing after its
    domain owner exited
    exit 6

The correction is one line of ordering and a paragraph saying why. The counts
taken before teardown answer only "did they ever run". Only counts taken after
every recorded pid is proved absent can answer "have they stopped", so the
baseline moves there.

The last correction made this gate refuse a launcher that starts nothing; this
one made it refuse a launcher that reaps correctly. Both were timing mistakes
about WHEN a fact is true, in a script whose entire job is to distinguish two
instants.

### What I should have had, and now do

A gate with only a negative probe cannot see a preflight that rejects the
behaviour it exists to require. The verifier now runs the successful-reaper
stand-in as a POSITIVE gate and requires exit 0, alongside the negative one --
and the negative one now requires exit 4 SPECIFICALLY rather than any nonzero
status, because "it failed somehow" would be satisfied by a preflight that
failed for a missing tool and would stop meaning anything the day the script
grows another early exit.

Both were driven to failure and back: restoring the pre-fix baseline timing
makes the positive gate refuse with the exact message above, and a preflight
that exits 9 makes the exact-reason gate refuse.

### Four outcomes, measured

    exit 0  a launcher that runs both descendants and reaps the whole tree
    exit 4  a launcher that starts nothing
    exit 6  a launcher that starts descendants and owns none of them
    exit 3  real bwrap in this managed context: no namespace

### Gates

- tools/acp-baton-bridge -- 89/89
- tools/codex-event-bridge -- 419/419, unaffected
- staged verify.mjs -- green, with both new gates driven to failure and back
- the repository whitespace check -- clean

### Unchanged, and still the acceptance gate

The service-context run. The portable logic now accepts the successful case
and refuses both failure shapes, which is as far as a managed turn can take
it.

No version-control history or index was mutated.
