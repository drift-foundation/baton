# Three handoff texts the canonical passes did not carry

Review 2026-10-18T19-33-42Z caught an operational fault of mine: canonical
event E325725 contains the literal string `@/tmp/w321690-handoff.txt` rather
than that file's contents. `comment=@<path>` is **not** a supported
indirection in the v11 CLI — it stores the operand verbatim — and a handoff
that lives in `/tmp` is not a durable canonical handoff.

I checked my other passes. Three were affected, all of them mine:

| Canonical event | Work | File here |
| --- | --- | --- |
| E325252 (return) | W325034 | `W325034-E325252.txt` |
| E325378 (return) | W325035 | `W325035-E325378.txt` |
| E325725 (return) | W321690 | `W321690-E325725.txt` |

Earlier passes (E325090, E325131, E325190) carried their text inline and are
unaffected.

These copies are the texts those three passes were meant to carry, preserved
here because the canonical events cannot be rewritten and both child Works are
closed. They are a provenance record, not a substitute for the canonical
handoff: the reviewer independently read the `/tmp` files at the time and
preserved the W321690 one in its own review evidence, so no decision rested on
bytes nobody saw.

**Method correction, in force from claim 325757:** every pass comment carries
its actual concise handoff text inline, with canonical `baton:work/records/...`
locators for anything longer. No `@file` operand.
