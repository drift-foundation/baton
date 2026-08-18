# Progress — contextual `say` prefill

Owned exclusively by the implementer (`baton.claude` under v11).

## Step 1 — W81 implemented (2026-08-17)

Claimed W81. Revalidation confirmed the pinned boundary after W76:
`Console.handle` still opens every `:` command with an empty buffer, and
the selected Threads row already carries the authority-local `local_id`
the pane renders. No authority or schema change.

### The seed

`_reconcile_say_seed` runs on every edit of the command buffer. It seeds
once, at the moment the buffer becomes exactly `say`, and only in a
detail view with one unambiguous selected Thread — root/list views and
Works with no selection invent no destination. The selector is the
row's `local_id`, never the label ordinal (W7 showed those diverge) and
never a canonical id the client reassembled. The seed ends with a space
so the caret lands where the next operand goes, and the assist stays
contextual (`required: body=`).

`filter`'s existing seed-on-first-space was the precedent for shape, but
the trigger differs because the finding says *typing exact `:say`*
seeds, with the trailing space produced BY the seed rather than typed.

### Why an explicit `thread=` has to displace the seed

This is the part that needed care rather than transcription. Paste into
a curses bar is indistinguishable from fast typing — there is no
bracketed-paste boundary here — so a pasted `say thread=T5 body=x`
NECESSARILY passes through the exact-`say` moment and picks up the seed.
Refusing to seed "when a thread= is already present" cannot work: at
that instant the pasted operand has not arrived yet.

So the client records the exact operand text it inserted, and when a
second `thread=` appears it removes precisely that text (and the space
it introduced) rather than guessing. The ruled "never duplicates or
overwrites an explicit `thread=`" therefore holds by construction, for
typed and pasted input alike, instead of relying on paste looking
different from typing. A seed edited away by hand stops being the
client's to manage.

The seed is a snapshot: it is captured at trigger time and never
recomputed, so moving the Thread selection while composing cannot
retarget a command already in flight.

### Evidence

New `tests/work/test_w81_say_prefill.py` (15): exact-`say` seeding, the
caret and contextual assist, many-Thread selection, the selector
round-tripping through `resolve_thread_selector` to the very Thread the
pane had selected, root/no-selection/no-Work cases, other verbs
untouched, pasted and typed explicit `thread=` displacing the seed,
repeated spacing and editing never duplicating, hand-edited seeds
released, selection movement not retargeting, refresh/resize leaving the
buffer alone, cancellation writing nothing, and delivery reaching only
the seeded Thread while the sibling Thread stays untouched.

Packaged PTY parity in `tests/work/test_tui_packaged.py` reads BOTH
facts off the same screen — the Threads pane's visible selector and the
command bar's seed — so it cannot drift with which Work sorts first.

Break-sweeps: removing the seed reds 6; disabling the explicit-operand
displacement reds 2; re-seeding on every keystroke (retargeting) reds 3.

### Two self-corrections worth recording

While writing the tests I asserted that typing `says` must not seed. It
does seed, because `say` completes first — but `says` is not a verb in
the grammar, so the assertion invented a requirement the finding does
not make. Replaced with the real property: every other verb reaches the
bar unchanged.

I also wrote an assertion ending in `or True`, which could never fail.
Replaced with the round-trip check described above. That is the second
vacuous assertion I have caught in my own work this session; both were
found by reading the test back rather than by it failing.

## Step 2 — W81 R1/R2: two integration boundaries (2026-08-17)

Both review defects reproduced from the committed tree before any edit,
and both come from my OWN later work interacting with this one — W123
added the Events tab after W81 was written.

**R1 — a quoted body containing `thread=` deleted the real seed.** I
used `count("thread=") > 1`, which is not operand-aware, so
`body="diagnostic contains thread=value"` looked like a second
destination and the seed was removed. The failure direction is the bad
one: a valid contextual reply silently became a command with no
destination at all.

Replaced with `_operand_starts`, which walks the buffer tracking quote
state and counts `thread=` only where a token actually begins outside
quotes. The bar is edited character by character, so this runs
constantly against INCOMPLETE input; an unterminated quote is therefore
treated as still-inside a value, which is the safe reading — it can
only keep the seed, never silently drop it. That asymmetry is
deliberate and is asserted.

**R2 — Events seeded a hidden retained Thread.** `_selected_thread_selector`
checked detail mode and the Thread cursor but not the active tab, so
typing `say` on the Events tab produced a destination the operator
could not see. It now requires the Messages tab as well.

### Evidence

Twelve new cases: a parametrised matrix over single quotes, double
quotes, multiple occurrences in one value, a trailing `thread=` inside
a value, and a genuine operand in three positions; an open quote
keeping the seed; escaped quotes not ending a value; the scanner
asserted directly so the rule is readable without reconstructing it
from console behaviour; Events inventing no destination and Messages
restoring the ordinary behaviour; and a seed in flight never retargeted
by a tab change.

While writing those I found that `[`/`]` are ordinary text while the
command bar is open — correct behaviour, since tab switching is a
view-level move — so that is now asserted rather than worked around.
Two of my first drafts were wrong about it, and one had an off-by-one
constant in the scanner assertions; both were my errors, not the
implementation's.

Break-sweeps: restoring the substring count reds 6; removing the tab
gate reds 1.

### Gate isolation

The full gate cannot run clean while W159 sits paused in the same tree:
its ruled blocking default refuses `request=` on unclaimed Work, which
119 pre-existing tests do. To verify W81 independently I temporarily
set that one default back to the pre-W159 asynchronous behaviour and
ran the complete gate: **978 passed, and the only failures were W159's
own 10 tests**, which correctly demand the blocking default. The ruled
default was then restored and the change re-verified. W81 and every
earlier item are clean; the outstanding failures are W159's collateral
and nothing else.

## Step 3 — W81 R3: stop maintaining a second lexer (2026-08-17)

Round two found the same class of defect I had just fixed, in the other
direction: `_operand_starts` treated every whitespace character as a
token boundary, including an ESCAPED one. So

    say thread=T2 body=diagnostic\\ thread=value

tokenizes for execution as one `body=` operand whose value happens to
contain `thread=`, but my scanner saw two operands and removed the real
seed — silently turning a contextual reply into a command with no
destination, exactly the R1 failure wearing a different hat.

The review's instruction is the important part, and it is right: do not
extend an approximate lexer one escape case at a time. Detection now
reads through `cli._partial_tokens`, the same partial-`shlex`
interpretation the parser and the command assistance already share, so
the two cannot disagree about quotes, backslashes, or escaped
whitespace. An escaped spelling that `shlex` RESOLVES into a genuine
`thread=` operand is counted, because by then it genuinely is one.

The fail-safe direction is kept and documented: when the line cannot be
tokenized even under the quote rules, the seed is left alone, because
the failure being guarded against is silently deleting a destination.

### Evidence

Nine new cases plus a property test. The direct reading covers quoted
values, escaped whitespace in both directions, an escaped spelling that
resolves into a real operand, and incomplete input; the parametrised
console cases prove the buffer behaviour; and one test asserts the
PROPERTY the reuse buys — that for every shape, the number of operands
detected equals the number `shlex` hands to execution. That last one is
what would catch the next divergence without anybody having to think of
the specific escape.

One of my assertions checked the raw buffer for `thread=T7` when the
buffer legitimately held the escaped spelling `thr\ead=T7`; corrected
to assert what execution will see.

Break-sweep: reinstating the approximate lexer reds 14.

Gate, isolated the same way as step 2 (W159's paused default temporarily
set back to the pre-W159 asynchronous behaviour): **983 passed, only
W159's own 10 tests failing**, then the ruled default restored and
re-verified.
