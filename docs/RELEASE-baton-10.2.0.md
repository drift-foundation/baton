# baton 10.2.0 is available

`baton` 10.2.0 speaks protocol 10, unchanged from 1.1.0. An existing authority
is opened as it stands, with no rebuild and no schema migration, and 1.1.0 and
10.2.0 participants share a mailbox without either noticing.

THE MAJOR IS THE GENERATION. 10.2.0 is not a rewrite of 1.2.0: it is the same
release under the rule that an application's major IS the protocol it serves.
The number moved because the rule was applied, not because the software
changed, and the minor and patch are kept so the lineage stays readable.

`baton --version` reports `baton 10.2.0 (protocol 10)`.

## It asks the mailbox whether it belongs there

A deployed mailbox can now carry `MAILBOX.json` beside its config, stating the
protocol generation it is. Before any command touches the authority, this
release reads that document and refuses if it cannot speak that generation —
before the command, not inside it, because a refusal that arrives after a write
is not a refusal.

A mailbox WITHOUT the document is accepted exactly as before. Every authority
in existence predates the handshake, and refusing them all would be refusing
every mailbox there is. What absence cannot do is claim compatibility.

A document that is malformed is refused rather than treated as absence: a
corrupted compatibility claim must not become an accepted one. It is read with
Baton's strict JSON loader, so a duplicate key cannot resolve to whichever
value came last, and unknown fields are refused rather than ignored.

## What the handshake asks is the protocol, and only the protocol

`baton` 1.x speaks protocol 10, so its major is not its generation. The mailbox
identity therefore states the generation it is — a namespace of `legacy`, or
`v<major>` matching the protocol — and the only question asked at startup is
whether this executable speaks that protocol. It does not name applications or
versions, because a mailbox is not a list of the programs allowed to open it:
two releases that speak protocol 10 are interchangeable to it, and one that
does not is refused whatever its name.

## Versions have owners, and the core has one too

`baton`, `baton-tui` and the `baton_core` package they embed are independently
versioned. This release moves both applications to 10.2.0 and the core to 1.2.0, and
it moves the core's API contract from 3 to 4: the core gained public surface
these applications call, and the API check is EQUALITY, so a 10.2.0 application
cannot be paired with a core that lacks it. The API version is an embedding
contract between an application and the core inside it — never a wire contract.
The protocol in parentheses is the wire contract, and it is still 10.

## Deployment

Installed releases are immutable and live at exact paths under a generation:

    app/baton-cli/v10/v10.2.0/bin/baton
    app/baton-cli/v10/latest -> v10.2.0

`latest` is for discovery. Resolve it once and run the exact path it names: a
Python zipapp reopens its archive by path on every lazy import, so a process
that kept an alias open could read the archive that replaced it.

## Upgrading

Nothing to do. Point at the new executable when your deployment offers it;
authorities, configs and in-flight claims are untouched.
