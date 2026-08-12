# Config regeneration wording contradicts the ceremony

Status: **documentation corrected in next-generation source by
`baton.reviewer` and independently signed off by `baton.implementer` on
2026-08-11. Scratch-candidate documentation-hash verification remains.**

## Observed

`docs/AGENTS-MAILBOX-PROTO.md` says config changes use the audited `regen`
ceremony and that "direct config/database edits are forbidden." Read
literally, that forbids the config-file write the ceremony requires.

The released implementation reopens the same configured JSON path, requires
the offered generation to equal accepted generation plus one, and requires a
participant with the `config` capability. Adding a participant or root
therefore requires an administrator to write the proposed generation+1 JSON at
that path and then run `regen --participant <admin>`. Editing JSON alone has no
authority effect; editing SQLite directly is always forbidden.

The ambiguity was found while reviewing `docs/EFFECTIVE-BATON.md`; that guide
now states the actual workflow.

## Source revalidation — 2026-08-11

The queued correction must include one operational consequence the existing
guide still understates.

**Confirmed:** `_check_meta(..., for_regen=True)` accepts only an offered
config whose `generation` is exactly the authority's
`accepted_generation + 1`. `regen_instance()` then checks the caller's
`config` capability and, in one transaction, validates protected live
participants and retained external-root bindings before updating accepted
generation, config digest, and accepted roots.

**Confirmed:** the proposed JSON write has no authority effect by itself, but
it is not operationally inert. Normal `open_instance()` calls require the
file's generation and digest to equal the accepted authority state. From the
moment a generation+1 proposal replaces the accepted JSON until `regen`
succeeds, ordinary reads and writes refuse with the accepted-config mismatch.
If `regen` refuses, the authority remains unchanged; the operator must either
correct and retry the still-generation+1 proposal or restore the byte-exact
accepted JSON before ordinary work resumes.

**Confirmed:** raw SQLite edits remain forbidden. Restoring or replacing the
JSON proposal is not a database bypass: the accepted digest/generation in the
authority is still the gate. Calling every config-file write “direct config
editing” obscures the ceremony's required input and should be removed.

## Release constraint

Do not edit the protocol document in the just-released 1.0.0 tree as part of
the Effective Baton guide. `dist/DISTRIBUTION.json` pins
`protocol_doc_sha256`; changing the document would mutate a released
distribution manifest for a wording fix.

## Proposed correction

In the next reviewed release window, replace the ambiguous protocol sentence
with wording that distinguishes the required proposed-config write from the
audited acceptance step and the prohibited raw-database bypass. Rebuild and
verify the distribution manifest in that release.

No protocol, schema, config-ceremony, or authority behavior change is proposed.

## Exact 1.1 documentation correction

Replace the protocol paragraph with wording equivalent to:

> To propose a config change, an administrator writes a valid generation+1
> JSON document at the same explicit config path, then a participant with the
> `config` capability runs Baton's audited `regen` ceremony. The file is only
> a proposal until `regen` accepts it transactionally; while it differs from
> the accepted generation/digest, ordinary operations refuse. If acceptance
> fails, correct and retry the generation+1 proposal or restore the exact
> accepted JSON. Never edit the SQLite authority directly or treat an
> unaccepted config file as active state.

Update `docs/EFFECTIVE-BATON.md` in the same change. Its current sentence
“Editing the file alone changes nothing” should instead say “changes no
authority state and temporarily makes ordinary operations refuse until the
proposal is accepted or the accepted JSON is restored.” Keep the capability,
same-path, exact-generation, and one-transaction statements.

The ordinary implementation delta is documentation only. Do not modify the
frozen 1.0 distribution manifest. Focused verification checks the two passages
and current regen/open behavior; the 1.1 candidate build must carry matching
documentation hashes in its scratch distribution. Slawomir's deliberate
release action, not an ordinary documentation edit, replaces canonical
artifacts/manifests.

## Documentation correction — 2026-08-11

At Slawomir's explicit instruction, `baton.reviewer` corrected both source
documents. They now distinguish the required same-path generation+1 JSON
proposal from transactional authority acceptance, state that ordinary
operations refuse while the proposal differs from the accepted
generation/digest, give both recovery paths after refusal, and prohibit raw
SQLite edits or treating an unaccepted file as active state.

This is next-generation source only. Frozen 1.0 artifacts and manifests remain
unchanged. Independent review and scratch-candidate documentation-hash
verification are still required; the author does not self-sign off.

Focused verification matched every required phrase in both documents and ran
the existing accepted-config mismatch, digest drift, exact-next generation,
capability, live-participant, additive-change, retained-root, and regen-race
tests: 8 passed, 564 deselected. No existing test, artifact, manifest,
authority, or config was modified.

## Independent review — 2026-08-11

`baton.implementer` independently signed off the corrected source wording in
`review-2026-08-11T19-39-32Z.md`. The reviewer checked all eight required
statements against behavior and ran `tests/core -k regen`: 11 passed. The
review specifically confirmed that the accepted digest makes “exact accepted
JSON” load-bearing and that ordinary operations correctly refuse when either
the generation or digest differs.

No review edit was made to the documents or tests. Candidate-build hash
verification remains pending and is deliberately separate from source sign-off.
