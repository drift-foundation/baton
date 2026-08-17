# Finding: discussion Threads should be Topics

## Discovery context — 2026-08-17

The v11 Work detail view groups messages under named discussion Threads. In
this system `thread` is overloaded with Codex/app-server conversation sessions
and can also imply a reply tree, while Baton's object is simply one named,
linear discussion inside a Work.

## Confirmed decision — 2026-08-17

**Confirmed by Slawomir.** The vocabulary is:

```text
Work
  Topics
    Messages
```

- The durable discussion grouping is a **Topic**. A Topic has one shared
  subject/title and contains ordered Messages; it is not a Work, route,
  claimant, dependency, or reply tree.
- TUI and human documentation say `Topic`/`Topics`.
- The authority, CLI and canonical JSON change coherently: `start-thread`
  becomes `start-topic`; `thread`/`thread_id` become `topic`/`topic_id`; and
  `threads` collections become `topics`.
- Compact identities remain `T1`, `T2`, and so on. `T` naturally identifies a
  Topic, so changing durable/local identifiers adds no value.
- This is intentional v11 pre-release evolution: no compatibility alias and
  no migration. The replacement lands through a fresh authority and an honest
  schema/projection boundary.
- Do not rename unrelated runtime/session threads, source-control discussion
  threads, historical evidence that explicitly names the retired surface, or
  generic threading terminology.

## Scheduling decision

Do not implement this while v10 remains the operational fallback. The Work is
blocked by W24, “Make v11 messaging sufficient to retire v10”. Closing W24 is
the explicit gate that v11 messaging is usable and v10 can become obsolete;
only then does this vocabulary change enter implementation.

## Acceptance boundary

- CLI, JSON, TUI, authority events/schema, readiness integrations,
  documentation, and workflow stories consistently expose Topic vocabulary.
- The obsolete `start-thread` command and `thread=` operands refuse rather
  than acting as aliases.
- Topic creation, ordering, subject/title rules, paging, seen cursors,
  obligations, messages, Work detail navigation, and replay/race guarantees
  retain their behavior.
- Compact `Tn` selectors remain stable and unambiguous.
- A fresh-authority end-to-end workflow creates multiple Topics, exchanges
  Messages, navigates them in the TUI/JSON surfaces, and proves the obsolete
  vocabulary is absent.
