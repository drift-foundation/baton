# Finding: forward Message pages advertise an unproved continuation

## Observed — 2026-08-17

While reviewing the bounded newest-first Message projection in W76, the exact
limit regression exposed an older pre-existing asymmetry. The reverse path now
queries `limit + 1` and advertises an older page only when the proof row
exists. The forward `thread(after=..., limit=N)` path still sets `next_after`
whenever exactly N rows were returned. If those are the final N rows, following
that token produces an empty page.

This did not invalidate W76: the v11 TUI's newest-first entry and older-page
path were the owned behavior and now have proof-row coverage. It is a separate
canonical JSON pagination defect and must not be hidden inside the completed
W76 contract.

## Proposed correction

Use the same proof-row rule in the forward direction: read at most `limit + 1`,
return no more than `limit`, and emit `next_after` only when the extra row
proves that another non-empty page exists. Preserve stable ascending order and
the existing exclusive cursor semantics.

The regression battery must cover fewer than limit, exactly limit, limit plus
one, multi-page traversal with no duplicate or omission, and retrying the same
cursor against an unchanged snapshot.

## Revalidation — 2026-08-17 against projection 6.2

The defect remains present in `src/baton_work/projection.py::thread`. The
`newest`/`before` branch reads `limit + 1`, records whether a proof row exists,
and trims the payload. The forward branch still reads exactly `limit`, and the
return expression sets `next_after` solely because `len(messages) == limit`.
An exact-limit terminal page therefore advertises a cursor whose canonical
follow-up is empty.

The implementation boundary is confined to the forward Message query and its
continuation calculation: fetch at most `limit + 1`, keep the first `limit` in
ascending order, and expose the last returned sequence only when the extra row
exists. Do not change `after` exclusivity, reverse pagination, references,
personal-new computation, `last_seq`, or snapshot handling.

Add the focused regression in a dedicated W130 test module rather than folding
it into W76. Extend the existing workflow pagination proof in
`tests/work/workflows/test_ws4_wf01.py` with an exact-multiple case so source
and packaged JSON both prove that every advertised cursor opens a non-empty
page and that traversal is complete, ordered, duplicate-free, and retry-stable.
