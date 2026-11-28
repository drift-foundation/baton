# Retired PyInstaller build output (W386626, follow-up history)

This dossier's Work (W197661) is closed. This note is follow-up history appended by W386626 (repository evidence
cleanup, slice 1; see `work/records/2026/11/finding-repository-evidence-cleanup/`). Nothing earlier in this dossier was
edited.

## What was retired from the repository tip

Five PyInstaller build trees: 461 files, 247,625,051 bytes, which was 15% of `work/records`. They were the bundled
interpreter, shared libraries and the `baton-v12-stack` executables of four historical builds:

- `instance-200000/build/distro/` and `instance-200000/build/distro2/`
- `instance-200254/build/distro/`
- `instance-200564/build/distro/`
- `instance-201492/build/distro/`

**Kept in place:** everything else in each `build/` directory. That includes `fixture.iid`, which
`tests.manager.test_w197661_verifier` reads, plus the build, install, start, submit and capacity logs and the status
JSON.

`RETIRED-DISTRO-W386626.json` lists every retired file with its mode, Git blob id, size and sha256.

## Where the bytes are

- **The last commit holding them:** `f07e7b2a6afe40bfe1458e557bc846a69a3b9974`. They were introduced unchanged in
  93da9d62.
- **The durable backup:** `origin` (`refs/heads/main`). It was verified on 2026-11-27 by fetching exactly these blobs
  from origin and comparing sha256 and mode.

## Restore

From the repository root:

```sh
git restore --source=f07e7b2a6afe40bfe1458e557bc846a69a3b9974 --worktree -- work/records/2026/09/finding-v12-worker-launch-version-mismatch/instance-200000/build/distro work/records/2026/09/finding-v12-worker-launch-version-mismatch/instance-200000/build/distro2 work/records/2026/09/finding-v12-worker-launch-version-mismatch/instance-200254/build/distro work/records/2026/09/finding-v12-worker-launch-version-mismatch/instance-200564/build/distro work/records/2026/09/finding-v12-worker-launch-version-mismatch/instance-201492/build/distro
```

- **The restored files are untracked** beside the checkout. To track them again, revert the retirement commit.
- **To extract elsewhere, without touching the working tree:**
  `git archive f07e7b2a6afe40bfe1458e557bc846a69a3b9974 -- <path> | tar -x -C <dir>`.

## Effect on retained scripts

`instance-201492/verify_lifecycle.py` measures `build/distro/out/distro` only when the directory exists
(`measure()`, `built_runtime`). Without the directory it reports `None`, not the digest pinned in `EXPECTED.json`.
Restore first before re-running that historical verifier's `main()` against its pin. Its unit tests do not measure the
directory.
