# Progress

Owner: `baton.implementer` only.

## 2026-08-10 — implemented

State: **complete, pending review.** 2302 passed. `bin/baton-tui` rebuilt.

`request_quit()` never returns True on the first press: it always enters
confirmation with the one-line `Exit? y/N`. The key table already gave the
answer semantics the ruling wants -- only `y`/`Y` confirms, everything else
declines -- so that side needed nothing.

Two removals came with it:

- the footer's second row. It restated the outstanding-claim count that the
  header and the list already carry, and the prompt is now asked with nothing
  owed too, where that row would have said "0". `_footer_height` is one row
  in every mode again;
- the decline status "staying — finish or close the open claim". With nothing
  owed it instructed the reader to finish a claim they did not have. It says
  "staying".

Evidence 1-10 covered. The ones worth naming:

- every declining key is parametrised -- `n`, `N`, Enter, Esc, an unrelated
  letter -- because "anything but yes means stay" is the property, not "n
  means stay";
- the no-store-call proof drives the whole request/decline/request/confirm
  cycle against a store that RAISES on any attribute access;
- packaged PTY coverage for BOTH flows: nothing owed, which is the case that
  used to exit at once, and a claim owed, asserting the superseded two-row
  prompt is gone.

Four existing tests pinned the old contract and were rewritten, each saying so:
`q` from browse, the unresolved-claim confirmation, the immediate-exit case,
and the footer form.

One PTY fixture quit with a bare `q` and hung at the new prompt. It sends `qy`.
I saw that test fail during an earlier break check and read it as fallout from
the break rather than a real dependency -- it was both, and the full suite is
what surfaced it honestly.

## 2026-08-10 — four stale-contract residues corrected

State: **corrected, pending re-review.** 1614 focused tests pass.

All four were text I left describing the shape I had just replaced, which is
the failure mode the decision-pinning rule exists for -- except here the stale
statements were in code comments and a trial document rather than a finding.

1. `_footer_height`'s docstring still called the quit confirmation "the one
   shape that still needs two" rows. It says why it stopped needing them.
2. `test_q_quits_immediately_when_nothing_is_owed` proved the opposite of its
   name after I rewrote its body. Renamed to
   `test_q_asks_even_when_nothing_is_owed`, with a docstring recording the
   reversal and what it proves now.
3. `TRIAL.md`'s key map said `q` "asks for confirmation if a claim is
   unresolved". Corrected, `Esc` added, and the historical two-row footer
   statement explicitly marked superseded rather than edited -- the trial ran
   against that shape, and rewriting history to match the present would erase
   what the trial actually tested.
4. The render test helper kept an unreachable `QUIT WITH...` branch, and a
   state-test comment said "two-row footer" while the slice beside it took
   one. Both corrected; the comment had been wrong even before this change.

Nothing about behaviour moved. `bin/baton-tui` rebuilt anyway, because the
docstring lives in a packaged module.
