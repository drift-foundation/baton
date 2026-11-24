# W385830 — proposed implementation contract, revision 4 (delta)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385849 and the FINDING entry "Contributor-list
attribution — owner 2026-11-23".

**PROPOSED — NOT APPROVED.** Research and design only. Nothing built,
launched or tested; no provider call; no credential read.

Base text: `IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md` as amended by
`-REV2-` and `-REV3-`; all three preserved unchanged. This file replaces
two members of REV3 §2.1, all of REV3 §2.3 and §2.5, and items 4 and 14 of
REV3 §3. It withdraws REV3 §4, corrects first contract §6.3, and raises the
next decision. Everything else in REV3 stands.

## 1. Settled

| Settled by the owner | Source |
| --- | --- |
| Every model the provider reports for an invocation is retained as a **contributor**. None is designated primary | M385849 |
| The requested model is kept separately, as intent | M385849 |
| The requested model must appear in the evidenced contributor list, through the **explicitly selected** selector-to-reported-identity mapping. No invented equivalence | M385849 |
| Additional contributors are recorded. No helper allowlist and no primary-role requirement | M385849 |
| A match establishes **reported participation**, not predominance or exclusive authorship | M385849 |
| Missing evidence, or absence of the requested model, still refuses and holds. Evidence binding and no-silent-fallback are unchanged | M385849 |

Withdrawn: REV3 §4 and its recommendation of a declared helper list. The
words "helper", "primary" and "expected model" are no longer used for a
reported identity.

## 2. The attribution record (amends REV3 §2.1)

Two members of the REV3 record are replaced; the others stand.

| Member | Meaning | Source |
| --- | --- | --- |
| model, requested | The selector passed on the command line. Intent only | Composition → launch → argv |
| **model, mapped identity** (was "expected") | The identity the owner has selected as what the provider reports for that selector | Composition; a value the owner selects (D2), never derived |
| **contributors** (was "observed") | Every model identity the provider's output for this invocation names, as a set: each once, in a fixed sorted order so that position implies nothing | Extracted by the adapter from the evidenced output |
| outcome | `matched`, `missing`, `conflicting` | §3 |

Rules that follow from the ruling:

- **No ranking is recorded.** The record holds identities only: no usage
  quantities, no ordering by volume, no role per contributor. The provider's
  raw output stays in the retained log, named by digest, for anyone who
  needs to examine it.
- **The mapping is exact.** The mapped identity is compared with each
  contributor by exact equality of the whole string. No prefix, alias,
  family, case or date-suffix matching. A selector with no selected mapping
  cannot be composed under the new selection.
- **One mapped identity per selector.** I have not assumed a selector may
  map to several reported identities. If a provider turns out to report one
  selector under more than one name, that is a new owner selection.
- **Every evidenced source feeds the same set.** Where a provider's output
  names models in more than one place (a single direct field, per-model
  usage entries), all of them go into the contributor set and none
  outranks another. This drops REV3's rule that a single-model field naming
  a different model is `conflicting` — that rule treated one field as
  primary, which the ruling excludes.
- **Bounded.** The set has a finite maximum size; output that exceeds it is
  unreadable within bounds and therefore `missing`.

## 3. Matched, missing, conflicting (replaces REV3 §2.3)

| Outcome | When |
| --- | --- |
| **missing** | No contributor can be read: the provider output is absent, truncated, unparseable, over a bound, or names no model; or the CLI build could not be measured |
| **conflicting** | Contributors were read but the requested model's mapped identity is not among them; or the evidenced CLI build differs from the selected one |
| **matched** | The mapped identity is among the contributors, on the selected CLI build |

Additional contributors never change the outcome. They are recorded and
shown.

Only `matched` lets a candidate be accepted or a verdict recorded;
`missing` and `conflicting` are refused with a typed cause and held (REV3
§2.2 item 6, unchanged).

**What `matched` says.** "The requested model was reported among the
contributors of this invocation, on this build." It does not say that model
did most of the work, or all of it, or that the others did little.

## 4. Wording on every surface (amends REV3 §2.2 item 7 and §2.4)

| Shown | Never shown |
| --- | --- |
| "Requested: X" | "Model: X" as a statement of what ran |
| "Reported contributors: X, Y" | "Primary", "main", "helper", "auxiliary", or any share or percentage |
| "Requested model reported: yes / no / no evidence" | "Produced by X", "Reviewed by X" |

A result's attribution line reads, for example: "Requested X. Reported
contributors: X, Y. Requested model reported: yes." Old compositions still
read "not selected (account default)".

Separation class (replaces REV3 §2.5): computed from the composed workers'
provider and **requested** model — a statement about what was selected, not
about which contributors ran.

## 5. Verification for N1 (amends REV3 §3)

REV3 items 1–3, 5–13, 15 and 16 stand, reading "mapped identity" for
"expected" and "contributors" for "observed". Item 4 and item 14 are
replaced, and six are added.

4. Contributors are extracted from: a direct model field only; per-model
   usage entries only; both, agreeing; both, naming different models;
   neither. The first four yield the union as the contributor set;
   "neither" yields `missing`.
14. Published diagnostics show the requested selector, the mapped identity,
    the contributor list, both CLI builds and the outcome, in the §4 words.
17. Requested model plus one additional contributor → `matched`; both are
    recorded.
18. Requested model plus several additional contributors, none ever
    declared anywhere → `matched`. No allowlist is consulted, and none
    exists in the profile.
19. Contributors present but without the mapped identity → `conflicting`,
    refused and held — including when a contributor differs from it only by
    case, prefix or suffix.
20. The same contributors delivered in different orders, or with different
    usage figures, produce byte-identical records. The record carries no
    quantity and no role.
21. A worker composed with a selector that has no selected mapping is
    refused at composition.
22. No surface, record member or log line written by this change contains a
    primary, helper or share designation.

Qualification consequence (corrects first contract §6.3): the two
real-provider questions capture **the full contributor list** each pinned
build reports for the selected selector. Their purpose is to give the owner
the facts for selecting the mapping (D2 values); they do not establish or
approve any list of additional models.

## 6. What is now specifiable

| Slice | State |
| --- | --- |
| N1 (explicit model and attribution) | Fully specified by the first contract §4.3 as replaced by REV3 §2 and this file. Deterministic tests use fixture identifiers, so it does not wait for D2 values |
| N2 (provider hooks, neutral tool policy) | Fully specified by REV2 |
| N3 (Codex adapter and image) | Blocked on D1, D3, D6 |

## 7. The next decision for the owner

**Which Codex CLI build is pinned for the Codex worker image?**

This is the Codex half of D1 only. The Claude pin is a separate, later
question. It comes first because the adapter's flags, its event shapes, the
image, the home-directory behaviour and the model mapping are all facts
about one specific build, and nothing in N3 can be fixed until that build
is named.

What is known, and only this:

| Build | Known | Not known |
| --- | --- | --- |
| 0.150.1 | The only build ever run in a container here: the August spike, under the spike's posture, not the v12 posture | Whether it has every flag the adapter needs (first contract §4.5). I hold no help capture for it |
| 0.169.0 | Installed on this host. Its help output is retained in this dossier and shows every flag in §4.5 | Never run in a container here. Not proved under the v12 posture |
| Any other | — | Nothing. I have not looked up what builds exist |

- **A — 0.169.0 (recommended).** The only build whose flag inventory is
  retained, and it shows the explicit-model, no-ambient-configuration and
  machine-readable-output flags the design relies on. Cost: its container
  behaviour is unproved, so the engine-only image gate and the first
  real-provider question carry the whole proof.
- **B — 0.150.1.** The build with container experience. Cost: that
  experience is three months old and under a different posture, and its
  flags are unverified — the adapter could need capabilities it lacks,
  found only at the image gate.
- **C — Another build you name.** Cost: no evidence of either kind exists
  yet; the image gate would take the inventory from scratch.

I recommend A. I have not assumed it. Whichever is chosen is a pin for the
design and the image recipe only: it selects no download, build, image or
provider call, each of which is still D7.

## 8. Decisions still open after that

| # | Decision | Unblocks |
| --- | --- | --- |
| D1 (Claude) | Whether the Claude pin stays on 2.1.247 or moves | N4 |
| D2 (values) | The Fable selector and its mapped identity; the Codex model selector and its mapped identity | N5 |
| D3 | Codex credential kind and registry reference | N3, N5 |
| D6 | One private provider-home mount for workers that declare it | N3 |
| D7 | Selection of the engine-only image gates and the two real-provider calls | N4, N5 |

## 9. Limits

- Nothing executed.
- "Every evidenced source feeds the same set" (§2) is my reading of "no
  primary designation". It is the one place this revision removes a refusal
  REV3 had. If a disagreeing single-model field should still hold the
  result, that is a correction to make before N1 is assigned.
- Leaving usage quantities out of the record (§2) is likewise my reading of
  the same phrase; the quantities remain in the retained raw output.
- The two-identity behaviour of Claude 2.1.247 is taken from the September
  qualification dossier, not measured by me.
- The table in §7 is what this repository and this host show. It is not a
  survey of available Codex builds.
