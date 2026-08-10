# A directed message can exist with no publication record

Logged before any workaround, per AGENTS.md. Not fixed: the WIP commit
boundary froze edits, and the fix is a schema change that would break the
human console again (see the deployment note below).

## What the contract says

`work/finding-scoped-audiences/FINDING.md`:

> Every directed message belongs to an immutable publication record, including
> a single-recipient send and a response message created by `reply`. There is
> no private-message storage special case for later audience authorization.

## What is actually true

    messages.publication_id TEXT REFERENCES publications(publication_id)

Nullable. Nothing refuses a NULL, and `doctor` has no check for one — its four
publication checks all validate rows that HAVE a publication and say nothing
about rows that do not.

## The cause, corrected

FIRST DIAGNOSIS WAS WRONG. I attributed the orphan to a peer build that
predated `publications` and passed the schema check anyway, and used that to
argue "protocol 10 is not one contract". The reviewer disproved it: the
pre-publication cutover executable was reconstructed byte-for-byte and REFUSED
to open the publication-aware live schema, reporting validation damage. It
published nothing. The schema check did its job.

The actual cause is in the current, publication-aware code:

    _impl.py:1963   Store.send   -> creates publications + publication_audience,
                                    passes the id to _insert_message
    _impl.py:2325   Store.reply  -> calls _insert_message directly, with no
                                    publication_id

So every response message `reply` creates carries a NULL link and delivers as
`audience: []`. I wrote that path and I wrote the contract it violates.

This is the acceptance path already pinned in
`work/finding-scoped-audiences/PLAN.md` — "Response messages created by
`reply` also receive their own single-recipient publication record; the claim
disposition remains their effectively-once operation key" — and no regression
exercises it. That is the real gap: not an unforeseen case, a written
requirement with no test.

How it surfaced: a live message arrived with `publication_id: None` and
`audience: []`, and `doctor` reported ok. The live instance contains such rows
right now.

## Why it is not cosmetic

The publication record is the CANONICAL audience. `_delivery` reads it to tell
a recipient whether work was shared, and the scoped-audiences finding names it
as what later audience authorization will read. A row without one:

- delivers `audience: []` — which reads as "nobody", where the truth is
  "unrecorded". A reader cannot distinguish the two, and the console shows
  neither, so shared work would silently present as private.
- has no frozen audience to authorize against, so any future
  participant-authorized reread has nothing to check.

The current fallback in `Store.publication_of` returns `([], False)` for a
NULL and documents it as "predates the record". That was written for rows
older than the publications table. It is now silently absorbing rows the
CURRENT code creates on every reply, which is what makes it a defect rather
than a documented legacy path — the comment describes a history that is no
longer the only way to get here.

## What a fix has to decide

1. One atomic single-recipient publication for each first committed `reply`,
   with a retry of that claim reusing the committed response rather than
   creating a second publication. The claim disposition stays the
   effectively-once key; the publication must not become a second one.
2. `NOT NULL` on the column, or a doctor problem, or both. NOT NULL is the
   real invariant, but it cannot be added while violating rows exist — they
   need a deliberate backfill or disposition plan, and deleting delivered
   messages to satisfy a constraint is its own harm.
3. Whether an orphan is a PROBLEM or a WARNING in doctor. It is unreadable
   audience, not corruption: the message is still claimable and closable.
4. Break-checked regressions on both the core and the packaged CLI.

Separately, and NOT the cause of this: the mutable `bin/baton` path and the
live authority were advanced while both were called protocol 10. That is a
real operational problem worth its own fix. I used it to draw a conclusion
about peer validation that the evidence contradicts, and it is recorded here
so the mistake is visible rather than quietly deleted.

## Deployment note

Any fix here changes the schema, and every protocol-10 schema change so far has
left Slawomir's console unable to open the mailbox until migrated in place.
That is tracked in the handoff and is his call, not something to bundle into a
defect fix.
