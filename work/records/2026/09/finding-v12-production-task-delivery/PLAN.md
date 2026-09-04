# Plan

1. [done, independent review 2026-09-04] Revalidate the missing `/input/task.json`
   path against the production composer, OCI mount vector, and certified
   Claude worker entry. Confirm whether another existing public operation
   already owns this delivery before adding one.
   Confirmed with `evidence/reproduce_missing_worker_inputs.py`: the production
   fixture projects `running` after one engine start, while both fixed worker
   paths are absent. No public operation owns the task file; the dogfood
   helpers are private, follow/parse/reserialize, and are not reusable here.
2. [done, approved 2026-09-03] Confirm the bounded profile decision
   recorded in FINDING: schema `/2` adds one absolute `task_document`; this
   profile defines its exact JSON bytes as `input_manifest.human_contract`;
   static validation reads once no-follow before Authority/offer/allocation;
   composition atomically publishes those held bytes as read-only
   `task.json`; restart re-proves the installed file; and the current copied
   source destination is fixed to `source`. If the task is not the manifest's
   human-contract artifact, stop: another durable task identity is required
   and a composer-only patch is not sufficient.
3. [changes requested 2026-09-04] The production-composer correction is in
   `tools/single_worker.py` and `DEPLOYMENT.md` and nowhere else. Schema `/2`
   carries the required absolute `task_document`; `_task_bytes` reads it once
   no-follow, ordinary and bounded during static validation and proves it
   against the manifest's `human_contract` media type, width, byte count and
   digest; the manifest's one source destination is fixed to `source`;
   `_published_task` installs the HELD bytes as read-only `task.json` before
   the source copy and before `compose_input_root` freezes the root; and
   `_proved_task` re-proves the installed document on every adopted root. No
   generic Worker Manager operation, Claude parser, dogfood composition, or
   W71917 source/workspace design was touched.
   Independent review found one remaining P1: `_published_task` protects the
   staging name with `O_EXCL` but uses `os.replace` for the final transition,
   so a foreign `task.json` created in the check/publish interval is silently
   overwritten. Make the final-name publication atomic and no-clobber, map a
   collision to the existing typed preparation settlement, preserve the
   foreign bytes, and clean only this operation's staging name.
4. [changes requested 2026-09-04] The whole recorded matrix runs. 63
   `tests.tools.test_single_worker` tests pass, including the positive
   composition, every static negative, the attempt-root negatives, the restart
   proof, and a real in-process `baton_worker` + `ClaudeAgent` `work` request
   over the composed root that reaches the provider seam through an injected
   runner. The dossier reproduction now reports `accepted` from the certified
   worker's own reader with both fixed paths present. Add a deterministic
   final-name race regression, the recorded FIFO static negative, and a
   fully-composed/stopped-before-start restart mutation case; the current
   changed-task case mutates only after a runtime is already running.
5. [changes requested again 2026-09-04] Independent review found the
   final publication transition clobbering: `O_EXCL` guarded only the staging
   name and `os.replace` finished the act, so a target appearing after the
   absence check was silently replaced. The transition is a no-clobber
   `os.link` now — the foreign target survives, only this operation's staging
   name is removed, and a typed refusal reaches the preparation journal with
   no runtime started. The negative matrix gained the FIFO case the
   `O_NONBLOCK` boundary exists for and the adopted-root case where the task
   changed after composition and before start.
   Correction review found the adjacent source-name race still open: the
   proved staging descriptor is closed before `os.link(staged, place)`, so the
   staging pathname can be replaced and `follow_symlinks=False` publishes the
   replacement symlink itself. Keep the final publication bound to the proved
   descriptor/inode; substitution must refuse without deleting the foreign
   replacement, record one preparation ending, and start no runtime. Add the
   exact staging-substitution regression.
6. [done, corrected and accepted 2026-09-04] The second review found the
   no-clobber link still publishing from the mutable STAGING name: a
   substitution there hard-linked a foreign symlink at the final name and
   returned success. The interval is removed rather than defended a third
   time — the document is created directly at its final name with
   `O_CREAT | O_EXCL | O_NOFOLLOW`, and the bytes, the readback and the mode
   all reach the descriptor that creation returned. Regressions cover a target
   that appears before the creation, a link at the final name that is refused
   and never followed, and the published object's identity: an ordinary
   single-linked 0444 file carrying exactly the held bytes.
   Two later Codex-backed review attempts were refused by the provider's
   cybersecurity classifier. Their remaining same-uid host-replacement concern
   is outside the already-approved M34768 trust model; the approver accepted
   the corrected ordinary-concurrency boundary without another hardening pass.
7. [ready after W81115 closes] Resume W71917 through the corrected production
   composition.
