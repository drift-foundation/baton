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
