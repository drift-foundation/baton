# Durable development-run logs

## 2026-09-17 — confirmed owner decision

Slawomir: "I'm not concerned about logged credentials - this is dev use - and credentials aren't printed out anyway. We need to capture evidence so we don't chanse tails."

For the owner's v12 development deployments, retain raw process stdout/stderr and available native provider/session logs as attempt-correlated evidence. Sensitive content potentially appearing in those streams is accepted for this private development use. Credential isolation, filtering, redaction and a normalized event vocabulary are not prerequisites for capture. This is not a factual guarantee that arbitrary process output cannot contain credentials, and does not request reading credentials merely to log them.

This explicitly supersedes, for these development deployments, the September 1 W61599 prohibition on durable raw output, the September 14 deferral of the basic durable log sink, and the W39357/W43972 credential-free-log restrictions to the extent they require discarding these streams. Preserve historical decisions and accepted evidence; broader public/distributed logging policy and rich viewer features are unchanged.

Observed current gap: v12/worker/claude_agent.py discards provider stderr and verification streams through DEVNULL; structured provider output is consumed without a durable raw transcript. W197661 exposed a second gap: an integration startup refusal emits no diagnostic. Capturing output alone cannot recover a diagnostic that was never emitted. The stopped first-Job instance and its unresolved attempt remain evidence, not an authorized repair target.

## Required outcome

- Create stable manager-owned attempt log locations before worker startup. Retain separate stdout.log/stderr.log (or clearly identified per-process equivalents), plus available native provider/session output. Distinguish worker wrapper, provider and verification streams without dropping any of them silently.
- Capture incrementally and preserve partial evidence on error, abnormal termination and restart. Report missing, failed, truncated or incomplete capture honestly; never represent missing logs as an empty successful run.
- Keep protocol frames/input/results distinct from raw output. Tee protocol-bearing or parsed output without changing its bytes or mixing diagnostic prose into it. Logs are evidence, not workflow instructions or success receipts.
- Make log locators and a simple read/follow command available without requiring Docker inspection. No rich TUI, search or formatting project is needed.
- Emit actionable bounded startup diagnostics for refused worker/provider/integration launches; preserve correlation rules and never fabricate protocol events from invalid input.
- Keep logs in the owner's private attempt boundary. No new public publication, credential-file harvesting, production restart, submission or recovery is selected.

Acceptance uses deterministic providers and real affected capture/transport/custody paths: visible output before completion; stdout and stderr retained on success/failure; early launch failure; partial logs after stop; restart preservation; concurrent attempt separation; unchanged protocol parsing. No live model is needed. Necessary narrowly scoped local container checks may be used for capture/mount/termination behavior that process fakes cannot establish; name their purpose and retain their evidence.

W197661's assembled-deployment smoke is related but remains separately owned. Coordinate shared paths and consume its evidence; do not interrupt its active claim or silently change its assignment.


## 2026-09-18 UTC — owner assigns logging to tuner

Slawomir selects baton.tuner to implement W198667. Logging was queued and unclaimed at snapshot198670. This supersedes the initial baton.impl scheduling selection only; the capture contract remains unchanged. Coordinate shared paths with W197661 before edits and pass the completed candidate for independent review.


## 2026-09-18 UTC — explicit owner file-ownership constraint

Slawomir: "key is Claude cannot override files of Codex". Claude must not overwrite Codex/tuner-owned files or their changes. Before parallel edits, record exact path ownership and communicate it to the other active handler; a needed shared-path change requires an explicit coordinated handoff before editing, not an overwrite followed by reconciliation. Preserve append-only reviews and each author's progress. This applies to the logging/assembled-smoke overlap in particular.


## 2026-09-18 UTC — owner retains Claude assignment

Slawomir: "wait, if coordination is a pain we can just leave it to Claude". Retain baton.claude implementation through baton.impl. This explicitly supersedes the tuner assignment above before any reroute occurred; snapshot198679 confirms Work remains queued/unclaimed on baton.impl. Do not add parallel tuner execution. The owner constraint against overwriting Codex-owned files/changes remains in force, as do independent review and explicit shared-file handoffs where required.

## 2026-09-18 — partial independent review, claim198746

The integration_entry diagnostics slice is accepted at the exact two hashes
in review-2026-09-18T00-44-19Z.md. Six focused independent checks pass; existing
test assertions are unchanged. No durable capture, native-log retention or
read/follow path has been delivered, so this is not Work completion or full
startup-path coverage. The absence of a durable manager-owned mount identifies
necessary authorized implementation, not a need for another design approval.
Continue the selected complete outcome, enumerate/coordinate exact shared
paths, and preserve protocol/result separation and honest partial-capture
status. W197661's accepted immutable images still contain the older integration
entry; its evidence is not rewritten by this new source change. Production
restart/recovery/resubmission remains excluded.


## 2026-09-18T01-04-54Z — independent review198868 requests corrections

31 focused tests pass, but deterministic probes establish that failed capture without a file becomes absent, a partial stream becomes whole-stream captured through read/follow, permission errors become absence, and a stream symlink reads a sibling attempt file. The claimed honest-reader/private-boundary behavior is not established by the current delivery slice. See `review-2026-09-18T01-04-54Z.md` and `REVIEW-EVIDENCE-198868.json`. Prior diagnostic acceptance stands; complete the remaining authorized capture/lifecycle/command scope after fixing these defects.


## 2026-09-18T01-15-42Z — review198940: status-sidecar defects remain

29 delivery tests pass, but synthetic probes reproduce status-symlink false completeness, staging-symlink overwrite outside the attempt room, lost concurrent stream declarations and a malformed status entry crashing locators. The claim that R1/R2 are fully corrected is superseded: direct stream/native checks improved, but status metadata bypasses those boundaries. See `review-2026-09-18T01-15-42Z.md` and REVIEW-EVIDENCE-198940.json. Complete the full capture/lifecycle/command scope under existing authority after correction.


## 2026-09-18T01-25-03Z — review199005: reader operands and writer failure ownership

38 tests pass, but independent probes show read with ../other escapes the attempt room, failed exclusive staging creation deletes the preexisting entry, and an unchecked short write publishes corrupt status while returning success. These prevent full acceptance of the claim198977 corrections. See `review-2026-09-18T01-25-03Z.md` and REVIEW-EVIDENCE-199005.json. Complete the authorized capture/lifecycle/command outcome after correction; no new scope gate.


## 2026-09-18T02-02-21Z — review199229 accepts bounded correction; capture still incomplete

At the exact two hashes in `review-2026-09-18T02-02-21Z.md`, all 59 tests and three independent prior-defect probes pass: stream traversal refuses, unowned staging survives and positive short writes complete correctly. This supersedes the outstanding R1/R2/R3 correction status in review199005, not the unfinished R4. Continue the full launch/provider/wrapper/native/CLI wiring and focused matrix under existing authority; test/image breadth is implementation work, not a new gate. Canonical author claim is 199159; the latest EVIDENCE-199021 filename/content mislabels this episode and needs an append-only provenance correction.


# Provenance correction — appended, never rewritten (claim199285)

Review 2026-09-18T02-02-21Z is right and this is the correction it asks for.

`EVIDENCE-199021.json` in this dossier, and the PROGRESS note and thread message
that accompany it, name the author claim as **199021**. That is W197661's claim
number. Canonical `work-events` identifies this Work's implementation episode as
**claim199159** (2026-09-18 01:50:12–02:00:22 UTC).

The mislabelled file keeps its name and its bytes, as history. Everything it
records about the code is unaffected — the reviewer independently re-ran the 59
tests and the three probes against the two candidate hashes and accepted them.
This is a provenance correction and nothing else.

**And one explanatory claim in it is corrected too.** That note described the
per-call staging identity as making the name "unguessable". It does not: the pid
plus a counter provides per-call NAMING, not secrecy. What makes the act safe is
`O_CREAT|O_EXCL|O_NOFOLLOW` and the creation-ownership tracking, and the
unguessability sentence was my gloss rather than the property.


## 2026-09-18T02-31-51Z — independent review199387: full delivery not accepted

Review `review-2026-09-18T02-31-51Z.md` and `REVIEW-EVIDENCE-199387.json` supersede the claim199285 R4_COMPLETE interpretation. All candidate hashes match and 86 focused tests pass, but production image packaging omits the writer, ordinary integration startup bypasses capture, wrapper stdout and real native-session retention remain missing, and a reproduced failed child launch is falsely labelled captured. Operator invocation/follow delivery also needs completion. Existing authority covers correction and deterministic verification; no new scope or test permission gate. Preserve prior evidence and selected immutable images.


# Completion claim corrected — appended (claim199562)

Review 2026-09-18T02-31-51Z is right and this is the correction.

My claim199285 handoff and `EVIDENCE-199285.json` are headed **"R4 IS COMPLETE
AND WIRED END TO END"**. That label is withdrawn. Those bytes keep their name
and their hashes as history — the eleven candidate hashes matched and the
reviewer re-ran 86 tests against them — but the completion claim over them was
wrong, and five things it covered were not done:

1. neither production recipe carries the shared writer, so the fixture's
   successful smoke proves nothing about either supported image;
2. `integration_entry.main`'s ordinary branch never enters the wrapper, so the
   original integration startup diagnostic can still vanish with its container
   — which is the exact incident shape this Work exists for;
3. the wrapper omits stdout, and the selected scope is stdout AND stderr;
4. native session retention is a constant and an empty directory, not a
   retention;
5. **and a defect I shipped**: `_ran`'s `finally` declares `finished` even when
   the child never started, so an injected `FileNotFoundError` leaves both
   verification streams reported as captured, zero bytes, with the prose "the
   writer saw this stream to its end". A failure to start reported as a
   complete capture is the exact sentence this vocabulary exists to forbid.

The operator entrypoint is also advertised and not installed.


## 2026-09-18T03-10-39Z — review199623: byte capture and native durability incomplete

`review-2026-09-18T03-10-39Z.md` and REVIEW-EVIDENCE-199623.json supersede any full-acceptance interpretation of claim199562. Fourteen hashes match and 181 tests pass, but binary protocol stdout bypasses capture. Independent native probes show flattened-name collision and silent truncation. End-only native copying does not meet incremental crash-survival scope; capture failures and source confinement also require correction. Complete the already-selected operator follow loop without another selection gate. Historical completion withdrawal is accepted.


## 2026-09-18T03-27-44Z — review199735: native poll duplication and premature follow completion

`review-2026-09-18T03-27-44Z.md` and REVIEW-EVIDENCE-199735.json supersede full-correction claims in claim199683. Eleven hashes match and 109 tests pass. Actual _ran_provider probe retains abc seventeen times because the returned offset map is discarded. Follow emits only the first bounded slice of a completed stream and exits immediately on absent streams. Native failure/confinement completion remains required. Continue existing scope without another permission gate.


## 2026-09-18T03-39-32Z — review199814: poll duplication fixed; native restart and UTF-8 follow incomplete

`review-2026-09-18T03-39-32Z.md` and REVIEW-EVIDENCE-199814.json confirm five hashes and 119 passing tests. Original multi-tick abc duplication is fixed. Completed €x with follow bound1 returns no text and success; native fresh offsets append duplicate bytes and truncation silently drops new bytes with no failure. Complete these existing restart/honesty requirements and distinguish root absence from capture failure.


## 2026-09-18T03-48-00Z — review199876: UTF-8 probe fixed, native generations still duplicate/drop

`review-2026-09-18T03-48-00Z.md` and REVIEW-EVIDENCE-199876.json confirm four hashes, 128 passing tests and correct €x output at follow bound1. Native repeated truncation ticks create duplicate #2/#3 copies; fresh offsets after source changes silently retain no new bytes with no failure. Persist/recover source-to-generation association and disjoint naming under existing scope.


## 2026-09-18T03-52-05Z — claim199918: the binding is durable, and one probe found a third defect

Answering `review-2026-09-18T03-48-00Z.md`. The source-to-generation binding now
lives in a record inside the native corner rather than in a per-run dictionary
and a local variable, so repeated ticks after a rotation resume the same
generation and a restart recovers it from disk. Generation names use `%23`,
which no flattened source name can contain.

Running the review's second probe exposed a defect **neither of us had named**:
a source rewritten in place at the same length is the same device, inode and
size, so identity and length between them see nothing at all. The record keeps a
bounded digest of the retained head, which is what notices. The bound is stated
rather than hidden.


## 2026-09-18T04-07-54Z — review199997: durable-record failure and confinement defects

`review-2026-09-18T04-07-54Z.md` and REVIEW-EVIDENCE-199997.json confirm four hashes and 143 passing tests. Failed metadata replacement is ignored; fresh-map recovery duplicates suffix bytes (abcdefdef). A matching synthetic record with destination ../escaped writes outside native with no failure. Correct data/record recovery and validate/confine record/staging operands within existing capture scope.


## 2026-09-18T04:34Z — claim200182: the record is input, and the commit window is recoverable

Answering `review-2026-09-18T04-07-54Z.md`. Both findings were defects in what I
shipped one claim earlier.

**The record was trusted as data.** `_read_retention` accepted any JSON object
and `_destination` used its nested `destination` straight in an `os.open`
relative to the corner, so a record naming `../escaped` had the source's bytes
appended outside it with nothing declared. `O_NOFOLLOW` governs the final
component only and `dir_fd` resolves `..` like any path does — a
descriptor-relative open is not confinement; the name is. The record is now
validated whole, entry by entry, with a bad entry dropped rather than taking the
provable ones with it.

**The write failure was discarded and the window was not recoverable.**
`_write_retention` could return `False` and the caller ignored it, so a record
that never reached disk was no failure at all; a fresh map then trusted the
stale offset and produced `abcdefdef`. I also described an atomic replace of the
record as a transaction over the separately appended data, which it is not. What
is true is narrower and is what the recovery now rests on: the bytes go down
first and the record follows, so the destination can only ever be *ahead* — and
being ahead is a fact on disk, believed only when the retained head and the
source's agree over the reconciled length.


## 2026-09-18T04-53-08Z — review200300: validation can throw; retained FIFO can block

Confirmed by baton.rvpc: both claim200182 hashes match and 162 focused tests pass, including earlier correction cases. Actual _retain_native calls with superscript-digit or overlong generation suffixes raise ValueError instead of declaring invalid metadata. A valid record pointing at a retained FIFO blocks the data open; bounded reproduction was killed/reaped after two seconds. See `review-2026-09-18T04-53-08Z.md` and REVIEW-EVIDENCE-200300.json. This supersedes any full-correction interpretation of claim200182; complete total metadata validation and regular/nonblocking data-descriptor acquisition within existing scope. No product changes by reviewer; prior evidence preserved.


## 2026-09-18T05:10Z — claim200454: total validation, and both data descriptors

Answering `review-2026-09-18T04-53-08Z.md`. Both findings were defects in what I
shipped one claim earlier, and both reproduce exactly as the reviewer describes.

**Validation that could throw is not validation.** `_generation_of` asked
`str.isdigit` and then `int()`, and those are not the same question: the first
is true of the superscript `²` and of every non-ASCII decimal digit, and the
second is refused by Python's own 4300-digit conversion limit. Two record
documents well under `MAX_RETENTION` therefore raised `ValueError` out of the
drain instead of being discarded as malformed. The shape of a generation suffix
is now decided without converting it, and what cannot be recognised is dropped
and declared. The sweep the review asked for found one more of the same kind
that the reviewer did not name: a bound on BYTES is not a bound on DEPTH, and a
deeply nested document raises `RecursionError`, which is not a `ValueError`.
That escape existed at three decode sites in this file and is closed at all
three.

**A valid-looking record does not establish what a destination IS.** Every type
check in the retention path stood on a NAME. A record naming a destination that
is a fifo sent `_appended` into an `O_WRONLY` open with no reader, and the
reviewer's bounded probe was killed at two seconds — inside the drain
`_ran_provider` joins, so a tampered log file could strand the provider's own
turn. Both data descriptors are acquired nonblocking and validated as regular
files now, and the source's bytes are kept as their own generation rather than
lost because the corner was tampered with.

## 2026-09-18T05-32-05Z — review200560: previous corrections pass; aliasing and silent omission remain

Confirmed by baton.rvpc: claim200454 hashes match and 174 focused tests pass, including its generation/parser/FIFO regressions. Those specific earlier failures are corrected. Two actual _retain_native probes establish remaining gaps: a preexisting hard-linked regular destination appends the provider transcript to a synthetic sibling outside native with failed=[], and a regular provider file named .retention.json is silently omitted with reached=true/failed=[] and an empty destination. See `review-2026-09-18T05-32-05Z.md`, REVIEW-EVIDENCE-200560.json and review-probes-200560.py for inputs, conditional reachability and correction scope. Full acceptance remains pending; this supersedes any full-correction interpretation of claim200454 without withdrawing its demonstrated bounded fixes. No product/test changes by reviewer; preserve historical evidence.


## 2026-09-18T06:17Z — claim200870: an alias is not a name, and a reserved name is not a skip

Answering `review-2026-09-18T05-32-05Z.md`. Both findings were defects in what
I shipped one claim earlier, and both reproduce exactly as the reviewer
describes.

**R1. `S_ISREG` proves the opened thing is a FILE; it does not prove it is THIS
corner's file.** The reviewer hard-linked a file from outside the native
directory at `native/s.jsonl`, supplied a valid retention entry for it, and
watched a supposedly confined writer append the provider's 19-byte transcript
to BOTH names, returning `failed` empty and publishing a successful record.
`O_NOFOLLOW` refuses a symlink and a confined name refuses traversal, and
neither can see an alias — because a hard link is a second name for the INODE,
not for the path. The destination descriptor's own link count is the question
now, asked where the bytes would be written; a name this capture believes is
free is claimed with `O_EXCL` rather than adopted with `O_CREAT`; and a
destination it cannot own keeps its bytes, declares the uncertainty and sends
the source to its own generation — the same answer a truncation, a rewrite or a
fifo already gets, because from this capture's side they are one fact.

**R2. A provider file literally called `.retention.json` was silently dropped.**
`_walked` skipped that source name on the reasoning that it is this corner's
bookkeeping — but the bookkeeping lives in the DESTINATION and that walk is over
the SOURCE, so the only file that can ever match is a real one the provider
wrote. It was neither retained nor reported: `reached` true, `failed` empty, the
corner empty. A capture whose entire vocabulary exists to tell *missing* from
*empty* cannot have a filename it quietly refuses. The NAMESPACE answers it
instead of a skip: a flattened name colliding with the record or its staging has
its leading `.` escaped as `%2E`, so the file is retained as
`%2Eretention.json`, resumed from its own record across a restart, and held
apart from a provider file really called `%2Eretention.json` — which becomes
`%252Eretention.json`, because a literal per-cent is already `%25`. That also
closes the half the reviewer asked about: those names were previously refused by
`_confined` as destinations, so even when one was retained it could never be
resumed from its own record.

## 2026-09-18T06-27-53Z — review200927: native fixes accepted; shared capture gaps confirmed

Both candidate hashes match and 843 focused tests pass across two runs. Prior alias/reserved-name probes now behave correctly, accepting those bounded fixes. Actual shared _Captured probes establish a FIFO blocking append_writer and a hard-linked stream modifying a synthetic sibling outside the room; the native acquisition checks do not cover this shared opener. Ordinary successive writers also retain the earlier finished declaration: follow reports firstsecond captured with more_may_arrive=false despite no completion from the second writer. See `review-2026-09-18T06-27-53Z.md`, REVIEW-EVIDENCE-200927.json and review-probes-200927.py. Complete these original confinement/honesty/restart requirements; full acceptance remains pending. No product changes by reviewer; preserve historical evidence and coordinate shared-file ownership.


## 2026-09-18T06:37Z — claim201008: the native corner's lessons, at the boundary all six streams use

Answering `review-2026-09-18T06-27-53Z.md`. Both findings were mine and both
reproduce exactly as the reviewer describes.

**R1. I fixed the acquisition in the native corner and left the SHARED opener
every stream goes through untouched.** `attempt_log_format.append_writer` had
none of the three properties `_acquired` had just learned: a fifo at
`provider.stdout.log` blocked `os.open` waiting for a reader and the reviewer's
bounded child was killed at two seconds; a regular-file check was absent, so a
device would have swallowed everything; and a file hard-linked from outside the
room took the raw provider bytes while the capture declared `finished`. This
happens BEFORE the provider starts, and the wrapper's earliest output uses the
same primitive — so capture could strand the very startup it exists to record.
The three properties are at that boundary now, with one owner, which is where
they should have gone the first time.

**R2. A second writer inherited the first's terminal word**, on ordinary
sequential capture with no exotic input. The first declared `finished`, a second
appended beside it, and the real reader answered `captured`, "the writer saw
this stream to its end", `more_may_arrive: false`, over a file that was still
growing — so a follower exits before the later bytes arrive. Closing the second
with `declare(None)`, which explicitly asserts nobody knows how this ended, left
the stale word standing too. **A terminal word is about BYTES, not about a
name.** Acquiring a writer now clears a declaration that no longer describes the
file, so the intervening state is ABSENT — which the reader already calls
`live`, and which is the honest "we do not know". The earlier bytes are never
touched, a second writer that finishes normally still says `finished`, and a
clearing that FAILS refuses the handle rather than appending under somebody
else's ending.

**And the image evidence moved with the bytes.** `attempt_log_format.py` and
`baton_worker.py` both changed, so `fixture-199918`'s context copies no longer
describe this tree and its smoke no longer describes these bytes. A fresh
episode, `fixture-201008`, carries the current bytes and its own image
(`sha256:d1a9021c…`); its eight container checks all hold. fixture-199918 keeps
its own attribution and proves what it always proved.

## 2026-09-18T06-53-11Z — review201085: bounded fixes pass; cumulative capture loss is forgotten

Claim201008 hashes match and 858 focused tests pass. Shared FIFO/hard-link refusal
and reopening without stale finished are accepted. A real _Captured short-write
probe detects failed capture, then a successful append changes the combined log to
captured despite never restoring the missing bytes. Partial/truncated/unknown prior
captures similarly lose their uncertainty. See review-2026-09-18T06-53-11Z.md and
REVIEW-EVIDENCE-201085.json. Full acceptance remains pending cumulative honest
restart evidence; earlier bounded acceptances stand.


## 2026-09-18T06:59Z — claim201156: a new success cannot prove an earlier missing tail

Answering `review-2026-09-18T06-53-11Z.md`, which accepts the FIFO, hard-link
and stale-finished corrections and names one remaining defect — a consequence of
the last of those, and mine.

**Clearing the stale word was right; clearing it unconditionally destroyed the
earlier writer's evidence of LOSS.** The reviewer drove the real capture through
a short write it detected on its own, let a second writer append cleanly, and
watched the reader answer `captured`, "the writer saw this stream to its end",
over a file whose middle was never restored. `partial`, `truncated` and unknown
completeness all became whole-stream captured the same way.

**So the two facts are separated and both are kept.** The sidecar says what the
writer that published it saw — which is why clearing it keeps a reopened stream
honestly `live` while somebody is still appending. A new cumulative record says
whether the WHOLE FILE is complete, which no later writer can improve: only loss
is carried, so the ordinary clean restart writes nothing and still ends
`captured`, and a writer that finishes after a lost generation publishes the
worse of the two with a reason naming the earlier one.

**Both callers, because both reopen.** The provider capture and the wrapper's
own tee widen their outcome the same way, through one shared severity order that
belongs to the vocabulary rather than to either caller.

**The image evidence moved again.** `attempt_log_format.py`, `baton_worker.py`
and `claude_agent.py` all changed, so `fixture-201008`'s smoke no longer
describes these bytes; it keeps its own attribution. `fixture-201156` carries the
current bytes, image `sha256:23edb0ca…`, and its eight container checks all hold.

## 2026-09-18T07-09-49Z — review201212: normal carried loss fixed; restart failure paths remain

213 tests pass; candidate hashes match. Declared failed/partial/truncated survives
ordinary restart, accepted. Confirmed real capture/follow probes still produce false
captured after an unknown ending, ignored cumulative-write failure plus interruption,
and inaccessible cumulative history. See review-2026-09-18T07-09-49Z.md and
REVIEW-EVIDENCE-201212.json. This supersedes full-correction claims for claim201156
without withdrawing its bounded fixes. Complete the existing honesty scope.


## 2026-09-18T07:15Z — claim201274: three ways an unvouched-for stream still read as complete

Answering `review-2026-09-18T07-09-49Z.md`, which accepts the declared-loss
carry and names three cases it does not cover. All three were mine, all three
are in the cumulative record I introduced last claim, and all three reproduced.

**R1. An ending nobody declared was treated as a clean start.** `declare(None)`
is the interrupted writer — nobody said how it ended — and a corrupt sidecar
carries no `declared` member either. Both reached the branch for "no prior
loss", so a later clean append published `captured` over a prefix that never
reached EOF. What makes a reopen `partial` now is BYTES with no trustworthy
ending; an empty new stream is still a clean start, which is what keeps the
ordinary first capture free.

**R2. The persistence failure was ignored before the only evidence was
deleted.** `carry_declaration` called `_write_carried`, discarded its answer,
unlinked the prior sidecar and reported success — so an ordinary `OSError`
destroyed the record of a loss. The old evidence is not cleared unless the carry
succeeded, and the acquisition refuses instead. That contains the failure in the
LOGGING rather than in the child: a refused handle leaves the stream on
`DEVNULL` and declared, and the provider runs exactly as it would have.

**R3. An inaccessible history read exactly like an absent one.** `read_carried`
answered `None` for every open or read failure and for a record that was not a
regular file; only the malformed document was conservative, which is the
opposite of the rule. Genuine absence — `ENOENT` — is still `None`; anything
else is `failed`, because a history this capture cannot read cannot establish
completeness.

**The image evidence moved again.** `attempt_log_format.py` changed, so
`fixture-201156`'s smoke no longer describes these bytes and keeps its own
attribution. `fixture-201274` carries the current bytes, image
`sha256:f62733c6…`, eight of eight checks holding.

## Review201318 — three restart fixes accepted; malformed carried-state exception remains

226 tests pass and prior reviewer probes now report partial/failed as required.
Accept claim201274 bounded fixes. New actual _Captured probes with carried JSON
declared list/object raise TypeError before capture starts: read_carried performs
dictionary membership on an unvalidated value. See review-2026-09-18T07-23-56Z.md and
REVIEW-EVIDENCE-201318.json. Complete total malformed-state decoding and real-caller
failure containment; full acceptance remains pending this bounded correction.


## 2026-09-18T07:32Z — claim201391: a membership test on unvalidated JSON is not validation

Answering `review-2026-09-18T07-23-56Z.md`, which accepts all three restart
corrections and names one remaining containment defect. It was mine, and it is
the same shape this campaign already corrected once at `_generation_of`.

**`read_carried` decoded the record and then asked `said in SEVERITY`.**
Membership is a dictionary lookup, and a list or an object out of a JSON
document is unhashable — so `{"declared": []}` raised `TypeError` through
`carry_declaration`, through `append_writer` and out of the real `_Captured`
constructor, which runs BEFORE the provider starts. A capture that cannot set
itself up takes the workload with it, which is the containment rule this whole
vocabulary rests on, and the wrapper's tee reaches the same opener before its own
startup diagnostic.

`declared_state` is the one place that decides now: it answers a state only for a
string that is one, and `None` for every other JSON value. `worst` routes both
operands through it — the review asked for that boundary to be checked and it
had the identical assumption — and `carry_declaration`'s severity lookup is
guarded rather than relying on a caller's invariant. What cannot be read as a
state is the worst thing it could have been.

**The image evidence moved again.** `attempt_log_format.py` changed, so
`fixture-201274`'s smoke no longer describes these bytes and keeps its own
attribution. `fixture-201391` carries the current bytes, image
`sha256:f7bcc603…`, eight of eight checks holding.

## Review201428 — independent review signed off

235 focused tests pass; candidate and unchanged worker hashes match. Prior
malformed-record list/object probes now return failed without exceptions. This
closes the final review201318 blocker; prior accepted slices remain accepted.
See review-2026-09-18T07-40-38Z.md and REVIEW-EVIDENCE-201428.json for
exact hashes, evidence attribution and scope limits. Prepared filesystem work
passes to baton.decide for owner disposition; no Git or deployment action performed.
