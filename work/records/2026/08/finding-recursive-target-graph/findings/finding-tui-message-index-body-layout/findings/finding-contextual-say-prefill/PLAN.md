# Plan

**Status — 2026-08-17:** complete; independent review pass 3 verified the
shared-tokenizer correction and signed off W81.

1. Revalidate the command editor and current selected-Thread/local-selector
   model after W76.
2. Seed `thread=<selected>` exactly once on contextual `say`, keeping the
   buffer editable and the caret ready for the next operand.
3. [done] Preserve explicit paste, quoting, assist, batch mode,
   cancellation, and read-only navigation semantics. Recognize `thread=` only
   as an actual operand outside quoted values; literal body text must not
   displace the seed. Match the command bar's actual `shlex.split` tokenization,
   including escaped whitespace and escaped token characters.
4. [done] Add pure and PTY tests for contextual/non-contextual entry, multiple
   Threads, selection changes, refresh/resize, duplicate prevention, posting,
   and packaged parity. Events is not Thread context: entering `say` there does
   not seed, while switching tabs after a seed leaves its snapshot untouched.
5. [done] Run focused tests and return for independent review. The complete
   gate remains isolated behind the concurrent W159 default-change batch.
