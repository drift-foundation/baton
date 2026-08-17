# Finding: Work message counters must describe the visible Work scope

## Parent

`finding-v11-messaging-cutover-gate` — observed while reading W24 in the live
v11 TUI.

## Observed

W24's detail header reported `new 21`, but entering W24 exposed only its two
directly labelled messages. The remaining personal-new messages belonged to
contained Works, including five on closed W136 that the default table hid:

```text
W24 own    2
W136       5
W148      10
W163       1
W171       2
W176       1
total     21
```

The default `Msg`, `My`, and `New` projections recursively aggregate a Work's
descendants. The TUI therefore displays numbers that cannot be reconciled with
the Threads reached by entering the row, while child rows separately repeat
their contribution. Hidden closed descendants can inflate a visible parent's
attention count indefinitely.

## Decision — 2026-08-16

Default Work counters describe the Work's directly labelled Threads—the same
scope reached by entering that Work:

- `Msg` is the number of distinct Messages in Threads labelled directly to
  the Work.
- `My` is the viewer's unresolved directed obligations in those directly
  labelled Threads.
- `New` is the viewer's distinct unseen Messages in those directly labelled
  Threads.
- Each contained child reports its own direct counters. Closed, collapsed or
  otherwise hidden descendants never inflate a visible parent's default row
  or detail header.
- A Thread deliberately labelled to several Works contributes to each direct
  Work view; that is visible reuse, not an error to hide through containment
  aggregation.

Recursive information remains available only through an explicitly labelled
breakdown/read such as `own`, `children`, `overlap`, and `subtree_total`.
Clients must not project that total into a plain `New`, `Msg`, or `My` cell.
Agent JSON and human TUI surfaces use the same direct default semantics.

For the observed authority, W24's default `New` is therefore 2, not 21.

## Projection compatibility ruling — 2026-08-16

The v11 product is in heavy pre-release evolution. Preserving compatibility
with earlier trial projection clients is not an acceptance constraint for this
change: no alias, adapter, migration, or dual-shape response is required.

The break must still be explicit rather than plausibly misreported as a
compatible minor. W179 advances the JSON projection major to `5.0`; clients
expecting `4.x` fail clearly and update to the new direct-count contract.

## Thread-less trial-assignment ruling — 2026-08-16

`My` has two direct-scope branches:

- A discussion `@` obligation follows its directly labelled Thread. If that
  Thread is deliberately labelled to several Works, the obligation is visible
  in each of those direct Work views.
- A trial assignment has no Thread. It contributes `My=1` only on the Work
  owning that trial, until it is reported or withdrawn.

Neither branch inflates a parent merely because the owning Work is contained
under it. This preserves direct visible scope without making a real
thread-less assignment disappear from every `My` counter.

## Acceptance

- Home rows and Work detail return/render identical direct `Msg`, `My`, and
  `New` facts.
- Entering a Work exposes the Threads from which those direct counts were
  calculated.
- Open, closed, collapsed and multiply nested children do not change a
  parent's direct counters.
- An explicit recursive breakdown remains mathematically honest, including
  overlap from multiply-labelled Threads, and names its subtree scope.
- Marking a direct Thread seen changes only the relevant direct Work counters
  plus any explicitly requested subtree breakdown; it does not rely on table
  expansion state.
- Workflow coverage pins the W24-shaped case: visible parent messages,
  several open children, one hidden closed child, and no unexplained aggregate
  in the parent row/header.
