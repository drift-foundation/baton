# Finding: prefill `say` from the selected Thread

## Observation — 2026-08-17

In Work details the TUI already has one canonical selected Thread, but entering
`:say` still requires the user to copy and type that Thread selector. This is
repetitive, error-prone input for the normal “reply where I am reading” path.

## Confirmed decision

Typing exact `:say` with a selected Thread seeds the editable command as:

```text
say thread=Tn 
```

where `Tn` is the visible authority-local selector for the selected Thread.
The user then enters `body=` and any optional operands. The TUI does not send
automatically.

Prefill occurs once, never duplicates or overwrites an explicit `thread=`, and
does nothing without one unambiguous selected Thread. The seeded selector is a
snapshot of user context; later focus or selection movement does not retarget
the command behind the user's back. Opening, editing, or cancelling the command
changes no seen or authority state.

## Acceptance boundary

- One and many-Thread detail views seed the currently selected visible local
  selector.
- Root/list views and empty Thread views do not invent a destination.
- Typed and pasted explicit `thread=` values remain untouched.
- Repeated spacing/editing does not duplicate the operand.
- Command assistance remains contextual after the seed and the caret lands
  where the next operand can be typed.
- Refresh, resize, cancellation, and focus movement preserve read purity.
- The eventual `say` posts only to the seeded canonical Thread.

## Revalidation — 2026-08-17 after W76

The decision remains current after the spatial/newest-first message-pane
change. `src/baton_work/tui/app.py` still opens every `:` command with an empty
buffer in `Console.handle`, while the selected row returned by `thread_rows()`
already carries the authority-local `local_id` rendered in the Threads pane.
No authority or schema change is required.

The implementation should keep command entry centralized: derive an optional
seed from the current detail-mode Thread selection only when the entered verb
has become exact `say`, then leave ordinary typing, explicit operands, `::`
batch entry, parsing, assistance, execution, and cancellation on their existing
paths. The seed must use the selected row's `local_id`, never its ordinal or a
canonical id reconstructed by the client.

Focused regression ownership belongs in a dedicated W81 test module, with
packaged PTY parity added to `tests/work/test_tui_packaged.py`. Tests must cover
one and many Threads, no selection/no Thread, selection snapshotting, explicit
typed and pasted `thread=`, duplicate prevention, caret/assist behavior,
refresh and resize purity, cancellation, and final delivery to only the seeded
Thread.
