# Implementer progress — the first v12 Docker ping-pong proof

Created 2026-08-26 by `baton.claude` on claiming W17110, as the record
requires.

## The three edges the assignment ordered, installed before any code

> Before code, install dependencies on W6633 and W6634 and make W6636 depend
> on this Work.

    block work=W17110 on=W6633     -> seq 17270
    block work=W17110 on=W6634     -> seq 17271
    block work=W6636  on=W17110    -> seq 17269

Installing the first two moved this Work to `block` and released the claim in
the same act. That is the instruction's own consequence rather than a surprise:
both prerequisites are open, and the bound record already said so — "the direct
prerequisites are W6633 and W6634", with PLAN item 1 marked blocked on both.

W6636 is installed the other way round, as the assignment says: the lifecycle
composition consumes this checkpoint, so composing before the checkpoint exists
would be composing over an unproved boundary. Reviewer authority cannot mutate
impl-routed Work, so the route handler installs all three — the same handoff
shape W6629, W6634, W16821, W16823 and W16830 used.

## Why W6634 is a real gate here and not a formality

The acceptance says completion must leave **no live assignment credential**.
The surface that produces and proves that is W6634's credential lifecycle —
approver message 16691's closed logical slots, trusted-profile provider
mapping, assignment-private volatile files, the fixed read-only
`/run/baton/credentials` root, the live-bearer registry held through teardown,
and bounded orphan cleanup.

**It is unimplemented.** I reported that on W6634 minutes before claiming this,
as its largest remaining deliverable. Running this proof now would either skip
the credential half of its own acceptance or invent that surface here — the
boundary violation this campaign has already refused twice, on W6634 itself and
on W16823.

W6633 is the other half and is itself blocked: without the reference worker
image there is no container to run and nothing to prove.

## Observed, and useful when this unblocks

`docker` is on PATH in this environment, so the acceptance's "Docker absence
fails clearly" case will need to be driven deliberately rather than by
happening to run somewhere without it. Worth knowing before item 4 is written:
a proof that never exercises its own absence path is a proof that would skip
itself silently on the one machine where it mattered.

## Deliberately not done

**No revalidation of the reference-worker, input/output or credential
contracts.** PLAN item 1 asks for it and is marked blocked on the same two
Works. Those contracts are exactly what W6633 and W6634 are still changing —
W6634's own surface moved three times today — so an answer produced now
describes a tree that has not settled.

**No orchestration, no `just ping-pong`, no fixtures.** Items 2 through 4 are
downstream of a revalidation that cannot honestly happen yet.

## State

**Blocked on W6633 and W6634, unclaimed, and gating W6636.** No repository
state was mutated.

## 2026-08-27 — the real-agent trials, run to their exact boundary

Evidence: `evidence/w17110-2026-08-27-trials.txt`.
Spike code: `v12/spike/ping-pong/` — labelled SPIKE ONLY in every file.
No repository state was mutated.

Everything above this heading describes a Work blocked on W6633 and W6634 and
scoped to a deterministic worker. **All of that is superseded**, twice: first to
a tracer-bullet spike, then to real Claude and Codex runtimes in Docker.
W6633 is now closed satisfying and the W6634 edge is gone, so this ran.

### What the experiment answers

**Both provider runtimes package into Docker and start.** Claude Code 2.1.247
and codex-cli 0.150.1, installed from their published packages by exact version,
running as an unprivileged uid, reporting their versions from inside their own
containers. Neither needed a host escape, an interactive terminal, or anything
copied out of the operator's home.

**A container can reach both providers.** Asked from inside one, not inferred
from the daemon — this campaign's workers run `--network none`, so the daemon
having egress says nothing. `405` and `401` are reachability proofs: the
endpoints answered.

**The whole outer shape works, for both.** Read-only `/input` carrying one
correlation identity; a separate writable `/output`; the credential provider
mounted read-only and never copied; `output.json` published last and
atomically; host-side validation that the correlation came back; and positive
cleanup proved by asking the engine rather than by remembering. Both trials:
`correlation_matches: true`, `clean: true`, nothing surviving.

### The comparison the ruling asked for

This is the part a scripted echo worker could not have produced.

- **Claude** reads a read-only credential provider and makes an
  **authentication** decision — "Not logged in". A read-only mount at
  `$HOME/.claude` is enough for it to get that far.
- **Codex will not start** with its state directory mounted read-only:
  `failed to initialize in-process app-server client: Read-only file system`.
  It writes beside its credential while running, so the provider has to be
  mounted as a **file** over `auth.json` with the directory left writable —
  which is why `--credentials` accepts both shapes.
- **Codex also refuses a `HOME` under `/tmp`** outright: *"Refusing to create
  helper binaries under temporary dir"*. My first version gave each runtime a
  fresh `mkdtemp` home. Claude accepted it; Codex would not run at all.
- **Both need their state directory pre-created and owned in the image.**
  Docker creates a missing bind-mount parent as **root**, so a container running
  as an unprivileged uid got `Permission denied` beside its own credential
  before reaching any provider.

**This bears directly on W6634.** Its approved credential delivery materializes
assignment-private files at `0600` and mounts them **read-only** at a fixed
root. On this evidence that shape works for a Claude-like runtime and **does
not** work for a Codex-like one, and the mode has to admit the *container's*
uid rather than the host user's. That is the kind of thing the checkpoint said
this experiment was for.

### Two defects in my own harness that only a real runtime found

1. **The first Codex run hung past its own deadline.** The in-container timer
   fired and killed `codex`, but its child held the stdio pipes open, so Node's
   `close` never arrived and nothing was published — the container was still up
   ten minutes later. Now: its own process group, killed as a group; settle on
   `exit` rather than only `close`; a grace timer that settles regardless; and a
   **host-side** bound that ends the container and records a `timeout` category.
2. A trial that cannot end is worse than one that fails — the operator has
   nothing to read either way, and no reason to stop waiting.

### What is NOT proved, and the one thing blocking it

**Neither trial returned a pong.** The ruling closes this Work satisfying only
when both real agents return the correlated pong from inside their containers.

The reason is single and specific: **no credential provider has been
nominated.** `/run/baton/credentials` — the path the ruling names — does not
exist on this machine. The operator's own Claude and Codex credentials do exist,
at `~/.claude/.credentials.json` and `~/.codex/auth.json`, both `0600`.

I did not use them, and that is a decision rather than an oversight. Those are
the operator's live personal credentials for their own agent accounts; the
record nominates a different provider; and mounting live authentication into a
freshly built image with network egress is not a substitution an implementer
gets to make quietly. The ruling's own instruction is to *"preserve the exact
redacted boundary failure rather than weakening isolation"*, and choosing a
credential source nobody offered is that weakening in the one direction it did
not have to spell out.

`preflight.py` exits `3` on exactly this and says so. It reports presence, mode
and size and **never opens a credential file**.

### The question that needs answering

**Which credential provider should the trials mount?** Any of:

- create `/run/baton/credentials/{claude,codex}` with copies the operator is
  content to expose to a container, or
- nominate `~/.claude/.credentials.json` and `~/.codex/auth.json` directly —
  `trial.py --credentials <path>` takes either a file or a directory, and
  mounts it read-only, or
- decline, and let this close as the partial result it currently is.

Everything else is built and proved. The trials are one flag away.

## State

**Partial result, ready for independent review.** Packaging, isolation,
input/output exchange, correlation, host validation and cleanup are all proved
for both providers; the pong is not, for want of a nominated credential source.
The ruling anticipates exactly this: *"a partial result remains valuable
experiment evidence but is not a satisfying two-provider proof."*

## 2026-08-27 — the review's P0 and three P1s

Evidence: `evidence/w17110-2026-08-27-corrected-trials.txt`.
No repository state was mutated.

All four correct. The P0 is the important one and it is not a bug in my
redaction — it is that **a redaction was the wrong mechanism**.

### [P0] An allowlist, not a redaction

I wrote a regular expression that recognised familiar token spellings and
called the durable boundary safe. The rule is not "remove the spellings I
recognise": a real agent **holds the mounted credential** and can emit
arbitrary stdout, and a prompt asking for one word is not a non-disclosure
boundary. A heuristic over text somebody else chooses is a guess, and the
reviewer's sentinel — shaped like no known token — walked straight through it
into the host report.

Nothing is redacted now, because nothing that could carry provider text is
read. The container publishes only facts it **computed**: the identities it was
given, both exit states, a **digest** of the answer, two byte counts, and on
failure one word from a closed vocabulary. The host copies from a closed
allowlist and drops anything else — the direction matters, because a document
this program did not write is one whose extra members it cannot vouch for.

The digest is what makes that possible: the host derives `sha256("pong")` for
itself and compares, so an exact match is decidable **without the host ever
seeing what was said**.

### [P1] The verdict is the host's, recomputed

It accepted the truthiness of the document's own `pong` member, so a container
claiming `pong: true` beside the text "not pong", exiting 9, was reported
satisfying. A worker-authored success bit is a claim, and the party that has to
be convinced is the host.

Six clauses now, each decided here from a computed fact: expected spike,
expected provider, matching correlation, the provider's exit, the container's
exit, and an exact-digest answer. `"not pong"` has a different digest — which a
substring test could never have told apart.

### [P1] Cleanup is enforced rather than observed

Image removal was unchecked, so a refused `docker image rm` followed by an
empty tag lookup reported nothing surviving while the immutable image may still
be there untagged. Now the removal's own answer is read, the image is queried by
the **recorded immutable id** when removal failed, the staged root's absence is
part of the verdict instead of a fact beside it, and the timeout path's kill and
removal both report their status.

### [P1] Present is not the same fact as readable

Both images run as `65532:65532`. A bind mount preserves host ownership rather
than translating it, so the operator's `0600` files owned by uid 1000 are
credentials the container **cannot open**, however correctly they are mounted.
My "one flag away" framing was wrong about that, and the reviewer was right to
stop it.

Preflight now reports `readable_by_container_uid` beside presence, decided from
mode and ownership with every ancestor's traversal bit checked — and still opens
nothing. Controlled in both directions: a world-readable file under a
traversable directory is readable; an owner-only file is not; a readable file
under a `0700` directory is not.

I did not nominate or mount those personal files, on this claim or any other.

### Both trials re-run under the corrected harness

Unchanged where it matters and better where it counts: read-only input, one
correlation identity carried through, `output.json` published last, a
host-recomputed verdict, enforced cleanup, and **no provider text anywhere in
the report** — `result`, `container_stderr` and `failure_detail` are all gone.

The wrapper-boundary comparison stands: Claude reaches an authentication
decision from a read-only provider; Codex will not start with its state
directory read-only, refuses a `HOME` under `/tmp`, and both need their state
directory pre-created and owned in the image.

**And the P1-4 defect is the same defect one layer up.** W6634's credential
delivery mounts `0600` files read-only at a fixed root. That is exactly the
shape the reviewer showed a container identity cannot read — so the finding
about the offered personal files is also a finding about the production design.

## State

**Still non-satisfying, and now ready to receive a credential.** Neither trial
returned a pong. The harness was the reviewer's precondition for mounting one
and it is corrected; what remains is a provider the operator nominates, with
ownership or a mode that admits uid 65532 — or an explicit ruling giving the
container a different identity.

## 2026-08-27 — the re-review's three P1s

Evidence: `evidence/w17110-2026-08-27-closed-shape-and-cleanup.txt`.
No repository state was mutated.

All three correct, and each is the same kind of gap: **a check that reported a
fact and did not act on it.**

### [P1] Allowlisting is not validating — and they are two boundaries

Filtering to an allowlist keeps unknown material out of the printed report, and
says nothing about whether the document is this harness's own. A file carrying
every valid fact **plus** raw provider text was still accepted as satisfying,
because the extras were quietly dropped rather than refused.

They are separated now. `allowlisted` is the **durable-report** boundary — what
may be copied. `_closed_shape` is the **document** boundary — what this harness
will accept as its own at all: exactly the required members, plus
`failure_category` and only when something failed. Missing, unknown and extra
all refuse, and the verdict gained a `closed_result_shape` clause.

### [P1] A failed observation is not an observation of absence

The removal's answer was enforced; the *queries* meant to prove absence were
not. A failed `docker ps` or `docker image ls` returns empty stdout, which
became an empty survivor list and then "nothing survived". Both query statuses
now participate in `clean`, and so do the timeout path's kill and removal —
recording them was not the fail-closed treatment the first review asked for.

**And a correction to my own prose.** Last round I called the surviving-id
fallback an immutable-id query. It is not one: the lookup is a *tag* lookup, and
a refused removal is treated as a surviving image by its recorded id because
that is fail-closed — not because anything asked the engine about the id. The
comment now says exactly that at the site.

### [P1] Reporting readability is not gating on it

Preflight reported `readable_by_container_uid` and then ignored it, so a
nominated provider the container cannot open still printed `READY` and exited
zero. That is the preflight telling the operator to proceed into the one
failure it exists to catch. Readiness requires it now.

A **directory** also needs its own execute bit, not only its read bit: `r` on a
directory is permission to read the *names*, `x` is permission to reach what
they name, and a credential provider is used for the second — so a `0444`
provider was reported usable. And the exact paths each trial mounts are assessed
beneath a directory provider, because a generic root cannot prove the
provider-specific file under it is readable.

### Measurement, and what it caught

Eleven guards, each measured by removal. **Four came back vacuous** against the
reviewer's nine, because another guard reached the same verdict first: a missing
member masked by the unknown-member rule, a refused removal masked by the
surviving-id fallback, the timeout cleanup statuses, and an unreachable
ancestor.

A guard nothing can observe is a guard nobody has established, so
`v12/spike/ping-pong/test_harness.py` separates each with a case that can only
fail for its own reason — including two controls, so a case cannot pass because
the decision says no to everything. **The reviewer's file is theirs and was not
edited.**

### Gates

- the reviewer's nine regressions — **9 tests, OK** (five failures at review)
- my four separations and two controls — **6 tests, OK**
- both trials re-run: read-only input, correlation carried, `output.json` last,
  closed published shape, host-recomputed verdict, both cleanup queries
  answered, enforced cleanup, and **no provider text anywhere in the report**
- the engine, asked: no surviving containers or images

## State

**Still non-satisfying.** Neither trial returned a pong. The harness is safe to
receive a credential; what remains is a provider the operator nominates that
uid 65532 can actually traverse and read — or a ruling giving the container a
different identity.

## 2026-08-27 — the third review's two P1s

Evidence: `evidence/w17110-2026-08-27-exact-values-and-ready.txt`.
No repository state was mutated.

Both correct, and both are the campaign's recurring shape once more: **proving
one thing and claiming another.**

### [P1] A closed shape is about values and branches, not names

Two defects in one rule.

It proved member **names**, so `result_bytes: "four"` was allowlisted to
`null`, kept `closed_result_shape: true`, and could satisfy the trial — because
a byte count is not otherwise part of the verdict, so nothing else would ever
have noticed. Every required fact is now held to its own bounded rule: a digest
grammar, an instant grammar, this spike's own name, a provider this harness has
an image for, bounded whole numbers, a non-empty correlation.

**And the two shapes were not disjoint.** Any recognised `failure_category` was
accepted whatever the exit and digest said, so a zero-exit exact-pong document
carrying `failure_category: authentication` was *satisfying* — neither the
success shape nor a truthful failure one. A category is a **claim** that
something went wrong; a document making it beside a clean exit and the right
answer is disagreeing with itself, and accepting one means accepting whichever
half happened to be read. The branches are exclusive now:

- **success**: zero provider exit, the exact pong digest, and no category;
- **failure**: a recognised category, and at least one of those two actually
  failed.

### [P1] A root is not a credential

Preflight collected the exact per-provider paths and then decided readiness from
the **root alone**, so an empty but perfectly readable nominated directory
printed `READY` while both entries a trial would actually mount were absent.
Readiness now requires every path each trial mounts to be present and readable
by uid 65532.

The root clause stays *beside* it rather than being replaced, and there is a
state where they disagree: a `0111` directory is traversable and not listable,
so its entries can be perfectly readable while the root is not. A case pins
exactly that.

The report is also printed **after** the verdict is computed, so it carries the
facts readiness was decided from rather than a subset of them.

### Measurement

Sixteen guards, each measured by removal, **none vacuous**. Three came back
vacuous on the first pass and are now separated by cases that can only fail for
their own reason:

- a boolean where an integer fact belongs — `isinstance(True, int)` is true in
  Python and false in JSON, so `exit_status: true` would read as the number one;
- a success shape that did not answer or did not exit clean — masked through a
  whole trial by the verdict's own clauses, so `_closed_shape` is exercised
  **directly**, with a control that proves the rule does not simply say no to
  everything;
- the root-readability clause, separated by the `0111` case above.

### Gates

- the reviewer's twelve regressions — **12 tests, OK** (three failures at the
  third review)
- my separations and controls — **12 tests, OK**
- both trials re-run: closed published shape, host-recomputed verdict, both
  cleanup queries answered, enforced cleanup, and no provider text in the report
- the engine, asked: no surviving containers or images

## State

**Still non-satisfying.** Neither trial returned a pong. The harness now
validates what it accepts, decides its own verdict, enforces every cleanup
outcome, and refuses to declare itself ready for a provider the container
cannot use. What remains is the operator's nomination.

## 2026-08-27 — the fourth review's two P1s

Evidence: `evidence/w17110-2026-08-27-total-validator-and-image-identity.txt`.
No repository state was mutated.

Both correct.

### [P1] A rule that raises has not refused — it has escaped

`provider` went straight to a dictionary membership test, and a JSON array is
unhashable, so a **perfectly valid JSON document raised `TypeError` out of the
validator** instead of being refused by it. The document is worker-authored, so
"the container would never write that" is not a property this validator may
rely on: it has to be **total** over every JSON value.

Two mechanisms, and each is established separately, because through
`_closed_shape` they are indistinguishable — either one refuses the reviewer's
array:

- the per-rule type guard (`_text`) is the fix, asked directly;
- the blanket that catches a rule which raises is the property the review
  actually named — totality holds only if every rule is right — and it is
  driven by making a rule misbehave, which is the only way to see it act.

### [P1] A tag is a name; the id is the image

Cleanup removed the unique tag and then queried by **that same removed tag**,
which proves nothing. An image surviving under another reference is untagged
successfully, the tag query comes back empty, `image_removed` is true, and the
trial reported a clean engine while the identity it built was still there.

The recorded identity is now asked about after **every** attempt, and a removal
that failed is still a survivor — a command that did not report success is not
evidence of absence either. That also retires the stale comment the review
named: nothing claims an immutable-id query that is not performed, because one
is.

### Measurement

**Nineteen guards, none vacuous.** Two came back vacuous on this round's first
pass and are now separated as described above.

Across the four rounds, this measurement has caught **nine** guards I had
written and not established. That number is the useful part of this record: the
suite being green has been a poor predictor of the boundary actually holding,
and removal has been the thing that told me otherwise every time.

### Gates

- the reviewer's fourteen regressions — **14 tests, OK** (one failure and one
  error at the fourth review)
- my separations and controls — **15 tests, OK**
- both trials re-run: closed and value-checked published shape,
  host-recomputed verdict, every cleanup outcome enforced including the
  identity query, and no provider text in the report
- the engine, asked: no surviving containers or images

## State

**Still non-satisfying.** Neither trial returned a pong. The harness validates
what it accepts, is total over what it is handed, decides its own verdict,
proves image absence by identity rather than by name, and refuses to call
itself ready for a provider the container cannot use. What remains is the
operator's nomination.

## 2026-08-27 — the fifth review: I wrote the same defect again

Evidence: `evidence/w17110-2026-08-27-identity-query-fails-closed.txt`.
No repository state was mutated.

The finding is correct, and it deserves stating as bluntly as the reviewer did.

**Two rounds ago I corrected `docker ps` and the tag query** because a failed
observation is not an observation of absence. **Then I added a new identity
query with exactly that defect** — every non-zero result read as "absent" — and
hard-coded `image_identity_query_ok = True` beside it, where the clean verdict
never consulted it. A daemon error reading 125 was indistinguishable from the
engine saying the image is gone, and the trial called that clean and
satisfying.

Correcting a defect at three call sites and then reintroducing it at a fourth
is not a lapse of attention; it is what happens when the *rule* is corrected in
the places it was found rather than understood as a rule. The three-valued
reading below is the rule, written where the next query will read it.

### The outcome is three-valued, because that is what it always was

- `0` — the image is there.
- `1` — the engine looked and there is no such image. A **successful
  observation of absence**, and the one case that may conclude anything.
- anything else — **the query did not run.** That is not an observation at all,
  and it cannot establish absence.

`image_identity_query_ok` is now that distinction rather than a constant, and
`clean` consults it. It is absent when there was no recorded id to ask about,
and absent is not a failure — there was nothing to observe.

### Measurement

**Twenty-two guards, none vacuous.** One was vacuous on the first pass: the
default that distinguishes an *absent* identity query from a *failed* one. Its
case makes everything else succeed so that default is the only clause left
deciding.

**Across the five rounds this measurement has now caught ten guards I had
written and not established.** That number is the honest summary of this
dossier: the suite being green has been a poor predictor of the boundary
actually holding, and removal has been the thing that said otherwise every
time.

### Gates

- the reviewer's fifteen regressions — **15 tests, OK** (one failure at the
  fifth review)
- my separations and controls — **16 tests, OK**
- both trials re-run: no provider text, host-recomputed verdict, every cleanup
  outcome and every cleanup *query* enforced
- the engine, asked: no surviving containers or images

## State

**Still non-satisfying.** Neither trial returned a pong. Every observation this
harness makes now fails closed: a query that did not run concludes nothing,
about containers, tags or identities alike. What remains is the operator's
credential nomination.

## 2026-08-27 — the sixth review: an exit-status contract I invented

Evidence: `evidence/w17110-2026-08-27-not-found-is-the-engines-word.txt`.
No repository state was mutated.

The finding is correct and the reviewer proved it against a real socket.

Last round I made the identity query three-valued: `0` present, `1` observed
absent, anything else failed. **That mapping is not one the CLI provides.**
`docker image inspect` exits `1` for "no such image" *and* exits `1` for a
daemon it cannot reach — so a reachability failure still read as an image that
is gone, and the trial could call that clean.

I asserted a contract about another program's behaviour instead of checking it.
The check takes one command:

```
absent    -> Error response from daemon: No such image: sha256:0000...
no daemon -> failed to connect to the docker API at unix:///tmp/…; …:
             connect: no such file or directory
```

### Absence is the engine saying so

`NOT_FOUND` matches the engine's own not-found wording, and it is **narrow on
purpose**: the unreachable-daemon message contains "no such file or directory",
so a looser `not found` or bare `no such` alternative would match the very
failure this exists to tell apart. Cases pin both directions against those real
strings, so if either message ever stops meaning what it means, the suite says
so rather than the harness quietly mis-reading it.

A pattern over another program's diagnostics is an **empirical claim about that
program**, not a rule I get to assert. That is the actual lesson of this round.

### And a second witness, orthogonal to the wording

A successful `image ls --all --no-trunc --quiet` inventory that lists the
recorded id means the image is there whatever `inspect` said. It is
status-bearing, so a query that failed is distinguishable from one that found
nothing — and it may only ever **add** a survivor. An inventory that does not
list an id cannot rescue an identity query that never ran, which is the
direction the fifth review's finding was about.

### Measurement

**Twenty-four guards, none vacuous.** One was vacuous on the first pass — the
inventory's power to add a survivor, which nothing reached until a case made
`inspect` say not-found while the inventory listed the id anyway.

**Across the six rounds this measurement has caught eleven guards I had written
and not established.**

### Gates

- the reviewer's sixteen regressions — **16 tests, OK** (one failure at the
  sixth review)
- my separations and controls — **19 tests, OK**, including the two that hold
  the engine's real wording
- both trials re-run: no provider text, host-recomputed verdict, every cleanup
  outcome and query enforced
- the engine, asked: no surviving containers or images

## State

**Still non-satisfying.** Neither trial returned a pong. What remains is the
operator's credential nomination.

## 2026-08-27 — harness signed off; the remaining gate is not mine

Seventh review: **correction accepted, bounded harness signed off.** No further
source-visible defect within the spike's bounded claim.

Revalidated against the current tree before passing: reviewer suite **16, OK**;
my separations and controls **19, OK**; `node --check` clean;
`git diff --check` clean; preflight still refuses, for the one reason it has.

No repository state was mutated.

### What is left is a decision, not an implementation

The reviewer names the two ways out, and both are the operator's:

1. nominate Claude and Codex credential providers readable by container uid
   65532, then run Claude followed by Codex through the signed-off harness; or
2. decline that credential exposure and close or park the experiment
   explicitly as the useful partial it is.

I cannot take either. Option 1 is an exposure decision about live credentials
for the operator's own accounts, which is not a substitution an implementer
makes quietly — and I have declined it on every claim since the first, for the
same reason each time. Option 2 is a closure decision, and this role passes
work back rather than closing it.

### So I made both answers one step instead

`v12/spike/ping-pong/OPERATOR.md` is new. It states why the obvious thing does
not work — both images run as uid 65532, the operator's own files are
`1000:1000 0600`, and a bind mount preserves host ownership rather than
translating it — and then gives the exact commands for each answer:

- **Option 1**: three `install` lines that place copies under
  `/run/baton/credentials` owned `65532:65532` at `0400`, a `preflight.py` run
  that exits zero only when both paths are usable, and the two trials in the
  order the ruling fixes. It notes that `/run` is a tmpfs on most systems, so
  the exposure ends with the machine, and gives the one line that withdraws it
  sooner.
- **Option 2**: what the evidence already answers, and the ruling's own words
  about a partial result.

Nothing in that file reads or prints a credential.

### Why this goes to `baton.ops` rather than back to review

The reviewer has signed the harness off and said in terms that the remaining
gate is the operator's. Returning it to `baton.bug` would ask the same
participant to review a decision they have already handed on; `baton.ops` is
where an operator ruling lives, and it is where W6634's design checkpoint went
for the same reason.

## State

**Harness signed off. Work non-satisfying, awaiting one operator decision.**
Both real providers must return the correlated exact pong for satisfying
closure, and that cannot begin until a credential provider is nominated.

## 2026-08-27 — the operator nominated a provider, and both trials ran for real

Evidence: `evidence/w17110-2026-08-27-first-real-credentialled-trials.txt`.
No repository state was mutated.

The operator acted on `OPERATOR.md`: both entries are present under
`/run/baton/credentials` at `0400`.

### My preflight refused it, and my preflight was wrong

Twice over, and both are the same mistake three reviews running: **I modelled
another system instead of observing it.**

**The host's uid numbering is not the container's on this machine.**

    the host sees      /run/baton/credentials/claude  uid 65534  mode 0400
    the container sees the same file                  uid 65532  mode 0400

So a rule reasoning from host-side ownership concluded "uid 65532 cannot read
this" about a file the container reads perfectly well. Readability is now
**asked**: a probe container runs as the configured identity and uses
`test -r`, which asks the kernel whether this identity could open the path and
**does not read it**. Where the probe and the host-side model disagree the
container is right — it is the party that has to open the file — and a probe
that did not run concludes nothing, which every other observation here already
obeyed.

**And readiness required the nominated root to be readable.**
`/run/baton/credentials` is `0711`: traversable and deliberately not listable,
which is the correct mode for a credential directory. I was refusing a provider
for being well made. `r` on a directory is permission to read the *names*, and
nothing here needs the names — each trial mounts one exact path it was told. My
own case asserting the opposite is corrected, and says so in its docstring.

The operator did this right and my harness told them they hadn't. That cost a
round, and the cause is the habit these reviews keep finding.

### Both trials ran. Neither returned a pong.

**Claude — `credential-refresh-blocked`.** Diagnosed with a boolean sieve that
reports which of a fixed set of phrases appeared and never the phrases
themselves: OAuth, expired, refresh, and nothing else. The runtime
authenticates, finds its OAuth token expired, tries to **refresh** it, and
cannot — the credential is mounted read-only.

That is a finding about the **delivery shape**, not the credential, which is
why it has its own category rather than being filed under `authentication`. A
read-only credential mount works only for a **static** credential. An OAuth
runtime rotates its own, and a copy taken at one moment is a snapshot of a
moving thing.

**Codex — `network`.** "Connection failed: error sending request" against its
backend, while preflight proves from inside a container that both provider
endpoints answer. Not diagnosed further: the raw probe outlived a ten-minute
bound, which is the same non-termination the harness already bounds and the
reason it does.

### What this tells W6634, and it is the most useful thing here

W6634's approved credential delivery materializes assignment-private files and
mounts them **read-only** at a fixed root. On this evidence that shape is
sufficient for **neither** real runtime:

- Codex will not **start** with its state directory read-only;
- Claude starts, authenticates, and cannot **refresh**.

Both want to write beside their credential. A delivery that forbids it supports
static secrets only — which may well be the right answer, but it is a decision
the design has not made explicitly, and it now has evidence to make it on.

### Gates

- the reviewer's sixteen regressions — **16, OK**, untouched
- mine — **20, OK**, gained two: a traversable root whose entries are readable
  *is* ready, and a probe that did not run concludes nothing
- both trials: closed published shape, host-recomputed verdict, every cleanup
  outcome and query enforced, **no provider text anywhere in either report**
- the engine, asked: no surviving containers or images

## State

**Still non-satisfying**, and now for a reason with a name rather than a
missing precondition.

**Claude is one step away and the step is the operator's:** the nominated copy
is a stale snapshot of a rotating token. Re-copying it from a freshly refreshed
host credential should let the trial run inside the new token's lifetime. That
preserves the read-only constraint the ruling pins. The alternative — a
writable credential mount — is a **revision of that constraint** and is not
mine to make.

**Codex needs its connection failure understood** before anything can be
concluded about it.

## 2026-08-27 — the eighth review's five findings

Evidence: `evidence/w17110-2026-08-27-two-gates-and-two-claims.txt`.
No repository state was mutated.

All five correct. Two are about the preflight gates; two are about claims this
record made that its evidence did not support; one is an instruction I wrote
that exceeded what the approver authorized.

### CORRECTION to the entry above this one

**The previous PROGRESS entry and its transcript quoted Codex's response
wording verbatim, while also claiming no provider text appears anywhere.** Both
cannot be true and the claim was the false one.

That phrase is not a secret. Persisting it is still a breach of the boundary
the *first* review closed: provider output comes from a process holding a
credential, so only closed categories and bounded operational facts may be
written down. Having argued that at length, I then wrote the text into two
durable artifacts.

**The Codex result is `network` and nothing more.** The earlier files are
historical events and are not rewritten; this correction stands beside them,
and the wording is not reproduced again.

### CORRECTION to that entry's W6634 takeaway

It stated as a finding that read-only credential delivery is insufficient for
Claude. **That was a hypothesis wearing a finding's clothes.**

What was observed is an expired token. No write-denied signal was ever seen —
and under the approved layout the surrounding state directory *is* writable, so
the earlier whole-directory Codex result does not transfer. The same entry said
a fresh snapshot might succeed, which is incompatible with the delivery shape
being the proved cause. I did not notice the contradiction inside my own
paragraph.

Confirmed and hypothesised are now separated in the evidence, and the
`credential-refresh-blocked` category is gone with it:

- **`credential-expired`** describes what was seen.
- **`credential-write-denied`** explains, and is earned only by an actual
  write-denied signal.

A category that names a mechanism has to be paid for with a signal for that
mechanism.

### [P1] Two gates, and one was silently standing in for the other

A bind mount hands the container the exact file, so a successful probe says
nothing about a carrier the identity could never have walked. Readability and
traversal answer different questions about different objects; folding them left
neither visible. Traversal is its own clause now, over the entries that exist,
and the carrier still need not be listable — which is what the approved
traverse-only layout requires.

### [P1] A failed probe fell back to the model it superseded

I wrote that a probe which did not run concludes nothing, and then had it fall
back to `readable_by_container_uid` — so a failed probe over a
positively-modelled file still read as READY. Once the engine is present, an
exact file is usable only when a probe **ran** and said so.

### [P1 operational] I authorized a deletion the approver did not

`OPERATOR.md` said `sudo rm -rf /run/baton/credentials`. The pinned decision
authorizes unlinking the two exact entries and removing the directories once
empty, and **explicitly authorizes no recursive deletion**. An operator would
have run that on my say-so. It is now exact `unlink`/`rmdir`, and `rmdir`
refusing a non-empty directory is the point.

`OPERATOR.md`'s "option 2 — close as a partial" is also gone: the full-proof
ruling superseded it, and leaving it there offered a path the approver had
removed.

### Both trials re-run

`credential-expired` and `network`. Closed shapes, matching correlations,
enforced clean teardown, `satisfying: false`, and **no provider text in either
report**.

### Gates

- the reviewer's eighteen regressions — **18, OK** (two failures at review)
- mine — **20, OK**
- live preflight — **exit 0**; the approved `0711` carrier still passes, and
  the two new negative boundaries refuse
- the engine, asked: no surviving containers or images

## State

**Still non-satisfying**, and the full-proof ruling means only two correlated
exact pongs discharge this Work. The credential remains staged and the harness
is corrected. The Claude path needs a token inside its lifetime; the Codex path
needs its connection failure understood.

## 2026-08-27 — BOTH REAL AGENTS RETURNED THE CORRELATED EXACT PONG

Evidence: `evidence/w17110-2026-08-27-both-pongs.txt`.

The live trials did not alter tracked source; no Git history or index was
mutated. (That is the narrow fact every earlier transcript overstated as "no
repository state was mutated" while documenting source and dossier changes —
the ninth review's [P2], corrected here rather than rewritten there.)

### The proof

A real Claude container and a real Codex container each received a correlated
`ping` through the read-only input root, ran the actual provider runtime
against a read-only credential mounted at its native path, and published
`/output/output.json` last carrying the exact `pong`. Every verdict clause is
true on both — this spike's identity, the provider asked for, the correlation
carried through, both exit states zero, the answer's digest equal to
`sha256("pong")` derived on the host, and a closed value-checked document
shape — with enforced clean teardown and **no provider text in either report**.

### What the Codex failure actually was, and it was mine

Two rounds classified Codex `network`. **The classifier was right and I was
looking in the wrong place**: it described what it saw, and what it saw was a
defect in my own recipe.

A bounded sieve matched `certificate` and `CA`, and reported
`ca-certificates present: NO`. `node:22-bookworm-slim` ships no
`/etc/ssl/certs/ca-certificates.crt`; the Codex CLI is a **native binary** and
uses the system trust store, so every TLS handshake failed and surfaced as a
connection error. Claude Code uses Node's bundled store and never noticed.

**That is the wrapper-boundary finding of the whole experiment**, and not one a
scripted worker could have produced: two agent runtimes packaged identically
differ in whether they need the system trust store, and the one that needs it
fails in a way that reads like the network being wrong. Installed on **both**
images, so the trials differ in the runtime and not in the ground they stand
on.

It also retires the hypothesis I was carrying: Codex's failure had nothing to
do with credential delivery. Exact-file read-only delivery works for both
runtimes.

### [P1] A write denied somewhere is not a write denied here

`credential-write-denied` matched generic `EACCES`/permission-denied/cannot-write
wording, which can name any path the runtime touched. That establishes a
write-denied **result** and nothing about what was being written to — the
eighth review's rule, applied to my replacement for the thing it removed.
Causation is now earned only when the message names the exact mounted
credential path, with controls proving an unrelated write failure cannot become
a credential claim.

**Those controls found an ordering defect while proving it.** `EACCES:
permission denied, open '.../.credentials.json'` contains the word
"credential", so with the broader list checked first it classified as
`authentication` — naming the wrong failure entirely, and doing it most
confidently in the case that mentions the credential. A denied write now wins
in either form.

### [P1] The operator documents described a state the Work had left

`OPERATOR.md` still opened by saying no provider had been nominated, when the
provider was staged and two rounds had run; an operator reading it would have
acted on a state that no longer existed. It now says where things stand and
what is next. `PLAN.md`'s decline/partial-close action is marked superseded
**on the line itself**, because a confirmed decision has to leave only one
actionable rule and a later section saying so elsewhere still left that one
readable as live.

### Gates

- the reviewer's eighteen regressions — **18, OK**
- mine — **24, OK**, four added for the classification controls
- live preflight — **exit 0**
- the engine, asked: no surviving containers or images

## State

**Both correlated exact pongs are proved, with enforced clean teardown.** That
is the closure condition the full-proof ruling names, and it is for independent
review to confirm rather than for me to declare — this role passes work back
rather than closing it.

**The credential is still staged.** The approved decision has the *operator*
unlink the two exact entries and remove the now-empty directories once the
trials are done and cleanup is proved. Both are done and proved; the exact
commands are in `OPERATOR.md`. An agent does not withdraw the operator's own
credential staging.

## 2026-08-27 — the tenth review: the proof, as values rather than claims

Evidence: `evidence/w17110-2026-08-27-exact-proof-reports.txt`.
The live trials did not alter tracked source; no Git history or index was
mutated.

All three findings correct.

### [P1] I persisted claims about the proof instead of the proof

The previous transcript rendered each success as a list of true booleans and an
abbreviated image id. `correlation_matches: true` asks a reviewer to take my
word for a comparison they could have made themselves from two strings I did
not print.

The harness was built so its stdout carries no provider text — that is the
whole point of the allowlist and the digest — so the exact stdout was always
safe to persist, and persisting it is what makes the result independently
recomputable. **Both trials were rerun while the provider is staged**, and the
evidence carries their stdout verbatim rather than reconstructed values.

A reviewer can now check, without trusting me:

- the host's `correlation_id` against the published one, per trial;
- `result_digest` against `sha256("pong")`, which the evidence also prints and
  anyone can derive — both trials report
  `sha256:9795c5ff…5baef2`, and the two correlations differ between trials as
  they must;
- both exit statuses, the provider's as the container observed it and the
  container's own;
- the complete allowlisted publication, so its members can be held to the
  closed set;
- `completion_signal_present` and the **full** image id;
- every cleanup command and query outcome and both survivor lists.

### [P1] The classifier matched across diagnostics, not within one

`writeDeniedCategory` tested stdout and stderr joined, so a credential path in
**one** line and an unrelated write denial in **another** combined into a causal
claim neither line makes — two facts that never met, read as one. A message is
the unit that carries a claim, so the denial and the path must now be in the
same one. Cross-line negative controls, and the positive beside them so the
rule is not merely a way of never concluding.

### [P1] `OPERATOR.md` trailed the Work a second time

It directed two retries after both trials had already returned the pong. It now
names one remaining operator action, says the sign-off and the closure are not
its business, and keeps the staging instructions under a heading saying they
are not a current instruction.

Twice is a pattern rather than an oversight: an operator-facing document is
state, and I was treating it as prose written once.

### Gates

- the reviewer's eighteen regressions — **18, OK**
- mine — **26, OK**, two added for the cross-line relation
- live preflight — **exit 0**
- the engine, asked: no surviving containers or images. The reviewer's own
  engine queries were denied at the socket, so that is my observation and not
  theirs; the per-trial cleanup fields in the reports are the part that does
  not depend on my running it.

## State

**Both correlated exact pongs are proved, and the proof is now in the record as
values.** Sign-off is the reviewer's. Terminal closure waits on the operator's
exact withdrawal of the two volatile credential entries, which the pinned
decision assigns to them and which `OPERATOR.md` now names as the only
remaining operator action.
