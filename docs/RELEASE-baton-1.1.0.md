# baton 1.1.0 is available

`baton` 1.1.0 is the agent command line. It speaks protocol 10, unchanged from
1.0.0: an existing authority is opened as it stands, with no rebuild and no
schema migration, and 1.0.0 participants and 1.1.0 participants share a mailbox
without either noticing.

`baton --version` now reports `baton 1.1.0 (protocol 10)`. The number belongs
to this executable alone — see "Versions have owners" below.

## Save a whole message

    baton --config CONFIG save ID --participant WHO --output /abs/path.json

`materialize` hands one leaf's bytes to a tool. `save` hands a person the whole
thing: the envelope and every part, in order, as one deterministic JSON
document with `"format": "baton.whole-message"` and `"version": 1`, carrying
exactly one of `message` or `notice`.

The document holds the IMMUTABLE envelope only — no claim, no seen receipt, no
lifecycle state, no saving participant, no save timestamp. That is what makes
it deterministic, and determinism is what lets a second save of the same
message be accepted as a resume rather than reported as a conflict.

`--output` names the file exactly: a canonical absolute path whose parent
already exists. It creates no parents, appends no suffix, resolves no relative
path, and never replaces bytes that differ. External parts stay references —
their pins are revalidated before serialization and a damaged one fails closed
— and transient messages are refused, because a durable copy would defeat the
retention their sender chose.

## Read back what you are entitled to read

`materialize` gained the authorized path: a message or notice you may read
without holding a claim — one you sent, one addressed to you and answered, a
notice you have seen. Authorization is unchanged and is still the core's;
a refusal remains indistinguishable from "no such thing", so it cannot tell a
non-party which kind an id is.

## Versions have owners

`baton`, `baton-tui` and the `baton_core` package they both embed are
independently versioned products. They may carry different numbers at the same
time, and a console release no longer obliges the tool to move.

The protocol version in parentheses is the separate on-disk contract. It is
what decides whether two participants can work together, and it is still 10.

Superseding 1.0.0: both executables used to report one shared release version,
so a human could never be told two numbers for one release. That rule prevented
drift by making difference impossible. The current model permits deliberate
difference and prevents accidental drift by giving every version exactly one
owner — a catalog inside the core package, from which the executables, both
distribution manifests and the documentation all derive.

## Documentation

The `regen` ceremony is described accurately: a config file is a PROPOSAL until
`regen` accepts it transactionally, ordinary operations refuse while its
generation or digest differs from the accepted state, and a refusal leaves the
authority unchanged. The safe retry and restore paths are written down, and
editing the SQLite authority directly remains forbidden.

## Upgrading

Nothing to do. Point at the new executable when your deployment offers it;
authorities, configs and in-flight claims are untouched.
