# Progress

## Step 1 — the counts (2026-08-18)

The canonical Thread read gains `total`: the whole-Thread Message count,
read inside the SAME snapshot transaction as the existing whole-Thread
`new`, so the pair can never disagree with each other or with the page
they are rendered beside.

The heading renders `Messages (total/unseen)` from those two facts. It
formatted `len(messages)` before — the loaded page — which is why a
Thread of forty read `Messages (10)` at a page size of ten. Nothing
infers the total from page length, sequence numbers, or cursor presence,
because none of those can express it: a page is a window, and its length
is a fact about the window.

The `(n: older)` continuation stays exactly where it was. Paging is a
different question from content, and the two now read as different
things because they are.

`PROJECTION_VERSION` 9.0 -> 9.1. Additive: the field is new, no existing
field changed meaning, so a 9.x consumer keeps working.

## Step 2 — acceptance

`tests/work/test_w29_message_counts.py`, 13 checks across both layers.

The projection half covers the defect directly (a page smaller than the
Thread), stability across pages and both paging directions, a
one-message Thread, marking seen moving only the second number, a new
Message moving total and unseen together, two viewers agreeing on total
and disagreeing on unseen, and — deliberately — a page whose length
EQUALS the total, because that is the shape in which a page-derived
heading looks correct and passes review.

The heading half drives the real render: the pair, zero unseen after
marking, a Thread larger than one page, the continuation surviving
beside the counts, a narrow terminal keeping both numbers, and paging
the pane changing neither. That last one compares the COUNTS rather than
the whole line, because the focus marker beside them legitimately moves
with pane focus and is a different fact.

Break-sweeps: restoring the page-length heading reds 5; computing
`total` from the page instead of the Thread reds 4 — the two layers are
pinned independently, so a regression in either is attributable.

## Step 3 — review round 1

One added regression found a real defect. With no match, my Enter path
adopted nothing and then executed whatever was in the buffer — the
pre-search draft, which the operator cannot see, because the row is
showing the search prompt. Enter with nothing chosen is now inert and
stays in search; Esc still restores that draft deliberately. Reverting
the guard reds the regression.

## Collateral, and one guard of mine that was too blunt

Six existing assertions named the old `Messages (N)` form and now name
the pair. `test_w176`'s empty-page stub gained `total`/`new`: it
synthesizes a snapshot, so it has to carry what the projection returns —
making the renderer defensive instead would have hidden a genuinely
missing field.

Separately, the gate went red on `README.md`, which now carries a
screenshot at `assets/images/baton-tui.png`. That is not this Work's
change, and it is not a defect: my own W103 guard forbade the substring
`baton-tui` anywhere in an active document, so a FILE NAMED after the
product read as an instruction to run the retired binary. The guard now
strips markdown link and image targets before scanning — a document may
name a file, it may not tell somebody to run the retired thing. Verified
by adding real prose that does exactly that and watching it red.

## Evidence

- Gate: **1188 passed** + 14 serial + acp 38/38 on 32 cores.
- Break-sweeps: 3, each reddening its own layer.
- Whitespace check clean.
- No database schema change.
