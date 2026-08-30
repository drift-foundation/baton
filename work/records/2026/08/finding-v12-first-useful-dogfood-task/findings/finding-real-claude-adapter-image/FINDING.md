# Build the real Claude worker adapter and image

Work: W39357
Parent: W38956

## Purpose

Turn the provider-neutral worker into one real Claude-backed dogfood image
without importing W17110's spike protocol or direct Docker lifecycle.

## Confirmed boundary

- Inject the provider through `baton_worker.main(agent=...)`; the worker-entry
  framing and assignment contract remain the authority.
- Reuse only W17110's pinned Claude installation facts. Do not run
  `trial.mjs`, publish its result shape or make the worker own Docker.
- Read the explicit attempt-scoped `claude` credential slot at the fixed
  `/run/baton/credentials/` mount. No home-directory fallback, environment or
  argv secret, workspace copy, hashing, printing or semantic inspection.
- Copy exactly `/input/source` into bounded container-private scratch below
  `/tmp`. The canonical/source bind stays read-only; the declared proposal is
  the only host-writable output.
- Invoke Claude through a closed, golden-tested argv. Provider prose is input
  to the adapter, never worker-control framing or success identity.
- Write `proposal/{result.json,candidate,change.patch,verification.txt}` with
  cooperative group-readable modes, then let the existing worker publish the
  measured `/output/output.json` last.

## Initial file ownership

This child owns new worker-side files such as a Claude agent module, its
dogfood entrypoint/Dockerfile and focused provider-image tests. It does not own
the Python manager transport files held by W39356 or operator files held by
W39358. Any necessary edit to shared `baton_worker.py` requires an explicit
handoff first; prefer its existing injection seam.

## Acceptance

- Provider argv, prompt/document conversion, bounded response handling,
  explicit credential path, source copy and declared proposal writes have
  focused tests with no live secret.
- Missing credential, nonzero Claude exit, malformed/bounded response or no
  candidate cannot report `completed` or publish a useful proposal.
- The image is pinned/reproducible at the level already proven by W17110 and
  starts the ordinary worker-entry program with the real adapter injected.
- A no-secret image gate proves the CLI/entrypoint is present. The first live
  provider invocation waits for the operator's exact credential and network
  grants and belongs to W39364.

## 2026-08-29 — implementation revalidation (`baton.claude`, W39357 impl claim)

### Confirmed against the current tree

`baton_worker.main(argv, stdin, stdout, agent, place)` still takes the injected
agent, and the image entrypoint still supplies `ScriptedAgent`. The agent
contract is exactly two methods — `consider(seen, request)` and
`work(seen, declared)` — and `work` must answer
`{disposition, outputs, recap}`. The worker measures the bytes, holds the
answer against the declarations and publishes `/output/output.json` LAST; none
of that is the adapter's to do, and this checkpoint does not touch
`baton_worker.py`.

W17110's pinned installation facts hold: `node:22-bookworm-slim`,
`@anthropic-ai/claude-code@2.1.247`, `ca-certificates` (its absence surfaced as
a fake "network" fault for two review rounds), and a pre-created home owned by
`65532` — Docker creates a missing bind-mount parent as root, which left the
runtime unable to write beside its own credential.

`credentials.CREDENTIAL_ROOT` is `/run/baton/credentials` and a slot is mounted
at `/run/baton/credentials/<slot>`, read-only, by the accepted adapter.

### Confirmed: the read-only root forces the private HOME, and that is not a
### workaround

W17110 mounted the credential directly at
`/home/nonroot/.claude/.credentials.json` through the spike's own Docker
lifecycle. The accepted v12 adapter cannot: `RESTRICTIONS` fixes `--read-only`,
with tmpfs only at `/tmp` and `/dev/shm`, and the credential lands at the fixed
`/run/baton/credentials/` root instead. A provider that writes anywhere under
its home therefore cannot start.

**Decision (pinned): the adapter composes a container-private HOME under the
`/tmp` tmpfs and SYMLINKS the provider's expected credential path at the fixed
slot.** A symlink is not a copy: no bearer is read, hashed, printed, inspected,
copied into the workspace, or placed in argv, an environment value, the result
or the evidence. `HOME` is an ordinary process operand of the child, and the
tmpfs is private to the container and destroyed with it.

The image-owned link W38956's parent finding contemplated is NOT used, because
an image-owned link would have to point at a path inside a read-only root that
the provider then cannot write beside. The link is made at run time, in private
scratch, by the adapter — which is also where the source copy already goes.

### Confirmed: no environment secret can reach the container by construction

The accepted `run_vector` composes no `--env` at all — W26291 retired that
transport with no fallback and `test_lifecycle_composition` asserts its
absence. That matters more than it looks: an `ANTHROPIC_API_KEY` present in the
container would silently outrank every other credential source, so a stray one
would decide which account the trial ran as. The adapter passes the child a
closed environment it composes itself and never forwards the worker's own.

### Pinned: the frozen task is a closed versioned document

The worker-control contract deliberately carries no task — `work` reads the
assignment from `/input/input.json`, and an inline task was the superseded
shape. The dogfood WORKLOAD still needs one, and it needs to be
machine-readable, because the adapter must run the task's own verification
command and cannot infer it from prose.

**Decision (pinned): `/input/task.json`, schema `baton.dogfood-task/1`, closed
over exactly `schema`, `task_id`, `instructions`, `verification` and
`source_root`.** It is a WORKLOAD convention and not Worker Manager protocol
vocabulary — the same boundary the parent finding draws for Git. The manager
never reads it; the operator checkpoint (W39358) stages it and the first task
(W39364) writes it.

### Pinned: the provider argv, and the one place it departs from W17110

W17110 ran `claude --print --permission-mode plan <prompt>`. `plan` is right
for a ping-pong that must not touch anything and wrong here: the dogfood task
must EDIT files. The composed argv is therefore

    claude --print --permission-mode acceptEdits <prompt>

with the candidate copy as the working directory. It is closed and
golden-tested, and it is deliberately NOT live-proven under this checkpoint —
the first live provider invocation needs the operator's exact credential and
network grants and belongs to W39364, which this finding already says.

**This is the one operand a reviewer should look at hardest.** It is the only
part of this checkpoint whose correctness a golden test cannot establish: the
flag names are W17110's measured evidence plus one deliberate change, and the
`claude-api` reference is explicitly the API/SDK surface rather than the CLI's,
so it does not settle CLI flags. If the first live trial shows
`acceptEdits` is the wrong spelling, the fix is one constant and one golden
vector.

## 2026-08-29 — third round, after `review-2026-08-29T22-18-55Z.md`

The second round's claimed no-secret publication boundary was bypassable in two
places and its advertised traversal bound did not count what it traversed. The
three decisions below are pinned because each replaces a rule that LOOKED
sufficient, and the next reader needs to know why the obvious weaker form was
not kept.

### Pinned: a checked path is a DESCRIPTOR CHAIN, never a string reopened later

**Superseded:** the second round's rule that `_checked_tree` plus a final
`O_NOFOLLOW` open was "the same checked objects". It was not. `O_NOFOLLOW`
refuses a link only at the LAST component, and `_checked_tree` recorded
relative path STRINGS — so `candidate/nested/claude` was still resolved through
whatever `nested` happened to be at the instant of the open. The task's own
verification command runs between the check and the publication, it is
provider-authored, and it owns that directory: replacing `nested` with a link
to `/run/baton/credentials` made the mounted bearer an ordinary final file.

**The rule now:** every read under a provider-authored tree walks the path by
descriptor — each component opened `O_NOFOLLOW | O_DIRECTORY` relative to the
one above it, the final name opened `O_NOFOLLOW` relative to its proved parent,
and `fstat` proving what was actually opened. No component is resolved by the
kernel from a string this module composed, so there is no lookup left for a
rename to redirect. The kernel spells the refusal two ways — `ELOOP` at the
final name, `ENOTDIR` at an intermediate one — and both are the same refusal.

The checked list is additionally revalidated after the payload's own
verification command returns and before publication begins. That changes no
published byte, because each read is already safe on its own; what it buys is
that a mutated tree refuses before the first output byte rather than part-way
through a proposal an operator would then find half-written.

### Pinned: captured streams have NO NAME

**Superseded:** the second round's rule that streams go to files under private
scratch and only a window is read back. The bound was right and is kept; the
NAMING was the defect. `_capture` created `capture-*/stdout` inside the
candidate — which for the verification run is the child's own working
directory — and `_window` REOPENED that pathname once the child returned. A
command that unlinked it and put a link to the credential in its place had the
bounded reader transcribe the bearer into `verification.txt`.

**The rule now:** captures are `tempfile.TemporaryFile` — a descriptor on a
file with no directory entry anywhere — and the window is read back from that
same descriptor. There is no pathname for a child to replace and no second
lookup to redirect.

Moving the capture directory to private scratch was considered and REJECTED as
the fix, though the capture root did move: the verification child runs as the
same uid as the adapter, so a private 0700 directory is a name it can reach
exactly as easily as its own cwd. A defence that depends on the child not
knowing a path is not a boundary. An anonymous file retires the class.

### Pinned: the entry ceiling counts EVERY entry the walk touches

**Superseded:** counting only regular files. Both walks examined directories
for links and then advanced the counter only for files, so a provider could
create an unbounded number of empty directories while crossing no stated bound
— leaving the traversal limited by tmpfs inodes and wall clock rather than by
`MAX_SOURCE_ENTRIES`, which the module and this finding both advertise.

**The rule now:** one shared `_bounded` check, applied by both the staged walk
and the provider-authored walk, counting every directory and every regular
file. The staged tree is the manager's and already measured, but a second party
that counts differently from the walk it is checking is not proving the same
thing. `_copy_tree` still answers the number of FILES copied, which is what
`result.json` reports and what the empty-tree refusal is about.

### Open, unchanged

The first live provider turn (W39364) and W39770's `main(agent=...)` seam
correction, which the image recipe still works around with a named stopgap.

## 2026-08-29 — fourth round, after `review-2026-08-29T22-51-53Z.md`

### Pinned: what binds the published bytes is the BYTES, not the path

**Superseded:** the third round's rule that revalidating each checked path
before publication makes the tree safe, and with it that round's claim that "a
mutated tree refuses before the first output byte". Reopening a path and
proving it regular holds its TYPE. The provider-authored verification command
runs after `_diff` measured the candidate and before `_publish` reads it, and
overwriting an already-checked regular file IN PLACE needs no link, no rename
and no new inode — so the proposal carried bytes that neither `change.patch`
nor `changed_paths` described, and the mounted bearer is one of the things
those bytes could be. The descriptor-chain rule from the third round is
unchanged and still necessary; it was never sufficient.

**The rule now:** `_diff` answers the sha256 of every candidate file it read,
and that digest is what carries through to publication. `_revalidated` proves
three things before anything is created — the ceilings again over a FRESH
walk, that every measured path is still there, and that every measured file
still has the bytes the patch describes — and `_publish` reads each file once,
proves that same digest at the moment of use, and writes those same bytes. The
proof is never separated from the use by another read.

A digest is not an inspection. Nothing decides what the bytes MEAN, no digest
is published, and a mismatch refuses rather than reporting what it saw — which
matters precisely because the substitution a verification command is most
usefully caught making is the mounted bearer.

### Pinned: an ADDITION is not a mutation

A verification command that leaves a cache directory behind has invalidated
nobody's evidence: what it added was never measured and is never published.
Refusing those would make ordinary tooling a fault; publishing them would put
unmeasured bytes in the proposal. So additions are tolerated and unpublished —
and the fresh walk still counts them against both ceilings, which is the other
half of the review's finding: a FIXED list could not see what verification
added or how much it grew, so the bound this module advertises stopped
applying at exactly the moment untrusted code ran.

### The guard that did not guard

`test_the_scripted_default_is_present_only_as_the_seam_stopgap` asserted that
`baton_worker.py` still CONTAINED `from scripted_agent import ScriptedAgent`,
meaning to fail once W39770 fixed the seam. It did not fail: W39770 MOVED the
import into `_scripted_default()` rather than deleting it, so the string
survived and the guard went on saying the stopgap was needed after it was not.
It now asserts the real condition — that the import is inside the lazy default
rather than ahead of the injection check — so the removal it guards is the one
actually owed.

**The removal is owed to W39770's approver acceptance and is deliberately not
done here.** The code reason for the COPY is gone; what keeps it is that
W39770 is signed off and not yet accepted, and this checkpoint does not get to
pre-empt that by shipping an image that depends on it.

## 2026-08-30 — fifth round, after `review-2026-08-30T04-01-29Z.md`

### Pinned: NO BYTE A CHILD WROTE IS PUBLISHED, and the streams are not read

**Superseded:** every earlier rule about how a child's captured stream is
bounded and read back. The second round bounded the capture before allocation;
the third gave it no pathname and read it from a held descriptor. Both were
answers to *how do we read this untrusted stream safely*, and this review is
the finding that the question was wrong.

No pathname race and no link were ever needed. The provider is handed the
attempt's bearer and its stderr was interpolated into `result.json`; the task's
verification command is code out of the candidate the provider has just edited,
running as the same uid with the same mount readable, and its two streams were
copied verbatim into `verification.txt`. **Printing the bearer was enough.**

**The rule now: both children run with `stdout` and `stderr` on
`subprocess.DEVNULL`.** Not bounded, not windowed, not held and discarded — no
descriptor, no capture file, no buffer, and no variable anywhere in the module
holding a byte a child wrote. That is what makes this enforceable rather than a
discipline: a later edit cannot interpolate a value that does not exist.
`MAX_DIAGNOSTIC`, `MAX_VERIFICATION` and `_window` are DELETED rather than
tightened, because a ceiling on an amount that never crosses is a ceiling on
nothing, and a focused case asserts their absence so re-adding one is a
deliberate act rather than drift back toward this finding.

### Why the review's other branch was not available

The review offered making the credential unavailable to provider-edited
verification code. It cannot be done from inside this container, and the reason
is the accepted posture rather than effort: `RESTRICTIONS` fixes `--cap-drop
ALL`, `--security-opt no-new-privileges`, one fixed `65532:65532` and a
read-only root, so this adapter has no mount namespace to alter, no second
identity to drop to, and no way to revoke a read-only bind mount. The argument
does not even depend on those details — **whatever the provider can read, a
child of this process can read, because they are the same uid in the same
namespace; and if the provider could not read it there would be no turn.**

And the provider's own diagnostic is not covered by that branch at all. The
provider authenticates with the bearer, so its stderr is an untrusted sink
whatever is done about the verification command.

### Why redaction was rejected, on principle rather than on difficulty

A redactor has to know the bearer's bytes to remove them, which means reading
them, which the confirmed boundary forbids — and a program that holds the
bearer in memory in order to scrub it is one formatting bug away from being the
discloser. A redactor that does NOT read it cannot know what to remove. There
is no enforceable source of truth here that does not violate the no-read rule,
which is what the review said and is why this record does not claim one.

### Rejected: removing the provider's credential link before verification

Considered as subordinate defence in depth and NOT DONE. It would take away one
name pointing at the slot while the slot's own fixed absolute path stayed
readable to anything running as this uid, so it narrows nothing an attacker
relies on — it only makes the module look defended. This is the same shape the
third round already rejected when it declined to fix the capture problem by
moving the capture directory: **a defence that depends on the child not knowing
a path is not a boundary.** Applying that rule to one's own preferred addition
is the only way it means anything.

### What the evidence carries instead, and it is not nothing

`verification.txt` carries the frozen command — which the OPERATOR wrote into
`/input/task.json` and this adapter read from a read-only mount — the ending,
which came from `wait` rather than from a stream, and an explicit statement
that the output is withheld and why. That last part is load-bearing: a reader
who does not know the output was withheld reads its absence as a command that
said nothing. `result.json` carries the exit status and the same argv.

Deliberately NOT carried: stream byte counts. A count is a scalar derived from
untrusted data, it would have to be defended, and it buys almost nothing over
the exit status. The boundary is easier to hold and easier to review when the
answer to "what of the child's output reaches the proposal" is *nothing*.

### A third sink the review did not have to name, and it was the worse one

`recap` is composed from `disposition` and `why`, and `why` carried the
provider's stderr — so the diagnostic reached the worker's own
`/output/output.json`, the PROTOCOL document the manager correlates and
collects, not only the application-metadata `result.json` the review named. Both
sinks are closed and both have a case.

### The deliberate cost, recorded rather than shrugged off

A failed provider turn now says only that it failed. That is a real loss for
bringing up the first live turn under W39364, and it is named here so nobody
rediscovers it as a surprise. It is not a reason to reopen the boundary: the
parent finding already rules that the evidence carries no provider diagnostic,
and the operator's authoritative signal was always its own rerun of the frozen
command against the collected candidate, never this file. **If W39364 finds it
genuinely cannot bring up a live turn without provider diagnostics, the answer
is an explicitly operator-authorized diagnostic mode as its own later-pass
Work** — not publishing untrusted bytes by default. No such Work is minted here
because the need is conditional and W39364 will meet it directly if it is real.

### Where provider-authored bytes DO still cross, and why that is different

The candidate tree, `change.patch` and `changed_paths` carry bytes and path
names the provider wrote. That is the deliverable, not the evidence: a proposal
exists to be read by a human before it enters anything, and nothing this adapter
can do would stop a provider that decided to write the bearer into a source
file. What the boundary claimed, and what was false, is that the EVIDENCE files
carry no credential content — and evidence files are the ones that get pasted
into logs, tickets and dashboards without the reading a candidate tree gets.

### W39770 is accepted, and the image stopgap is gone

`detail work=W39770` reports it closed `satisfying` at sequence 42402 with a
rationale assigning this removal to W39357. `COPY scripted_agent.py` is removed
from `Dockerfile.claude`, and the image gate now asserts the module's ABSENCE
from the artefact while still holding the seam property that makes the absence
safe — so a regression in `baton_worker.py` fails in that gate with actionable
prose rather than as a `ModuleNotFoundError` in a live turn.

### Open, unchanged

The first live provider turn — W39364.

## 2026-08-30 — follow-up correction under W44424 (`baton.claude`)

**This record's Work is closed and stays closed.** What follows is explicit
follow-up history against terminal evidence, per `AGENTS.md`, rather than a
rewrite of anything above it. The correction belongs to **W44424**, which is
its own Work and is deliberately NOT bound here — a record has exactly one
Work, and this one is W39357's.

### Superseded: the task identity was coerced before it was matched

`_task` read `_TASK_ID.match(str(document["task_id"]))`, so a JSON number
reached the regex as its decimal spelling and passed. **The identity of a
versioned document was decided by a coercion this module performed rather than
by what the document says**, and every other member in the same function is
held to its type before its shape.

**The rule now:** exact `str` before the match, which is the rule the sender
already applied.

### How it was found, because that is the part worth keeping

Not by reading this file. W39358's operator reads the same frozen task on the
way in, to move a refusal earlier than a failed provider attempt — and it
refuses a numeric identity. The two ends therefore disagreed about the same
document while an agreement test compared the regex TEXT and the closed member
set and reported them identical.

**A test that compares two constants is not a test that two predicates agree.**
That test now asserts the asymmetry explicitly instead of implying parity, and
this change removes the asymmetry it was asserting. The reviewer filed the
receiver half as W44424 rather than letting the operator Work edit this closed
child's file, which is why the correction arrives here as its own history.

The regression is `test_a_task_identity_is_text_before_it_is_matched` in
`tests/manager/test_claude_agent.py`, filed additive by the reviewer and now
passing.
