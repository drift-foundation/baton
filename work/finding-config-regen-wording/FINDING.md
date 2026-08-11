# Config regeneration wording contradicts the ceremony

Status: **confirmed documentation defect; queued for the next release window**.

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

