# W385830 — proposed implementation contract, revision 3 (delta)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385847 and the FINDING entry "Explicit models and
attributable results — owner 2026-11-23".

**PROPOSED — NOT APPROVED.** Research and design only. Nothing built,
launched or tested; no provider call; no credential read.

Base text: `IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md` as amended by
`IMPLEMENTATION-CONTRACT-REV2-2026-11-23.md`; both preserved unchanged. This
file replaces the first contract's §4.3 (explicit model, end to end) and its
N1 verification list, and raises the next decision.

## 1. Settled

| # | Settled by the owner | Source |
| --- | --- | --- |
| D2a | **Every worker in the new composition names an explicit model, the Codex implementer included.** No account default for these compositions. Existing admissions are unchanged | M385847 |
| — | **Why: attribution.** When code, an implementation or a review has a problem, the model that produced it must be identifiable | M385847 |
| — | Retained for each result: the requested model; the provider-reported model and its evidence; provider and CLI version; the exact attempt; the resulting candidate or verdict | M385847 |
| — | The requested model is intent, not proof. The observed identity is never inferred from it | M385847 |
| — | Missing or conflicting model evidence prevents acceptance: refuse and hold. The owner may then explicitly select another model for subsequent execution | M385847 |

Still open: the identifiers and the CLI pins.

## 2. Model selection and attribution (replaces first contract §4.3)

### 2.1 The attribution record

One record per attempt that invoked a provider. It is what answers "which
model produced this?" later, so it is defined by what it must let a reader
establish, not by a parser.

| Member | Meaning | Source |
| --- | --- | --- |
| attempt | The exact attempt id, phase and Job | Launch document |
| provider | Which provider adapter ran | Adapter identity |
| CLI build, selected | The build the worker's profile names | Composition |
| **CLI build, evidenced** | The build the installed program reports | **Measured by the worker** from the program's own version output before the provider turn. Today the build is copied from the delivery and never measured (Surveyed) |
| model, requested | The selector passed on the command line | Composition → launch → argv |
| model, expected | The identity the provider is expected to report for that selector | Composition |
| **model, observed** | Every model identity the provider's terminal output names for this invocation | Extracted by the adapter; see §2.3 |
| evidence | Digest of the exact provider output the observation was read from, and the name of the retained log that holds it | Adapter; the existing provider log |
| outcome | `matched`, `missing`, `conflicting` | §2.3 |

It contains identities, versions and digests only. No provider content.

### 2.2 Where it travels and what it is bound to

1. **Selected** at composition: the model operand is required. Composition
   under the new selection refuses a worker that names none. The selector
   and the expected identity are written into that worker's runtime profile,
   replacing the hard-coded value; the profile digest already covers them
   and is already per worker.
2. **Delivered** by one new versioned launch member.
3. **Applied** in the fresh argv. No fallback-model option is ever passed.
4. **Recorded by the worker** in the result document it already writes for
   the phase — the proposal result for an implementation, the review report
   claim for a review — so the record is inside the frozen, digested output
   of that attempt.
5. **Bound on the host at the ending**, in the settlement the Job store
   already writes for the attempt, beside the result id and manifest digest
   — and, for a review, beside the verdict id; for an implementation, beside
   the candidate checkpoint. That is the binding the owner asked for:
   attempt → attribution → candidate or verdict, each by identity and
   digest.
6. **Enforced** in the same ending, before a candidate is accepted or a
   verdict recorded: only an outcome of `matched`, with an evidenced CLI
   build equal to the selected one, proceeds. Anything else is refused with
   a typed cause and the phase is held for the owner. No retry, no
   substitution, no automatic recovery.
7. **Shown** in the attempt's published diagnostics, and available to the
   History view of W385263 as a recorded fact of that attempt.

After a hold, the owner may select a different model for subsequent
execution. That is a new composition (or, once W385263 delivers them, a plan
revision); the held attempt keeps its own record unchanged.

### 2.3 Matched, missing, conflicting

| Outcome | When |
| --- | --- |
| **missing** | No model identity can be read: the provider output is absent, truncated, unparseable, over the size bound, or names no model; or the CLI build could not be measured |
| **conflicting** | Identities were read but they do not establish the expected model: the expected identity is not among them; or a field that names one single model names a different one; or the evidenced CLI build differs from the selected one |
| **matched** | The expected identity is established and nothing above applies |

One case this table cannot settle by itself, and it is real, not
hypothetical: the pinned Claude build was measured (first contract F5)
reporting **two** identities for one invocation — the selected model and a
smaller helper model the CLI uses internally — with no field saying which
did what. Whether that is `matched`, and on what condition, is the question
in §4. Until it is answered N1 cannot be completed.

What a `matched` record proves, and does not: the provider reported the
expected model for that invocation, on the evidenced build. It does not
prove every token came from that model.

### 2.4 Old and new

- Workers composed under the earlier selection are unchanged: they pass no
  model, and nothing is enforced.
- For honesty, surfaces show their requested model as "not selected
  (account default)" rather than the profile's hard-coded label. That is a
  display correction to an existing false label (first contract F3, F4) and
  changes no admission.
- A worker image that predates this change reports no attribution record.
  Under the new composition that is `missing`: held, never accepted.

### 2.5 Separation class

Computed from the composed workers' provider and model, so the pool's label
is a consequence of the attribution inputs rather than an assertion.

## 3. Verification for N1 (replaces first contract §6.1, N1 list)

Deterministic; fake provider at its normal boundary.

Selection and delivery:

1. Composing under the new selection without a model is refused for every
   role and provider; with one, only that worker's profile digest changes.
2. The fresh argv carries exactly the delivered selector and no fallback
   option. A launch with no model under the new composition is refused by
   the worker.

The record:

3. The worker measures the CLI build from the program and records it; a
   build different from the selected one yields `conflicting`.
4. Observed identities are extracted from: a direct model field; usage keys
   only; both; neither. Each yields the outcome §2.3 and §4 assign.
5. Truncated, oversized, unparseable or absent provider output yields
   `missing`. Nothing is inferred from the requested selector.
6. The record names the evidence digest and the retained log; the digest
   matches the retained bytes.
7. The record contains no provider content.

Binding and enforcement:

8. An accepted implementation's ending settlement carries the attribution
   beside the candidate checkpoint; an accepted review's carries it beside
   the verdict id. Each can be reached from the other by identity.
9. `missing` or `conflicting` → the result is refused with its typed cause;
   no candidate is accepted, no verdict is recorded, dependents stay
   closed, the phase is held, nothing retries.
10. The same for an implementation whose own verification passed: a passing
    verification does not rescue a missing attribution.
11. A record whose attempt id is not the attempt being ended is refused.
12. Restart between the worker's result and the ending replays the same
    decision.
13. A pre-change worker image under the new composition is held as
    `missing`.

Display and preservation:

14. Published diagnostics show requested, expected, observed, both CLI
    builds and the outcome.
15. A worker composed under the earlier selection behaves exactly as today
    and is shown as "not selected (account default)".
16. Separation class reflects the composed providers and models.

## 4. The next decision for the owner

**When a provider reports more than one model for a single invocation, when
does the attribution count as matched?**

Measured on the pinned Claude build: asked for one model, its result named
that model **and** a helper model. The Codex build's behaviour is unknown
until it is pinned and inventoried.

- **A — Declared helpers only (recommended).** The worker's profile names
  the expected model and, separately, any helper identities the owner has
  accepted for that provider build. `matched` requires the expected identity
  to be present and every other reported identity to be on that declared
  list. An unlisted extra identity is `conflicting`. The record keeps both
  lists, so a reader sees "selected model X; declared helper Y also
  reported".
  Attribution stays exact about what was allowed, and a new or changed
  helper is noticed instead of absorbed. Cost: the helper list has to be
  established per pinned build — the first real-provider qualification call
  supplies it — and a CLI update that introduces a new helper holds work
  until the owner accepts it.
- **B — Expected identity present is enough.** Any additional reported
  identities are recorded but do not affect the outcome.
  No list to maintain. Cost: a provider could do most of the work on another
  model and still read as matched, as long as the expected one appears at
  all. That weakens exactly the attribution this ruling is for.
- **C — Exactly one identity.** Any second identity is `conflicting`.
  Strictest. Cost: on the measured Claude build every run would be held,
  so the Claude reviewer could not be used at all.

I recommend A. I have not assumed it. It fixes the profile's members, the
`matched` rule in §2.3 and what the qualification calls must capture.

## 5. Decisions still open after that

| # | Decision | Unblocks |
| --- | --- | --- |
| D1 | CLI pins: which Codex build; whether the Claude pin moves | N3, N4 |
| D2 (values) | The Fable selector and expected identity; the Codex model identifier | N5 |
| D3 | Codex credential kind and registry reference | N3, N5 |
| D6 | One private provider-home mount for workers that declare it | N3 |
| D7 | Selection of the engine-only image gates and the two real-provider calls | N4, N5 |

## 6. Limits

- Nothing executed.
- That the worker never measures the CLI build is a survey statement
  (`worker/claude_agent.py`, no version call found); I did not re-read every
  path.
- The two-identity behaviour is taken from the September qualification
  dossier's record of real 2.1.247 runs, not measured by me, and may differ
  on another build.
- Running the program's version command inside the worker is a local,
  deterministic act with no provider call; whether every provider CLI
  answers it without network or credentials is to be confirmed in the
  engine-only image gate.
