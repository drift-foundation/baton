# Finding: the v11 Message panes waste scarce reading space

## Observed

The projection-9 TUI labels the Message index with the number of rows on the
currently loaded page, not the selected Topic's real total, and gives the
reader a standalone `Message M…` heading immediately above metadata that
already identifies that same Message. The first treatment is misleading on a
paged Topic; the second spends a terminal row without adding information.

## Confirmed decisions — 2026-08-18

**Confirmed by Slawomir during the live v11 trial.** Two separate changes make
the lower reading area honest and denser:

1. The index heading is `Messages (total/unseen)`, where `total` is every
   Message in the selected Topic and `unseen` is personal to the current
   participant. Neither number is the current page length.
2. The standalone selected-reader heading (`Message M…`) is removed. The
   canonical Message metadata begins the reader immediately and carries the
   reader-pane focus cue without consuming another row.

The independently reviewable children are:

- `findings/finding-message-total-unseen-heading/`
- `findings/finding-remove-message-reader-heading/`

The existing newest-first index, selected-row highlight, explicit older-page
cue, separate references, and spatial pane navigation remain unchanged.

## Presentation follow-up — 2026-08-18

**Confirmed by Slawomir during the same live trial.** The Message index itself
also becomes a fixed-column table. That independently tracked refinement lives
under `../finding-v11-detail-pane-formatting/`; it does not change the
total/unseen or reader-heading decisions owned here.
