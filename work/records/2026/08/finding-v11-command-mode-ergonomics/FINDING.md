# Finding: v11 command mode is costly for repeated operations

## Observed

The `:` bar exposes the whole strict v11 operation grammar and already shows
context-sensitive assistance, but it still treats every command as new input.
Operators commonly repeat a recent operation with one Work id, outcome, or
rationale changed. Retyping long canonical operands such as `outcome=` and
`satisfying` is slow and creates avoidable refusals.

## Confirmed decision — 2026-08-18

**Confirmed by Slawomir during the projection-9 v11 trial.** Command mode grows
as an ergonomic layer over the one canonical grammar:

1. Up and Down navigate submitted command history, and command mode provides
   incremental reverse search through that history.
2. Tab completes command names, operand names, and values drawn from a closed
   grammar vocabulary. For example, `ou<Tab>` becomes `outcome=` in the
   applicable command, and `outcome=sat<Tab>` becomes
   `outcome=satisfying`.
3. Completion never creates a second protocol dialect. The executed command,
   JSON surface, audit evidence, help, and errors retain the full canonical
   spellings. An ambiguous prefix is never guessed.
4. Typing, history navigation, searching, and completion are client-local and
   read-only. They do not query or mutate the authority, mark messages seen, or
   schedule a projection refresh.

The first slice covers static information already present in the declarative
command grammar. Work ids, Thread ids, participants, routes, paths, and other
dynamic authority/filesystem values are deliberately separate future work.

The two independently reviewable children are:

- `findings/finding-searchable-command-history/`
- `findings/finding-command-completion/`

The completed command-assistance contract remains the one owner of the visible
hint line. This record extends it; it does not replace its quote-aware parser or
permit duplicated completion metadata.
