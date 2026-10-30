# Checkpoint — this packet has ONE drifted member and is NOT owner-runnable

Written under claim358915 (2026-10-23T20:4xZ), after owner release358877 and
the owner ruling recorded in FINDING "2026-10-23 — owner redirects retry work
to the manager now" and DESIGN REC-7.

## The drift, stated first

`INDEX-HASHES.txt` and `review-2026-10-23T05-45-38Z.md` both record
`fresh_attempt.py` at

    64d4442c445d85a8002f2d98e5069abf229e2f0204c27eb46e1638ba47aff621

The file on disk is

    15dd4b084e96bb40dc71b4c9c53b03a7d17da775be58d729b38262079ebdb919

mtime `2026-10-23T05:53:27Z`, which falls inside claim358825 (05:46:07Z to the
owner's release at 05:54:03Z). That claim began the correction this packet's
review asked for and was stopped for the server shutdown before it recorded
anything. **These bytes were never journalled, never proved and never
reviewed.**

**The reviewed `64d4442c` bytes no longer exist anywhere.** Its `/tmp` twin was
lost when the host rebooted — boot `2026-10-23T20:17:05Z` — and this packet is
untracked in version control, so there is no copy to restore from and I have
not fabricated one.

**`INDEX-HASHES.txt` is deliberately left alone.** Running `sha256sum -c
INDEX-HASHES.txt` in this directory now FAILS on `fresh_attempt.py`, and that
loud failure is the correct signal. Rewriting the manifest the reviewer
verified would have silenced it. This file is the explanation the failure
should lead you to.

Every other member matches its recorded digest.

## What the partial revision contains — characterised, not proved

It answers all three blockers of `review-2026-10-23T05-45-38Z.md`. It compiles
(`py_compile`, this claim). Nothing beyond that is established.

- **Store boundary.** `accountable_digest` no longer walks `db/`; `ACCOUNTABLE`
  is six ordinary documents plus `generated` and `state/task`. `work_is_free`,
  which copied `authority.sqlite3` with its WAL and SHM and opened the copy, is
  gone, replaced by `collisions_refused` reading ordinary configuration.
  `rehearsed` no longer copies `db/` — it mints a synthetic twin through the
  supported bootstrap from this instance's own `install-inputs.json` and
  `generated/bootstrap-inputs.json`. The two questions this cannot answer are
  named as operational findings in `MISSING_PROJECTIONS` rather than worked
  around: no supported command projects whether a Work id exists on an
  Authority (deferred to the apply operation, which the Authority itself
  guards), and no supported command freshly observes runtime liveness
  (`manager status` says of itself that it does not refresh the runtime axis).
- **Inherited pins.** `pinned_helper` enforces `configure.INHERITED_PINS` at the
  consumption path, alongside the `configure.py` and fresh3 template pins.
- **Quiescence.** `projection` judges a canonical published projection with the
  product's own stage vocabulary, bounded by `QUIESCENCE_MAX_AGE_SECONDS=600`,
  and fails closed on unmet OR unknown; `check` and `apply` both call it, and
  `commands` emits `0_stop_if_not_quiescent` ahead of the apply.

**`prove.py` and `evidence/PROVE.json` are the OLD, reviewed artefacts at their
recorded digests. They describe `64d4442c` and DO NOT describe the bytes on
disk.** The 39-check result stands as evidence about the superseded revision
only. Likewise `evidence/LIVE-CHECK.json` was produced by the old revision,
whose live probes the review correctly rejected; it is retained as history and
is not a permitted production-check path.

## Status

**Do not hand this to the owner.** `/tmp/w325959-fresh-attempt.py` does not
exist — the reboot removed it — and the durable copy is an unproved
work-in-progress. Nothing in this packet has been run against instance 3 since
the owner's own `quickstart-c` attempt.

The correction itself is superseded. DESIGN REC-7 and the owner ruling move
atomic Job-identity uniqueness, fresh-attempt admission and replay into the Job
manager behind a thin CLI, and say in terms that script-side prechecks cannot
substitute for manager enforcement. This partial revision is preserved as the
measured input to that work — particularly `MISSING_PROJECTIONS`, which names
exactly what the manager operation has to own — and not as something to finish.

## Preserved and unchanged

`quickstart-c`, its Work `5a8fa4b4-W1`, its binding, workers, attempt logs and
published status; instances 1, 2 and 3; the accepted `fresh3-358443` packet;
`post-install-357462/configure.py` at `b15280cc`. No store was opened, copied,
traversed or hashed under this claim. No submit, serve, start, stop, engine,
provider, model or credential read. No Git and no change under `v12/`.
