# baton-tui 10.2.0 is available

`baton-tui` 10.2.0 is the human console. It speaks protocol 10, unchanged from
1.1.0, and opens an existing authority as it stands.

`baton-tui --version` reports `baton-tui 10.2.0 (protocol 10)`.

## It checks the mailbox before curses takes the screen

If the mailbox carries a `MAILBOX.json` identity, the console reads it and
refuses a mailbox whose protocol it does not speak BEFORE the terminal is taken
over. That is the whole question: the identity states a generation, not a list
of applications or versions permitted to open it. A console
that discovered it was the wrong generation mid-render would have to say so
through a drawing surface it had already claimed, which is how a clear refusal
becomes a corrupted screen.

A mailbox without the document is accepted exactly as before.

## Nothing else about the console changed

No key, no pane, no draft behaviour. `N`, `/`, `m`, `M`, the send confirmation
and the editor round trip are as they were in 1.1.0. This release exists
because the core moved and the console's startup path moved with it.

## Versions have owners

`baton-tui`, `baton` and the `baton_core` package they embed are independently
versioned. Both applications move to 10.2.0 and the core to 1.2.0: the
application major is dictated by the protocol they speak, while the core keeps
its own line. The core API
moves 3 to 4, and the console's startup check is EQUALITY: it refuses a core
that is not the one it was built for, by name, rather than failing on the first
message that needs the missing surface.

## Upgrading

Nothing to do. Existing drafts are read and upgraded in place; authorities,
configs and in-flight claims are untouched.
