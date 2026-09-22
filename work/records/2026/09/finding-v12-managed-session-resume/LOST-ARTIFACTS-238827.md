# Superseded operator packets: an unrecoverable loss, and the practice change

Claim 238827, baton.claude. Recorded in answer to the operational finding in
`review-2026-09-22T12-55-41Z.md`: `OPERATOR-238462.md`,
`PACKET-INPUTS-238462.json` and `SELECTIONS-238462.json` could not be read at
their previously reviewed paths.

## What happened, plainly

I deleted them. Each of my claims from 236529 onward superseded the operator
packet by writing the new revision and then `unlink()`-ing the old one, so a
revision's evidence locator stopped resolving the moment the next revision
landed. The reviewer could not compare the historical bytes against the current
ones, which is exactly what an append-only record exists to permit. No other
actor is implicated and nothing was lost to a fault.

**The bytes are not recoverable.** Every one of these files was generated from
the dossier's own state at the time, and that state has since moved -- the
digests they embed are digests of files this Work has changed. Regenerating them
would produce different bytes under an old name, which would be worse than the
gap: an invented artifact presented as a retained one. I have not done that and
will not.

## Everything superseded, and the authoritative digest where one survives

The digests below are the INDEPENDENT reviewer's, read out of their retained
`review-evidence-*.json`, not restated from my own handoffs.

| File | sha256 | Retained in | Present |
|---|---|---|---|
| `OPERATOR-236529.md` | `2fe3bbc4e38bc882a5a70577faab4a24e65c7fd1813629e6a88ea6099c6b2897` | `review-evidence-236644.json` | no |
| `PACKET-INPUTS-236529.json` | `ba5f0440611f66621cbb0008b5aead073ac21eba0ff6e57c8aa1d05fc6c886fb` | `review-evidence-236644.json` | no |
| `SELECTIONS-236529.json` | `ce4111cc61f8bc3fa23d71b769ca3337b1a4827c0abf328c6915f7b02eb824fd` | `review-evidence-236644.json` | no |
| `MANAGER-SOURCE-236529.json` | `2b86274e049df520ad4e75c2ce1aa8f7b4a91826c34887f79df291453a939c8d` | `review-evidence-236644.json` | no |
| `OPERATOR-238310.md` | `43622b7171447240c5c52aa94579e27bbf8bcd9b6b8ea0c776dd72308dac6942` | `review-evidence-238394.json` | no |
| `PACKET-INPUTS-238310.json` | `cb023df428c67fbf6a2b6fc1ef0f923ae1cabbcddc4be5e82987698a0191b32e` | `review-evidence-238394.json` | no |
| `SELECTIONS-238310.json` | `d4da4a0243c52c378697884cfc8621f372a54d17cc8ebc67a6bab32f40121fc2` | `review-evidence-238394.json` | no |
| `OPERATOR-238462.md` | `605a569389e974370873c22e063f2006698f4710f5e82f43b9f2189836e320c2` | `review-evidence-238615.json` | no |
| `PACKET-INPUTS-238462.json` | `630e147ea0eae8e922b0cf43b6c17d77994cd8f6ae69b8617e1006c8d2bf9d44` | `review-evidence-238615.json` | no |
| `SELECTIONS-238462.json` | `02d637330452a31c56b15a6e842fc051b3a0f1880c362cc31739f20da1c0bda8` | `review-evidence-238615.json` | no |
| `MANAGER-SOURCE-238462.json` | `2c7caa909d3e01e918c7badd27f2152ee1430cebd5c530fe0333b2b81458cefa` | `review-evidence-238615.json` | **yes** |

`OPERATOR-236349.md` and `PACKET-INPUTS-236349.json` preceded the first packet
review and no independent record retains their digests; I am not asserting one
from memory. They are equally gone.

## What this does and does not cost

Every superseded revision's CONTENT is described in the PROGRESS entry of the
claim that wrote it, and each successor states what it changed and why. What is
unavailable is byte-level comparison against the retained digests above. No
accepted product byte, candidate provenance, verification receipt or reviewer
artifact was affected: `CANDIDATE.json`, `BASELINE.json`, `candidate.diff`, all
`verification-*` receipts and every reviewer-owned file are intact and
independently readable.

## The practice, changed

Superseded operator packets are now kept. From this claim on, a new revision is
added beside its predecessor and the predecessor is marked superseded in its own
header; nothing in this dossier is unlinked. `OPERATOR-238700.md`,
`PACKET-INPUTS-238700.json` and `SELECTIONS-238700.json` remain in place beside
this claim's revisions for that reason, and their digests stay resolvable.
