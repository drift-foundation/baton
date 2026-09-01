# Progress

## 2026-08-31 — first implementer round (`baton.claude`, W55360 impl claim)

**Plan items 4 and 5 are done.** A nonzero provider turn now publishes one word
this module spells, and no byte the provider wrote reaches any sink. Files
changed: `v12/worker/claude_agent.py` and
`v12/python/tests/manager/test_claude_agent.py`.

The dated supersession was already pinned in both this record and W39357's
owning finding before I claimed, so item 4's first clause needed no edit from
me. I re-read it and implemented exactly what it says.

### What the adapter does now

`PROVIDER_ARGUMENTS` gains `--output-format json` and nothing else. A new
`_ran_provider` hands the child an ANONYMOUS PIPE for stdout — no path, no
file, nothing under the output root — and `DEVNULL` for stderr, then drains
that pipe in a thread beside the child, retaining at most
`MAX_PROVIDER_RECORD` (64 KiB) and reading the rest to EOF. `_ran` is untouched
and still gives the verification command `DEVNULL` on both streams.

On a NONZERO exit only, `_failure_reason` decodes the retained bytes as strict
UTF-8, parses one complete JSON object with an `object_pairs_hook` that refuses
duplicate members, requires a string `terminal_reason`, and looks it up by
EQUALITY in `PROVIDER_FAILURE_REASONS = {"api_error": "api-error"}`. Everything
else — overflow, empty, invalid UTF-8, malformed, trailing data, duplicated,
non-object root, non-string, unknown — answers the single word `unclassified`.
The result is published as `provider.failure_reason` and composed into `why`
and the recap; a clean turn publishes `null`.

Two properties are separate on purpose and both are asserted: the drain is
CONTINUOUS (so a chatty provider cannot wedge on a full pipe) and the retention
is BOUNDED (so it cannot decide this process's memory).

### The two existing assertions this moved, and the authority for moving them

Both are the ones the ruling names, and neither is weakened:

- the argv golden now expects `--output-format json` and a 7-word vector;
- `test_both_provider_streams_are_discarded_rather_than_captured` became
  `test_the_provider_stderr_is_discarded_rather_than_captured`, keeping the
  stderr assertion exactly as strict, plus a new
  `test_the_provider_stdout_is_a_bounded_anonymous_pipe` that `fstat`s the
  descriptor DURING the call and requires `S_ISFIFO`.

The verification-stream case is untouched, and a new case re-proves both its
streams are `DEVNULL` through the structured path as well.

### Twelve new regressions, and then a mutation check on them

`TheStructuredRecordIsMappedAndNeverPublished` drives a REAL child that writes
its record in several chunks, with a distinctive marker planted in every other
member, in member NAMES, in nested values, in an unknown terminal reason, and
in the bytes past the ceiling. The marker must appear in no proposal file and
no recap; `api_error` — the provider's own spelling — must appear in neither
either.

**Then the regressions were themselves mutated, because a suite that cannot
fail proves nothing.** Nine mutations of the module:

    CAUGHT  the provider's spelling is published instead of the mapped word
    CAUGHT  the overflow guard is dropped
    CAUGHT  duplicate terminal_reason keys are silently resolved
    CAUGHT  the retained ceiling is removed
    CAUGHT  the drain stops at the ceiling instead of reading to EOF  [hangs]
    CAUGHT  stderr is captured instead of discarded
    CAUGHT  the structured-output operand is dropped from the argv
    CAUGHT  the non-object root guard is deleted
    CAUGHT  the reason type guard is deleted

**Two of those started as MISSES and the tests were wrong, not the mutations.**

1. The overflow guard was unprovable: every flood case also failed to PARSE, so
   removing the check changed nothing. A case now hands `_failure_reason` a
   perfectly good `api_error` document WITH the overflow flag — the only shape
   that isolates it.
2. The duplicate-key guard was unprovable: my document put the marker LAST, and
   `json.loads` keeps the last of two equal keys, so it was unclassified with
   or without the check. The case now drives BOTH orders, and the earned-value-
   last order is the one that makes the guard load-bearing.

Two later mutations reported MISSED and are recorded as EQUIVALENT MUTANTS
rather than gaps: `document = {}` and `str(found)` both fall through to
`unclassified` anyway. Deleting those guards outright is caught.

### What this does not do, said where a reader will meet it

The module docstring now states plainly that `api-error` is DESCRIPTIVE: it
says the provider's own terminal record called the ending an API error, and it
is not evidence of an expired credential, a limited account, a missing scope or
a network fault. That is the honest result the ruling requires, and it is
narrower than what the two W51487 rounds wanted.

### Verification

    tests.manager.test_claude_agent                          81 tests, OK
      (68 before; 12 new plus the split stderr/stdout pair)
    plus test_worker_entry, test_worker_image and
      tests.tools.test_dogfood_operator                     403 tests, OK

No Docker build, no provider call, no credential read and no supervised attempt
were part of this proof, as the plan's own boundary requires. `result.json` has
no consumer to update: the operator explicitly never reads the worker's account
and only checks member presence.

Whitespace clean; no line I added exceeds the file width.

### State

Awaiting independent review, including the security review the record asks
for. Passing back rather than closing.

## 2026-09-01 — second implementer round (`baton.claude`, W55360 impl claim)

**Both [P1]s from `review-2026-09-01T03-35-56Z.md` are corrected**, in the same
two files: `v12/worker/claude_agent.py` and
`v12/python/tests/manager/test_claude_agent.py`. The review is right on both,
and on the same underlying point in each: a bound I wrote was not the bound I
claimed.

### [P1] The drain now ends on its own clock, not on EOF

The reviewer's mechanism is exact. EOF on the read end arrives when the LAST
writer closes it, and the provider's own children are writers this adapter was
never told about. My `reader.join()` therefore waited on a descriptor a
descendant held, AFTER `self._run` had already returned — so `PROVIDER_SECONDS`
bounded the provider and nothing bounded the turn. The timeout path was worse,
not better: `subprocess.run` kills its DIRECT child and nothing else.

What the reader does now:

- `os.pipe()`, and the read end is NON-BLOCKING. The loop is
  `select` with a slice, so no single step of it can block indefinitely.
- The provider ending sets a `threading.Event`, and the reader arms a deadline
  of `PROVIDER_DRAIN_SECONDS` (2s) from that moment. When it expires the
  reader RETURNS — whether or not it saw EOF, and whether or not bytes are
  still arriving. Two seconds is a grace for reading what is already in the
  pipe, not for waiting on somebody else's descriptor.
- A stream that was never proved finished is `partial`, exactly as an
  over-ceiling one is, and a partial record is `unclassified`. The document
  the leader wrote may parse perfectly; it still earns no word, because a
  prefix of a record is not a record.
- The close and the signal are in the `finally`, so a timeout or a missing
  executable starts the same clock.
- THE READER OWNS AND CLOSES THE READ DESCRIPTOR. The main thread closing an
  fd another thread may still be reading is a use-after-close, and leaking it
  is a descriptor held for the life of the turn; giving the one thread that
  touches it the job of closing it is neither.

`reader.join()` is now bounded by construction rather than by a second timeout
in the caller: every path through the loop re-checks the deadline, so the
thread terminates within the grace and the join returns with it. I chose that
over `join(timeout)` because a join that gives up still has to decide what to
do with a live thread and its descriptor, and this way there is no such case.

### [P1] The parser is strict and it is total

Both of the reviewer's records are real, and I confirmed both before changing
anything: `{"terminal_reason":"api_error","x":NaN}` published `api-error`, and
30,000 nested arrays inside the 64 KiB ceiling raised `RecursionError` out of
`_failure_reason` entirely.

- `parse_constant=` refuses `NaN`, `Infinity` and `-Infinity`. They are
  Python's extensions and are not JSON; accepting them let the PROVIDER decide
  what counted as a well-formed document.
- `RecursionError` is caught beside `UnicodeDecodeError` and `ValueError`. It
  is not a `ValueError`, which is why it escaped. A bound on BYTES was never a
  bound on parser DEPTH, and the function whose whole contract is to answer one
  of two words must not have a third exit.

Nothing about either correction interpolates an exception, a member, a length
or an excerpt: every path out of `_failure_reason` is still a constant written
in that file.

### The rename, and why it is not cosmetic

`overflowed` is now `partial`, at `_ran_provider`'s return and at
`_failure_reason`'s keyword. There are two ways the retained bytes can fail to
be the record — dropped at the ceiling, and a stream that never proved it
finished — and they mean the same thing to every reader downstream. One name
for one fact; `overflowed` would have been a lie in half the cases that now
set it.

### Regressions

Five new cases, plus two more inside the existing unusable-record table:

    a descendant holding stdout cannot outlive the bound   (seam, clocked)
    a descendant holding stdout publishes only the fallback (end to end)
    a timed out provider with a descendant still ends      (timeout path)
    Python's non-standard constants are not JSON           (NaN, +/-Inf)
    a record the parser cannot finish is unclassified      (30k nesting)
    "a non-standard constant"            in the real-child table
    "nesting the parser cannot finish"   in the real-child table

The descendant cases drive a REAL leader that `Popen`s a descendant it never
waits for. The descendant inherits the write end, WRITES THE MARKER, and lives
20 seconds — an order longer than the adapter is allowed to wait for it. So the
retained record genuinely contains the marker, and the assertions are a clock
AND a word: the call returns while the descendant is still holding the pipe,
the record is partial, `unclassified` is published, and no marker reaches any
proposal file or the recap.

### Mutation check on the corrected guards

Seven mutations of the module, all seven CAUGHT:

    CAUGHT  the drain deadline is never armed
    CAUGHT  an unfinished stream is reported whole
    CAUGHT  the provider-ended signal is dropped
    CAUGHT  the reader owns no deadline at all, only EOF
    CAUGHT  non-standard JSON constants are accepted
    CAUGHT  a parser recursion fault escapes
    CAUGHT  the partial guard is deleted

### Verification

    tests.manager.test_claude_agent                          86 tests, OK
      (81 before; 5 new methods and 2 new table cases)
    plus test_worker_entry, test_worker_image and
      tests.tools.test_dogfood_operator                     409 tests, OK

No Docker build, no provider call, no credential read and no supervised
attempt. Provider stderr and both verification streams are untouched on
`subprocess.DEVNULL`; nothing in this round widened what is read. No line I
added exceeds the file width and no trailing whitespace was introduced.

### State

Awaiting independent review again. Passing back rather than closing.

