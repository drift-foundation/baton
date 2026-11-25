# Credential lifecycle correction — draft for independent review

Candidate **sha256:7f45e1e53d5f4608123cb8f6dba9ec9a701f6b5f89ac4c7e65ad0660eb6066b8**, archive sha256 `938b2b9b561f72d7993f589f2fcd66f5ca6e6b4596109ec80326238dc6381c9b`. Eight product/doc/test paths in candidate-manifest.json, full bytes in candidate-files.tar.gz, exact delta against retained before-images in delta.patch. Base **c1727ad68ffa0f5015b07f27202a66be00848143** (human build-context checkpoint observed). DESIGN before-image additionally contains the two already-existing owner paragraphs; preserve them. Main product files are unchanged.

## Outcome

Selected seeded-retained mode now resolves/copies the configured source automatically during first host preparation, before engine launch. External host receipt and worker path-bound marker retain initialization state. Ready-home restarts validate metadata without opening the credential or resolving original source/registry; provider refresh is preserved. Missing/invalid credentials and interrupted/mismatched receipts produce explicit recovery, not reseeding. Existing unmarked seeded homes require explicit recovery/migration; no automatic migration/reset is supplied. Legacy delivered mode remains unchanged.

The successor qualification launcher automates copying through the same host lifecycle. It needs a once-configured selected source reference/file and copy authorization, not manual per-Job copying. Its helper preserves restart state even after source/config deletion. --check verifies pinned code without accessing credentials. It emits engine vectors only after preparation; no engine/provider invocation is in the launcher. Original packet71c44a15 remains unchanged.

## Verification

Affected groups: manager-pure and tools-pure; focused supported just test-one only. **314 collected,314 executed,314 passed**,22.036232572 seconds, exit0. No skips, duplicates, unaccounted ids or source drift. Full selection, collection, stdout/stderr, header, ledger and before/after source identities retained as final-01.*. This is explicit focused-id accounting, not a whole-group/suite green claim. The 44-case iteration and all failed exploratory runs remain. No baseline failures occurred in the final selected cases; no broad group or earlier incident group was rerun.

Coverage includes actual composed manager close/reopen with an absent synthetic credential registry, next worker turn and final completion, preserving simulated refresh without calling the resolver. Missing credential reaches the real attempt preparation failure before provider invocation; helper tests cover interrupted copy, marker loss/corruption/path/permissions, collision refusal, independent homes and legacy references. Qualification tests exercise real file copy/private permissions/distinct inode, deleted source+config restart, missing credentials and null authorization. No real providers/engine; fake boundaries explicitly labelled.

Prepared interpreter /home/sl/.local/state/baton-v12-venv/bin/python. Fixture root /var/tmp/baton-credential-lifecycle-386081 outside all repositories; candidate clone has independent .git, no linked metadata. W386057 isolation files are separately inherited verification inputs, excluded from candidate path set. No protected metadata cleanup or mutation.

## Ownership, review and gates

Claim E386081; ownership coordination M386082/M386084/M386085. K has not replied as of M386085. Disjoint scratch and new evidence were used; no shared product/dossier overwrite. FINDING.append.md, PLAN.append.md and PROGRESS.append.md retain exact proposed appends for coordinated import; RULING-AND-PLAN.md pins the owner instruction and acceptance before implementation. Independent review may consume these exact bytes now; confirm main ownership and drift before import.

No Codex realization, credential-path activation, managed entry, N4b parser, success classification or conversation-resume work changed. J1/N4b/native qualification remain gated. W386048 and W386057 stay separate. Stage B source/access, explicit model, image/tools and execution selections remain unresolved; current renderer still pins N3 image lacking git, while newer image tool evidence does not itself select execution.

Limits: synthetic verification does not establish authentication, vendor refresh schema, credential size suitability or live behavior. Existing manager source materialization retains its4096-character bound; shared copy ceiling is1MiB. No real credential was inspected to choose/change those limits. Current worker-managed credential lifetime remains private; no new credential values/hashes enter lifecycle receipts. Owner backup/checkpoint of this packet remains pending.

Next bounded milestone: independent exact-candidate review, then coordinated owner import/checkpoint.
