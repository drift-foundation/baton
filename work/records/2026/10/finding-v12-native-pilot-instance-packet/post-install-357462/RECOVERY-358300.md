# The review-only recovery route, traced — and the exact blocking invariant

Supersedes `RECOVERY-358239.md`, whose categorical "the capability is ABSENT"
and "a fresh Job necessarily repeats implementation" conclusions were **not
established**. `review-2026-10-23T04-34-12Z.md` is right: I reasoned from
**absent function names** rather than from the supported composition's own
gates. That is a weak argument, and the reviewer's candidate route is real.

**What I got wrong, specifically.** I searched for `adopt`, `retry_review`,
`rereview` and `freeze_checkpoint`-as-adoption, found none, and concluded
absence. But the route does not need a function with one of those names: a
**review-only Job bound to the same Work** could reach the same line, because
the line is keyed on Authority and Work rather than on the Job. Not finding a
name is not finding a wall.

## The route is real as far as the line

Confirmed by reading the reviewed build:

- `review_cycles.create_line` (`:1495`) is documented *"Create or recover the
  one persistent line for Authority and Work"*, and `line_id = _id("line",
  {"authority_uuid": …, "work_id": …})` — **no Job ID**. A review-only Job on
  the same Work recovers **this** line.
- `_same_assignment` (`:1186`) compares `authority_uuid`, `work_id` and
  `generation`. **No Job ID.**
- `attach_review` (`:2125`) gates on a `frozen` checkpoint, line/profile match,
  that assignment match, the producer belonging to the same line, and
  **independence** — the reviewer's worker, participant and principal must all
  differ from the producer's. None of those compare Job ID either.

So admission, claim and existing-line recovery are **not** where this stops,
and my earlier document was wrong to imply they were.

## The first exact blocking invariant

`attach_review` at `:2168`:

    if line["state"] != "review-ready" \
            or line["current_checkpoint_id"] != checkpoint_id:
        raise ContractRefusal("refused", "precondition",
            "review attaches only to the current review-ready checkpoint")

and on a successful attach, `:2206`:

    UPDATE review_lines SET state = 'reviewing' …

**The faulted review already consumed the line's `review-ready` state.** The
manager attaches the reviewer and moves the line to `reviewing` *before* the
container runs; the adapter then refused the declaration and the worker
faulted. So the line is now `reviewing`, and a second attachment — from any
Job, including a review-only one on the same Work — is refused by that
precondition.

**And nothing returns it.** The only write of `'review-ready'` in the module is
at `:2114`, inside **`freeze_checkpoint`** — a line becomes review-ready by
**freezing a new checkpoint**, which means producing a new implementation
result. There is no `detach`, `abandon_review`, `release` or `reopen` entry
point: the module's abandonment family is
`abandoned_correction_of` / `restore_abandoned_correction` (`:2957`, `:3104`),
and `restore_abandoned_correction` returns a line to **`correction-ready`**
(`:3648`) — the *correction* path, not `review-ready`.

**This is a state-machine invariant, not a missing helper**, which is why
searching for names was the wrong method and why the answer is now narrower and
better founded.

## The minimal missing capability, stated precisely

One supported operation that, for a line in `reviewing` whose attached review
attempt **ended without a verdict**, returns the line to `review-ready` against
the **same current checkpoint** — preserving the frozen checkpoint, the
producer's writer identity and revision, and the independence record of the
failed attempt as history.

It is the direct analogue of what already exists for corrections:
`restore_abandoned_correction` does exactly this shape for `correction-ready`.
So the missing piece is a **review-side counterpart of an operation the product
already has**, not a new mechanism. That is a materially smaller and more
credible claim than "no adoption path exists".

**Not built, and not proposed as product work here.** It needs its own bounded
Work, dependencies and acceptance, and only if the owner selects retained
adoption.

## What I could not establish, named rather than glossed

- **Whether the attachment actually committed.** I am inferring that the line
  reached `reviewing` from the fact that the worker started its exchange
  protocol (`receipt.json` accepted, `state-describe.json` answered) — the
  container ran, so the manager had already attached. **I did not read the
  store to confirm the line's current state**, because that is a raw-store read
  nobody authorised. If the attachment did *not* commit, the line may still be
  `review-ready` and a review-only Job may attach without any new capability.
  **That single readback decides between the two outcomes**, and it is the
  cheapest next step.
- **Ending, publication and receipt attribution** for a review-only Job. I did
  not trace these, so I am not claiming the route is otherwise clear — only
  that the line-state gate is the *first* thing it hits.

## Corrected bottom line

Not "the capability is absent". Rather: **the existing composition can reach
the same line from a different Job, and the first thing that refuses is the
line's own `reviewing` state, for which the product has a correction-side
restore but no review-side equivalent.** Whether even that is needed depends on
one unread fact — the line's current state — which a supported read-only
inspection should settle before anything is selected.
