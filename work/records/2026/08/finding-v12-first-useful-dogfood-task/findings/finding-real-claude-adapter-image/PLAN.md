# Plan

1. Revalidate W17110's pinned Claude image facts and the current
   `baton_worker.main(agent=...)` seam.
2. Implement a worker-side Claude adapter with a closed argv, bounded prompt
   and response, explicit fixed credential slot and typed failure mapping.
3. Add the dogfood image/entrypoint without importing the spike lifecycle.
4. Copy the exact staged source into bounded private scratch, run the frozen
   task there and author only the declared proposal tree.
5. Prove positive shape and provider negatives without a live credential;
   build/probe the image if the engine gate is available.
6. Return W39357 for independent review. Do not begin operator composition or
   authorize a live credential/network posture under this claim.

## 2026-08-29 — first implementation round under W39357

1. [done] Revalidated W17110's pinned installation facts and the
   `baton_worker.main(agent=...)` seam against the tree. Two facts changed the
   design and are recorded in `FINDING.md`: the accepted `--read-only` posture
   makes an image-owned credential link unusable, and the accepted `run_vector`
   composes no `--env` at all, which is what keeps an ambient
   `ANTHROPIC_API_KEY` from silently outranking the mounted slot.
2. [done] `v12/worker/claude_agent.py` — closed argv, composed (never
   inherited) child environment, the fixed credential slot linked into private
   `/tmp` scratch without reading a byte, bounded no-follow source copy, and a
   typed failure mapping in which no branch can report `completed`.
3. [done] `v12/worker/Dockerfile.claude` and `v12/worker/dogfood_entry.py` —
   W6633's worker program unmodified with this image's agent injected at its
   documented seam, W17110's pinned CLI version and trust store, the same fixed
   `65532:65532`, and no `baton_v12` import path.
4. [done] The task's frozen document contract: `/input/task.json`, schema
   `baton.dogfood-task/1`, closed over five members. W39358 stages it and
   W39364 writes the first one.
5. [done] `v12/python/tests/manager/test_claude_agent.py` — 43 cases, no
   provider, no network, no secret. Registered in the parallel phase.
6. [NOT DONE, and it is the acceptance's own boundary] The first live provider
   invocation. It needs the operator's exact credential grant and an approved
   network posture and belongs to W39364.

## 2026-08-29 — second implementation round under W39357

1. [done] **[P1] The provider-authored tree is revalidated before it is read.**
   `_checked_tree` holds the candidate to the staged tree's own rules at the
   moment of USE — regular files and directories only, no link at any depth,
   bounded on both axes — and `_diff`/`_publish` consume that checked list.
   Every read opens `O_NOFOLLOW` and proves the descriptor regular, so a link
   created between the walk and the use is refused rather than followed.
2. [done] **[P1] Both captures are bounded before allocation.** Streams go to
   files under the private tmpfs and only a window is read back; provider
   stdout is discarded outright because nothing reads it. Held by cases that
   drive real oversized output through a real `subprocess.run`.
3. [done] **[P2] `source_root` is held by equality to `SOURCE_ROOT`**, as
   `schema` already was. Containment was the wrong rule: a sibling inside
   `/input` is exactly as payload-selected as `../elsewhere`.
4. [done] **[P2] The no-secret image gate exists and is built.**
   `tests/manager/test_dogfood_image.py`, eleven cases, registered as the
   thirteenth serial module. It builds the image and asks the ARTEFACT for the
   pinned CLI version, the trust store, the copied program, the entrypoint's
   behaviour, the injected adapter, the byte-identical worker, the absent
   credential and the fixed identity.
5. [carried by W39770] The seam defect that gate found: `main(agent=...)`
   imports the scripted default unconditionally, so the injection seam cannot
   be used without shipping it. Stopgap in the recipe, named as one, with a
   case that fails when the seam is fixed.
6. [NOT DONE, unchanged] The first live provider turn — W39364, gated on the
   operator's credential and the approver's network posture.

## 2026-08-29 — third implementation round under W39357

1. [done] **[P1] A checked path is a descriptor chain.** `_open_under` walks
   every component `O_NOFOLLOW | O_DIRECTORY` relative to the one above it and
   `fstat`s what it opened; `_diff` and `_publish` read only through it, on
   both the candidate and the staged side. `_revalidated` re-proves the checked
   list after the payload's own verification command and before publication
   begins, so a mutated tree refuses before the first output byte.
2. [done] **[P1] Captured streams have no name.** `_capture` uses
   `tempfile.TemporaryFile` and `_window` reads the held descriptor rather than
   reopening a pathname; the verification capture no longer lands in the
   candidate at all.
3. [done] **[P2] The entry ceiling counts directories.** One shared `_bounded`
   check applied by both walks. `_copy_tree` still answers the number of files
   copied, which is what `result.json` reports.
4. [done] Removed `_relative`, dead since the first round.
5. [done] Focused suite is 55 cases, including the reviewer's three additive
   regressions and four of mine that hold the new invariants directly. The
   no-secret image gate rebuilt and ran; the whole v12 suite ran.
6. [NOT DONE, unchanged] The first live provider turn — W39364 — and W39770's
   seam correction, which the recipe still works around with a named stopgap.

## 2026-08-29 — fourth implementation round under W39357

1. [done] **[P1] The measured bytes are bound through publication.** `_diff`
   answers a sha256 per candidate file; `_revalidated` re-walks under both
   ceilings, proves every measured path present and every measured file
   unchanged; `_publish` reads once, proves the same digest at the moment of
   use, and writes those bytes. A mismatch refuses before the proposal exists.
2. [done] Post-verification additions and growth are re-accounted, because the
   revalidation is a FRESH walk rather than the fixed list.
3. [done] Additions are tolerated and unpublished; mutation and deletion of a
   measured path refuse. Six additive cases hold the rule from both sides.
4. [done] The stopgap guard now asserts the real condition. W39770's seam fix
   moved the import instead of deleting it, so the old assertion could never
   have fired.
5. [OWED, gated] Remove `scripted_agent.py` from the recipe and update that
   guard, ONCE the approver accepts W39770. Named here so the integration is
   not stranded, per the review's closing paragraph.
6. [NOT DONE, unchanged] The first live provider turn — W39364.

## 2026-08-30 — fourth-round review

1. [confirmed] The measured-byte binding, fresh bounded walk and unpublished
   bounded-addition rule close `review-2026-08-29T22-51-53Z.md`'s finding.
2. [changes requested] Close the direct credential stream paths reproduced by
   the two additive regressions in `test_claude_agent.py`: provider stderr is
   copied into `result.json`, and provider-edited verification code can print
   the still-mounted bearer into `verification.txt`. Pin the evidence-stream
   decision before implementation; do not read/hash/inspect the bearer as a
   redaction workaround.
3. [changes requested] W39770 is now closed satisfying. Remove
   `scripted_agent.py` from `Dockerfile.claude`, retire the obsolete presence
   guard and rerun the authorized no-secret image build/probes.
4. Return for independent review. The live provider turn remains W39364's.

## 2026-08-30 — fifth implementation round under W39357

1. [done] **[P1] The stream-evidence decision is pinned first**, as the review
   required, in `FINDING.md` under the fifth-round heading: no byte a child
   wrote is published, the streams are not read at all, and the two branches
   the review offered are answered — isolation is unavailable inside the
   accepted posture, and redaction cannot have an enforceable source of truth
   without violating the no-read rule.
2. [done] **[P1] Both children run on `subprocess.DEVNULL`.** `_capture`,
   `_window`, `MAX_DIAGNOSTIC` and `MAX_VERIFICATION` are deleted; one `_ran`
   helper is the whole boundary. The reviewer's two additive regressions pass,
   rewritten to drive real children so `DEVNULL` is actually exercised.
3. [done] **[P1] The third sink is closed too.** `why` feeds `recap`, so the
   provider diagnostic also reached the worker's `/output/output.json`. Both
   the review's named sinks and this one have cases.
4. [done] `verification.txt` carries the operator-authored frozen command, the
   ending, and an explicit statement that the output is withheld and why.
5. [done] **[P2] W39770 is integrated.** `COPY scripted_agent.py` removed from
   `Dockerfile.claude`; `test_dogfood_image` asserts the module's absence from
   the artefact and still holds the seam property that makes it safe. The
   no-secret image gate was rebuilt and rerun here.
6. [NOT DONE, unchanged] The first live provider turn — W39364. Recorded with
   it: withholding provider diagnostics is a real cost to bringing that turn
   up, and the remedy if it bites is an operator-authorized diagnostic mode as
   later-pass Work, never publishing untrusted bytes by default.

## 2026-08-30 — fifth-round independent review

1. [confirmed] Both child processes send both streams directly to
   `subprocess.DEVNULL`; the adapter retains only the return code, so provider
   or verification output cannot reach proposal metadata, evidence, or the
   worker recap.
2. [confirmed] The revised real-child regressions preserve the two review
   attacks and add the previously unnamed recap sink. Deleted tests covered
   capture helpers and ceilings that no longer exist; the retained assertions
   prove the frozen command, ending, and explicit withholding notice remain.
3. [confirmed] W39770 is integrated: the Claude image no longer copies
   `scripted_agent.py`, and the image gate holds both artefact absence and the
   lazy-default seam that makes the absence safe.
4. [done 2026-08-30] The focused adapter and independently runnable adjacent
   suites pass. The managed reviewer cannot reach Docker and therefore makes
   no independent image-build claim; the implementer's recorded fresh build,
   eleven no-network probes, matching adapter digest, and absent scripted
   module are the available image evidence.
5. [done 2026-08-30] Signed off for approver acceptance. The first live
   provider invocation remains separately owned by W39364.
