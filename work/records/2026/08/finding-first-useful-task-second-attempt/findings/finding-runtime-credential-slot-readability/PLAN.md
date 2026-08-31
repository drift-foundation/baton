# Plan

1. [done] Obtain and pin the approver's explicit security ruling for live
   credential reader identity, file gid/mode, root mode, and adapter refusal.
2. [done] Revalidate the exact group flow from deployment configuration into
   credential materialization and the OCI execution vector. `_launched` already
   holds the one nominal configured group before both materialization and
   adapter construction; no new configuration lookup is needed.
3. [done; independently signed off] Fresh materialization has the ruled
   descriptor ordering, recovery proves the manager-owned `0700` root, and one
   authoritative constant names `0640`. The remaining live `0600` prose is
   replaced in `credentials.py` (twice), `launch.py` and `test_credentials.py`,
   and recovery now drives owner and gid drift deterministically by controlling
   the slot's `lstat` answer rather than by chowning an inode. Reviews:
   `review-2026-08-31T13-56-33Z.md` and
   `review-2026-08-31T15-45-28Z.md`; response in `PROGRESS.md`, third round;
   sign-off in `review-2026-08-31T16-20-31Z.md`.
4. [reviewed] Adapter preflight distinguishes missing from unreadable with
   `os.access` before provider launch and opens no bearer.
5. [done; inventory gate superseded] Focused unit checks and the exact two-case
   real-Docker transcript pass. W54182 durably owns the already-preserved
   hours-long boundary-inventory failure and explicitly makes it non-gating for
   this Work; do not rerun that aggregate or remove unrelated pre-existing
   containers. The inventory delta this Work does contribute — two unowned
   `workspace_group` receiving entries in `credentials.py` — is recorded on
   W48697, which owns that global debt.
6. [done] Independent review signed off in
   `review-2026-08-31T16-20-31Z.md`; close satisfying and return W51487 for a
   wholly fresh retained attempt.
