# baton-tui 1.1.0 is available

`baton-tui` 1.1.0 is the human console. It speaks protocol 10, unchanged from
1.0.0, and opens an existing authority as it stands.

`baton-tui --version` now reports `baton-tui 1.1.0 (protocol 10)`. The number
belongs to this console alone — see "Versions have owners" below.

## `N` asks who a notice is for

Composing a broadcast begins with its audience: `*` for everyone, or any team
scope the authority is configured with. Typing filters the list, Tab completes,
Enter accepts what you typed.

The audience is carried explicitly from that prompt through composition, the
send confirmation, draft retention and reopening, and publication. Both defects
found in review were the same shape — a missing value whose default was
"everyone" — which is why there is no path left where the audience is absent
and something has to decide what absence meant.

## Leaving the editor asks before sending

Ctrl-E takes a reply or a composition into your editor. Exiting the editor now
enters the send confirmation rather than returning to the composer: a message
written in vim is one deliberate keystroke from being sent, and zero from being
sent by accident. Exiting the editor still cannot publish anything by itself.

## `/` filters the list

Author, other party and subject, over the rows already on screen, matched as a
literal case-folded substring. It reads no body, takes no claim and records no
notice receipt — claiming is the only thing that may read content, and that is
unchanged. An accepted filter stays in force so you can act on a result; `/`
then Esc clears it.

## Saving what you can already read

`m` reaches every part you can view in full — answered messages, messages you
sent, notices you have seen — instead of demanding a live claim. The preview
boundary is unchanged: a pending unclaimed message and an unseen notice still
refuse, because writing bytes to disk is reading them in the most durable form
there is.

`M` is its larger twin. It saves the WHOLE message — envelope and every part,
in order — to a path you type in a one-line box, seeded from your projection
directory when one is configured. The row it acts on is captured when you press
the key, so polling cannot redirect the save while you are still typing.

## Drafts

The draft file advances to format 3 and reads formats 1 through 3. A notice
draft retains its audience; a full-body draft retains whether a body was
requested. The version bump is the point rather than bookkeeping: an older
console accepting a newer file would silently drop the protection the new field
carries, and for a scoped notice that means publishing it to everyone.

## Versions have owners

`baton-tui`, `baton` and the `baton_core` package they both embed are
independently versioned products. This console can move without the tool
moving, which is the whole reason the numbers were separated.

The protocol version in parentheses is the separate on-disk contract, and it is
still 10. The console also declares the core API it was built against, and
refuses at startup rather than mid-render if it is ever run against a core that
is not the one it was tested with.

Superseding 1.0.0: both executables used to report one shared release version.
That rule prevented drift by making difference impossible; the current model
permits deliberate difference and prevents accidental drift by giving every
version exactly one owner.

## Not in this release

Bulk selection and archiving were implemented, reviewed and withdrawn.
Participant-scoped archive metadata belongs in Baton's SQLite metastore rather
than in a file beside the console's drafts, so the feature and its
compatibility design are deferred to protocol 11.

## Upgrading

Nothing to do. Existing drafts are read and upgraded in place the first time
this console writes them; authorities, configs and in-flight claims are
untouched.
