# Progress

## Step 1 — the fix, wider than the evidence (2026-08-18)

`zipapp.create_archive` stamps every member with its staging mtime.
`tools/deploy_work.py` now writes the archive itself, deterministically:
fixed member timestamps, fixed modes, a pinned `create_system`, sorted
enumeration, and stored entries. Nothing in the artifact derives from
the clock or the host.

**The recorded evidence understated the defect, and the fix is scoped to
the defect rather than the evidence.** The investigation found exactly
one differing member, generated `__main__.py`, because the copied
sources kept their mtimes between two builds inside one checkout. That
was luck. Every one of the fourteen members carried a source mtime —
verified against the reviewed artifact, whose members show thirteen
distinct timestamps — so a fresh clone, a rebase, or a single touched
file would have moved the rest too. A `__main__.py`-only correction
would have passed the recorded reproduction and still shipped a
non-reproducible builder.

Three host dependencies are closed, not one:

- **mtimes**, the observed cause;
- **`create_system`**, which `ZipInfo` otherwise takes from the BUILD
  HOST, so identical sources would differ between a Linux and a Windows
  builder;
- **enumeration order**, since `os.walk` returns filesystem order —
  inode order on some filesystems — and the old path never sorted.

The generated bootstrap is byte-for-byte what `zipapp` wrote, so the
ruled entry point is untouched: `cli:entry`, NOT `cli:main`, because
zipapp discards the target's return value and that turned refusals into
exit 0 (the WF-06 lesson).

## Step 2 — acceptance (2026-08-18)

`tests/work/test_w4_reproducible_release.py`, 5 checks. Four are
hermetic and run against a synthetic staging tree, so the suite never
perturbs the checkout's own mtimes: a 700-million-second mtime
difference producing identical bytes; fixed metadata across EVERY
member; sorted member order; and the bootstrap, shebang, and executable
mode unchanged. The fifth is the operator-level property, marked
serial — deploy twice for real, and compare both the artifacts and the
digests the deployer reports, including that the reported digest
actually describes the bytes on disk.

Break-sweep: restoring `zipapp.create_archive` reds 3 of the 5.

### Measured

- Two consecutive deployments: `archive_sha256`
  `fb6f209aa2d27fe076e0b53a6dcc4cc5a6bf30cf90c582bc7f3f1f32c384c880`,
  byte-identical.
- After touching every `src/baton_work/*.py`: same digest, same bytes.
- Archive: 14 members, one distinct `date_time`, one `create_system`,
  all `ZIP_STORED`, sorted.
- The installed artifact runs `--help` and `init`; deploying over an
  existing release still refuses.
- Gate: **1079 passed** + 5 serial + acp 36/36 on 32 cores.
- Whitespace check clean.

## Not done here — the last plan step is not an agent's to take

The remaining step ("after the correction is committed, deploy it to a
new immutable release directory and verify stable rebuild digests before
using that release") requires a commit, and agents in this repository
never perform mutating version-control operations. It is left for
Slawomir after review. The digest above is what that release should
reproduce; if it does not, the artifact does not match the reviewed
source.

## Step 3 — review round 1 (2026-08-18)

Both corrections were right, and the first one uncovered a flaw in my
own test harness.

**The unused `stat` import** is gone. Mine — added when swapping the
`zipapp` import out and never used.

**Member modes are now asserted.** The reviewer's point is exact: mode
was the one metadata the implementation claimed to fix and no test
checked, and it is the only assertion that can distinguish the
intentional constants from a return to host-derived defaults. Every
directory member carries `DIR_ATTR`, every file member `FILE_ATTR`.

I then found my first version of that assertion was partly
self-referential. Comparing only against `deploy.FILE_ATTR` moves BOTH
sides of the equality when the constant is edited, so a silent mode
change would have shipped green — the umask accident the assertion
exists to catch. It now also pins the literal values (0644 for files,
0755 for directories), and the sweep that changes the constant reds.

### A latent hazard in the break-sweep method itself

Proving that took two attempts, because the first umask sweep reported a
false GREEN. Cause: `_deployer()` loaded the module through
`spec_from_file_location`, which honours `__pycache__`. A cached `.pyc`
is reused when the source's (mtime, size) match what it recorded — and
`0o100644` -> `0o100600` changes neither length nor, at that moment, the
recorded second. The test asserted on constants that were no longer on
disk.

This matters beyond one test: every break-sweep in this repository
edits a source file and immediately reruns pytest, so any sweep whose
edit preserves file length can silently report the wrong colour. Most
sweeps add or remove lines and are therefore safe by accident, not by
design.

`_deployer()` now compiles the source bytes directly, so it can never
read a cached build. Both mode sweeps then behaved correctly: changing
the constant and dropping the assignment each red exactly
`test_every_member_carries_fixed_metadata` and nothing else.

### Evidence

- Focused: `test_w4_reproducible_release.py` 5 passed,
  `test_deploy_v11.py` 11 passed.
- Gate: **1079 passed** + 5 serial + acp 36/36 on 32 cores.
- Two fresh deployments still agree byte for byte on
  `fb6f209aa2d27fe076e0b53a6dcc4cc5a6bf30cf90c582bc7f3f1f32c384c880`.
- Whitespace check clean.
