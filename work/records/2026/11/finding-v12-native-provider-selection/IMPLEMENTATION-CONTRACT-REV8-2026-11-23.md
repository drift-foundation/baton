# W385830 — proposed implementation contract, revision 8 (delta)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385872 and the FINDING entry "Claude CLI pin
retained — owner 2026-11-23".

**PROPOSED — NOT APPROVED.** Research and design only. Nothing built,
launched or tested; no provider call; no credential or registry read; no
runtime edit.

Base text: `IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md` as amended by
`-REV2-` to `-REV7-`; all seven preserved unchanged. This file folds in the
Claude pin and its qualification condition, takes the re-seed act and its
test out of the contract as not approved, states the login-sharing limit,
and raises the next decision.

## 1. Settled

| Settled by the owner | Source |
| --- | --- |
| **Claude CLI 2.1.247 is retained** for this Work. Codex stays on 0.169.0 | M385872 |
| That exact build is qualified against the selected requirements, including explicit Fable selection and evidenced contributor reporting | M385872 |
| An upgrade happens only if qualification establishes that 2.1.247 cannot meet those requirements | M385872 |
| Any alternative build needs its own explicit selection and its own qualification. No silent substitution | M385872 |
| Whether a credential refresh invalidates other copies of a login is an unresolved qualification question, to be answered before a login is shared across worker homes | M385872 |
| The explicit re-seed operation is **not approved**. It stays pending until an actual recovery requirement is established | M385872 |

Both halves of D1 are now settled.

## 2. The Claude pin (amends first contract §4.6, §6.2, §6.3)

| Where | What the pin fixes |
| --- | --- |
| Image recipe | `Dockerfile.claude` keeps 2.1.247. The image is rebuilt only because the worker adapter changes; its CLI does not |
| Worker profile | "CLI build, selected" for a Claude worker is 2.1.247; the worker measures the installed build, and any other is `conflicting` (REV3) |
| Participation sources | Drafted from the retained September output of this same build (per-model usage entries; no direct model field) and confirmed at qualification (REV5 §3.1) |
| Instruction loading | Unchanged build, so whatever it loads today it still loads. What that is has not been observed in the image and is inventory item U2/U9 |

## 3. What "meets the requirements" means for 2.1.247

The ruling makes an upgrade conditional on a demonstrated failure, so the
contract has to say what counts as one. Each row is a fact about this
exact build in its image; none is established yet.

| # | Requirement | Established by | Fails when |
| --- | --- | --- | --- |
| C1 | The installed program reports 2.1.247 without network or credential | Engine-only image gate | It reports anything else, or cannot be measured |
| C2 | It accepts an explicit model selector on a fresh turn with the adapter's exact arguments | Help inventory at the gate; real-provider question Q2 | The option is absent, or the turn is rejected for the selector |
| C3 | Asked for the selected Fable selector, it runs the turn rather than refusing or substituting | Q2 | The provider rejects the selector, or the turn completes with no evidence of that model |
| C4 | Its output carries at least one participation source, readable within the adapter's bounds | Q2 | No field evidences which models did work |
| C5 | The contributors include an identity the owner accepts as the requested Fable model | Q2 output, then the owner's selection of the mapped identity (D2) | The reported contributors contain no such identity |

- **All five hold** → 2.1.247 is qualified for the Claude reviewer; no
  upgrade question arises.
- **Any fails** → that is the demonstrated need. The evidence is the
  retained Q2 or gate output. Nothing changes by itself: the pin stays,
  the Claude reviewer stays unqualified, and the owner is asked to select
  an alternative build, which is then pinned and qualified from the start
  (C1–C5 again, plus a fresh inventory of its result shape, home files
  and instruction loading).
- **Mechanically enforced:** the image's version gate accepts exactly the
  pinned build; the worker refuses to attribute a turn run on any other.
  There is no code path that tries a second build.

One call cannot show that C3–C5 hold on every later turn. That is what the
per-attempt attribution record is for: a later turn that does not evidence
the requested model is refused and held, whatever qualification showed.

## 4. Taken out: the re-seed act (amends REV7 §2.2 item 6 and §6 item 27)

- REV7 §2.2 item 6's second half — "one explicit operator act replaces the
  home's credential from the registry" — is withdrawn from the contract.
  It was my proposal and is not approved.
- REV7 verification item 27 is withdrawn with it.
- What remains specified when a retained login stops working: the provider
  fails to authenticate; the attempt ends as a typed provider failure; the
  home and its credential are left exactly as they are; nothing re-seeds.
- **Stated gap:** the contract then has no supported way to make that home
  usable again. That is deliberate and pending. It is raised when a
  qualification result or a real lapse shows what recovery is actually
  needed.

## 5. One login, one home — until qualified (amends REV7 §2 and §5 U5)

Until U5 is answered, the contract does not let a login be shared across
worker homes:

- Within an instance, composition refuses a second worker in
  seeded-and-retained mode that names the same credential reference as
  another.
- Across instances, and between a worker and the operator's own session,
  Baton cannot see sharing. That part rests on which login the owner
  selects as the seed (U8), and is stated as a limit, not enforced.
- The pipeline this Work delivers has one Codex worker, so the rule costs
  nothing today.

Verification added (deterministic):

28. Two seeded-mode workers in one instance naming the same credential
    reference are refused at composition; two naming different references
    are admitted.
29. The Claude image's version gate refuses a build other than 2.1.247,
    and the Codex image's a build other than 0.169.0.
30. A Claude worker whose measured build is not 2.1.247 yields
    `conflicting`; no retry on another build occurs.

## 6. Where the contract stands

Settled: D1 (both pins), D3, D4, D5, D6, explicit models, contributor
attribution, home safeguards.

| Slice | State |
| --- | --- |
| N1 — explicit model and attribution | Specified. Deterministic; fixture identifiers |
| N2 — provider hooks, neutral tool policy, per-worker adapter identity, retained home, one-writer check | Specified. Deterministic |
| N3 — Codex adapter and image recipe | Specified as far as behaviour; its flags, event shapes and file locations are filled from the in-image inventory |
| N4 — engine-only image gates | Needs images, then selection (D7) |
| N5 — real-provider questions Q1, Q2 | Needs selection (D7), the seed login (U8) and the requested selectors (D2) |
| N6 — packets and joined proof | After N1–N5 |

Everything still open concerns qualification: U8, D2 values, D7, U5, the
recovery gap in §4. None of it changes what N1, N2 and the deterministic
part of N3 must do.

## 7. The next decision for the owner

**Should I now consolidate the eight contract files into one
self-contained contract for your approval of the deterministic work, and
leave the qualification decisions until images exist?**

The contract is a first file plus seven deltas, three of which withdraw
something an earlier one proposed. Nobody should implement from that. And
the remaining decisions all sit behind work that has not started.

- **A — Consolidate now; qualification decisions later (recommended).**
  One self-contained document covering N1, N2 and N3's deterministic part,
  with settled, proposed and open kept apart, as was done for the A1
  contract. You approve or correct that. U8, the model selectors and the
  gate and provider-call selections are raised in order when the images
  exist and the answers can be acted on. Cost: you approve implementation
  before knowing whether either pinned build passes its gate; a failed
  gate would then change N3, and possibly the Claude pin, after code
  exists.
- **B — Settle the qualification decisions first, then consolidate.** The
  next single question would be the requested model selectors (D2), then
  the seed login (U8), then the selections (D7). Cost: three or more
  rounds on matters that cannot be acted on until images are built, while
  specified deterministic work waits.
- **C — Consolidate only N1 and N2.** The provider-independent core is
  approved and built first; N3 is consolidated after an early engine-only
  look at Codex 0.169.0. Cost: two contracts and two approvals, but the
  Codex unknowns (U1, U2) are faced before its adapter is written.

I recommend A. I have not assumed it. Consolidation is a document; it
approves nothing by itself and assigns no one. The order relative to
W385853's delivery change stays as proposed on T385853 and is not decided
by this.

## 8. Still open after that

| # | Item | Needed for |
| --- | --- | --- |
| D2 (requested) | The exact selector each worker requests: Fable reviewer, Codex implementer | Q1, Q2 |
| U8 | Which registry login seeds the Codex worker, and that it is not in use elsewhere while U5 is open | Q1 |
| D7 | Selection of the engine-only gates and of Q1 and Q2 | N4, N5 |
| D2 (mapped) | The identity each selector is accepted as reporting | Native use |
| U5 | Whether a refresh invalidates other copies of a login | Sharing a login |
| Recovery gap | What restores a home whose login has lapsed | When established |
| Order with W385853 | Coordination in progress | Assignment |

## 9. Limits

- Nothing executed.
- §3's five requirements are my reading of "selected requirements,
  including explicit Fable selection and evidenced contributor reporting".
  C1 and C2 are added as preconditions of those two; if the owner intends
  a different set, §3 is where to correct it.
- The same-reference refusal in §5 is my mechanisation of "before sharing
  a login across worker homes". It covers one instance only.
- C5 depends on the owner's judgement of what the build reports; the
  contract cannot decide it.
