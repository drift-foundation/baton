# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-27 — claimed; PLAN 1, the W6634 credential revalidation

Claimed W26284 at seq 26819, after passing its sibling W26283 back at seq 26817.
Both are successors of the W6634 half I reported as non-satisfying while holding
W6636; this one owns fresh-run credential delivery.

### How this revalidation was done, and why

The finding says provisional code is **evidence, not accepted implementation**.
W26283 ended with a measurement that found a guard sitting in this same spike
with *nothing observing it* — a live-secret scan standing in for a named
acceptance clause. Reading more carefully was not going to catch the next one,
because the code reads *well*: every rule the finding names has a comment
beside it explaining why it is there.

So the revalidation is a **measurement**: each rule the finding names was
removed from the source and the credential, adapter, secrets and text-sweep
suites re-run. A rule nothing notices is one this provider has not established,
however carefully it is written.

Harness: `evidence/w26284-revalidation-harness.py`. Nothing in it is a fix.

### Result: eight of eighteen rules are unestablished

**Caught — the rules that are genuinely established:** an existing credential
root is never written into; a slot name cannot leave the root it names an entry
of; a bearer wider than the bound is refused; a failed materialization leaves no
root; teardown proves each removal before forgetting, and refuses an unprovable
one; the lifecycle record is removed; a credential is mounted read-only; and no
bearer reaches the argv.

**UNSEEN — removed and nothing failed:**

| the finding says | what nothing observes |
| --- | --- |
| "registered as live **before** any materialization" | moving `remember_secret` to *after* the write |
| the same | removing the registration entirely |
| "**mode-0600** files" | `VOLATILE_FILE = 0o644` |
| "assignment-private **mode-0700** volatile root" | `VOLATILE_DIR = 0o755` |
| the same | applying the mode *after* the open instead of at it |
| exclusive creation | dropping `O_EXCL` from the credential file |
| bounded slots | `MAX_SLOTS = 100000` |
| "failure preserves live-secret tracking" | forgetting *before* removing |
| bounded mounts | dropping the mount-count bound |

The two permission rules are the sharpest. The acceptance says outright that
*"fresh-run credential files and roots have the required permissions"*, and
both constants can be changed to world-readable and world-traversable with the
entire suite still green. The ordering rules are the next sharpest: "live before
materialization" and "converge to absence before forgetting" are the two
properties that make the registry mean anything, and neither is observed on the
fresh-run path.

### What that settles about the plan

PLAN 2 and 3 are largely *not* rewrites. The code already does these things; what
it does not have is anything holding it to them. So this Work's substance is
mostly PLAN 4 — establishing the rules that exist — plus whatever the
establishment then exposes, which is how W26283 found its real defect.

I am deliberately **not** treating "the code already does it" as done. That is
exactly the reasoning that let a scan sit unobserved through seven review rounds
of W6634.

## State

PLAN 1 done and recorded. Implementing next.

## 2026-08-27 — PLAN 2–5: establishing the rules that already existed

Evidence: `evidence/w26284-2026-08-27-credential-provider.txt`.
Harness: `evidence/w26284-revalidation-harness.py`.
No Git history or index was mutated.

### The measurement corrected itself twice before it was reported

Two of the nine rules the first pass called UNSEEN were my harness's fault, not
the code's. The "registered live after the write" mutation moved
`remember_secret` down by two lines — still *above* the `os.open` that
`test_the_bearer_is_live_before_its_bytes_reach_a_file` watches, so it could
never have failed — and the "never registered at all" anchor matched twice.
Re-anchored properly, both are **caught**: that ordering is genuinely
established.

I am recording this because reporting them would have been reporting two
defects that do not exist, and the only reason I did not is that the class name
`MaterializationArmsTheRegistryFirst` made me go and read what it asserts.

**The honest result is seven unestablished of nineteen.**

### Why the permission rules were the sharpest

`test_one_private_file_per_slot` asserts

```python
self.assertEqual(stat.S_IMODE(os.stat(place).st_mode), credentials.VOLATILE_FILE)
```

— the observed mode against **the constant that produced it**. It proves
internal consistency and nothing about the required permission, so
`VOLATILE_FILE = 0o644` and `VOLATILE_DIR = 0o755` both pass the whole suite.
The acceptance says *"fresh-run credential files and roots have the REQUIRED
permissions"*, and a required value is a literal somewhere or it is not
required.

`ThePermissionsAreTheContractsRatherThanTheCodes` now asserts the literals, and
asserts them **under a zero umask** — `os.open`'s mode is masked by the process
umask, so a case run under `0o077` would observe `0o600` even for a file created
`0o666` and would pass for exactly the defect it exists to catch.

### What else was established, and what changed

Nothing about the behaviour changed. The code already did all seven; what it
lacked was anything holding it to them:

- the two permission literals, plus the mode given **at** the open rather than
  applied after, and `O_EXCL` — all three observed at the open itself;
- `MAX_SLOTS`, at both owners: the assignment's authorized set and the
  adapter's mount composition, which are separate rules and needed separate
  cases;
- the failure path's order — the root gone **before** the bearer is forgotten,
  driven by failing the provider on the second slot so the first is already
  written and live when the discard runs.

Two of my own new cases were wrong before they were right, and both taught
something: the provider capability is handed `(provider, reference)` rather than
the slot name, so my first failure injection never raised at all; and
`refused/unavailable` is not a pairing the taxonomy has, which the closed
pairing refused — the check doing its job on me.

### The real-engine suite

The acceptance asks for it and for proof that secrets are absent from argv,
environment, labels and durable documents. `test_credentials_engine.py` starts
real containers carrying a delivered credential and asks the **daemon** what it
recorded: the whole `inspect` document searched as text, then the four members
named individually so a failure says which.

**That assertion had to be made falsifiable.** Nothing in the ordinary path puts
a bearer where the daemon could store it — the credential is a file, not an
argument — so asserting its absence proves only that the ordinary path is
ordinary. A caller-supplied label is the one member that would be spelled into
the command line, which is how the existing argv case makes the §13 walk
reachable, so this does the same and then asks the daemon whether anything was
created.

Driving that found a question worth answering: `start` reaches the engine
**before** the sweep, for its duplicate probe. I checked whether that probe's
argv carries the bearer — it does not, because `participant` is not one of the
candidate label filters — and asserted it so it stays true. Verified rather than
assumed, and worth saying that it could as easily have gone the other way.

### Gates

- credentials, adapter, secrets, text-sweep and the engine suite — all green
- **19 mutations, all caught**, with the real-engine suite in the measurement
- full v12 tree — **1568 tests, 7 failures**, exactly the accepted baseline

## State

PLAN 1–5 done. Passed for independent review rather than closed.

### For review

- The behaviour is unchanged and deliberately so. If the reviewer's judgement is
  that a provider whose rules were unobserved should also be *rewritten*, that
  is a different Work than this finding describes, and I would rather be told
  than assume it.
- `O_EXCL` on the credential file is now observed at the open, but it remains
  **unreachable through `materialize`**: the root's existence is refused first
  and `os.makedirs(..., exist_ok=False)` guarantees an empty root, so no slot
  file can pre-exist. It is kept as defence for a caller reached another way,
  and this is stated rather than left to look like coverage.

## 2026-08-28 — the two reviewed P1s, corrected

Claimed W26284 at seq 29780. Read the thread, the whole record and the review,
then reproduced both P1s on the current tree before touching anything:

```text
materialization cleanup: root_present=True bearer_live=False
pre-sweep engine calls: 2 calls containing bearer: 2
```

### The cleanup that forgot without proving

`_discard` exists to answer whether the root is GONE. The failed-
materialization handler called it, threw the answer away, and forgot every
bearer unconditionally — so a filesystem that refused the removal left the
bearer bytes readable while the registry guarding every later §13 scan was
disarmed. A check that cannot fail is worse than no check, because it reads as
evidence.

It now branches on the proof. A proved removal forgets and re-raises the
caller's original failure. An unproved one keeps every bearer REGISTERED and
raises its own `policy/credential-lifetime` ending rather than propagating the
provider's — what an operator has to act on is a stranded bearer, not a
provider that was down a moment ago.

### The sweep that covered one vector out of five

`run_vector` swept the argv it composed and nothing swept the others, so
`start`'s duplicate probe reached the engine FIRST and unswept. The candidate
selector puts `runtime_attempt_id` into a `--filter` argument and a provider
answer is explicitly untrusted, so a bearer equal to the attempt identity was
handed to the daemon by the very call meant to run before anything happened.

I moved the rule rather than copying it. The property is about INVOCATION, not
composition — every process on the host can read another's command line — and
invocation is exactly what `EnginePort.__call__` is. Adding the sweep beside
`run_vector`'s would have been four more copies of one rule and a fifth
waiting for the next vector somebody writes. The reviewer's own reproduction
now reports `0 calls containing bearer`, and it reports zero CALLS: the probe
refuses before the engine is reached at all.

**One existing expectation moved with it.**
`test_no_bearer_reaches_the_argv` asserted the walk was reachable by calling
`run_vector` directly. What it protects is unchanged — a live bearer does not
reach a command line, and the guard that stops it can fail — but the boundary
that owns the rule moved, so the reachability half now drives the port. The
review's required correction is what authorizes that; I am naming it here
rather than letting it look like incidental churn.

### The real-engine case that proved something else

`test_teardown_forgets_only_after_the_bytes_are_proved_gone` started a real
container and then called `tear_down` directly. Removing a host pathname is
not proof that a bind-mounted runtime cannot still hold the inode, and this
finding keeps the shared quiescence/removal/settlement crossing explicitly
outside this provider.

The review offered two ways out and the finding's own boundary chooses between
them: this suite stays inside fresh-run delivery and failure. The case now
tears down a delivery that never launched — a real ending this provider owns —
and a new case covers the one runtime-absence question it does own: a start
the engine refused settles through the adapter's real `ps` against a real
daemon before the delivery is released. Nothing here stops, removes or
reconciles a container, because no container exists. The post-runtime crossing
stays W6636's.

### Why my own nineteen-mutation measurement was not enough

This is the part I want to state plainly, because the measurement was honest
and still missed both defects.

Both failed-materialization mutations watched a SUCCESSFUL removal — one
deleted the `_discard` call, the other swapped it with the forgetting. Neither
drove the explicit FALSE answer, which is the one the operation exists to
return. So nineteen of nineteen could be caught while the registry was
disarmed over bytes still on disk. And the argv mutation removed the sweep
from the one vector that had it, while the case backing it chose the
`participant` label precisely because it is NOT a candidate filter — proving
the late sweep worked and saying nothing about the early leak.

A measurement can be complete against the rules it chose to break and still
miss the rule nobody wrote down. Here that rule was "`_discard`'s ANSWER is
the guard, not its call". The harness now drives the false answer and removes
the sweep at its single owner.

### One anchor failure worth naming

The credential-mount mutation reported `[ANCHOR] 2x in oci.py` rather than
mutating silently. W26291 added a launch-document mount whose argv composition
AND whose collision-refusal prose are byte-identical to the credential one, so
both the mount line and the text above it match twice. The anchor is now
pinned through the word "credential"; the duplication itself belongs to W26291
and is named rather than edited from this Work.

### Gates

- `test_credentials` 80, focused four-suite set 265 — green
- real-engine `test_credentials_engine` 7 — green, and it now removes its own
  trees: measured before and after a fresh run at 347, **delta 0**
- the revalidation harness — **20 of 20 mutations caught**
- the reviewer's reproductions, re-run through
  `evidence/w26284-corrected-reproductions.py` — exit 0,
  `root_present=True bearer_live=True` and `0 calls containing bearer`
- `tools/parallel_test.py` — 1553 tests, **6 failures, all in
  `test_boundary_inventory`**, the accepted baseline and none this Work's
- `--phase serial` — 105 tests, 0 failures

### On the reviewer's own reproduction file

`evidence/w26284-review-reproductions.py` is KEPT exactly as produced. Its
first probe catches `OSError` around `materialize`, because the old code
propagated the provider's failure after silently forgetting; the correction
makes an unprovable cleanup its own refusal, so that probe now raises instead
of reporting. `evidence/w26284-corrected-reproductions.py` is the same two
probes with that one catch widened — the MEASUREMENT is unchanged, and it is
the measurement that decides safety.

### Left for the operator, not removed by this turn

347 `v12-w26284-engine-*` trees under `/tmp` from runs before the cleanup fix.
Named exactly rather than swept up: a glob-wide destructive command over paths
this turn did not create is what managed-turn policy steers away from, and the
defect that produced them is fixed at its source.

No version-control history or index was mutated. Awaiting independent review.
