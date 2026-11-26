# W386308 owner checkpoint — read-only TUI, first slice

Prepared by K (`baton.prompt`). The owner alone stages and commits. Nothing was staged by me.

- Reviewed candidate: base `7961f8bd4f5aae1209c72f796acb693d5ba65b76` plus combined patch SHA-256 `f0cc2bd83ac98ddb8b7918f5d5bae1cfce13e8156363bc7bda86730ff9e0c4c6` (`../correction-386357/combined.patch`, per-file digests in `../correction-386357/manifest.json`).
- Accepted by Codex in `../../review-2026-11-26T04-05-35Z.md` (first review `../../review-2026-11-26T03-55-01Z.md`, corrected by delta `00d4edcf…`).
- Main is `38ea1a07`. It differs from the base only in `packaging/stack.spec` and `tests/tools/test_packaging.py`, which the candidate does not touch, and `v12/DESIGN.md` at `38ea1a07` equals the base's.
- The working tree already holds the reviewed bytes for seven of the eight paths. `v12/DESIGN.md` in the working tree also has unrelated uncommitted edits, so its reviewed hunk is staged separately from `design-obs2.patch` (SHA-256 `2669c8dbd05d704defe19a10cca2c702d8173d00f91735cbeb8b4078d689aeee`). Applied to the committed `DESIGN.md`, that patch gives exactly the reviewed file (`4194efa0…`).

## Commands

From `/home/sl/src/baton`:

```sh
git add -- v12/python/tools/job_tui.py v12/python/tests/tools/test_job_tui.py v12/python/tools/stack.py v12/python/tools/stack_command.py v12/python/tools/parallel_test.py v12/python/tests/tools/test_work_command.py v12/python/JOB-VIEWER.md
git apply --cached work/records/2026/11/finding-v12-readonly-operator-tui/evidence/checkpoint-386358/design-obs2.patch
/home/sl/.local/state/baton-v12-venv/bin/python -B work/records/2026/11/finding-v12-readonly-operator-tui/evidence/checkpoint-386358/check-staged.py
git commit -m "Add a read-only terminal interface for watching v12 Jobs"
```

- `git apply --cached` changes only the index; the working tree's other `DESIGN.md` edits stay uncommitted.
- `check-staged.py` is read-only and must print `"ready": true`: eight staged paths, each byte-equal to the reviewed candidate, nothing else staged.
- Commit with no path and no `-a`. A path or `-a` would take the whole working-tree `DESIGN.md`.

Not verified by me: I did not run `git apply --cached` anywhere; my rehearsal of these commands in a disposable repository was not permitted. I checked the hunk with `patch` on a copy of the committed file.

## Build and open the packaged TUI

After the commit, so the bundle's stamp names a clean commit:

```sh
(cd v12/python && /home/sl/.local/state/baton-v12-venv/bin/pyinstaller --noconfirm --clean --distpath build/out --workpath build/work packaging/stack.spec) && v12/python/build/out/distro/baton-v12-stack tui --root /var/tmp/baton-w386308-native-job/live
```

- The build line is the one `just build` runs, without its pip step; it is also what the passing field run used.
- `--root DIR` makes the TUI read `DIR/status.json`. The native launch packets write their Job's status to `<private root>/live/status.json` about every two seconds, so name the `live` directory of whichever packet you launch. The path above is this Work's own packet root.
- It can be opened before the launch: it shows `not read yet` until the file appears. For an installed instance use `tui --instance <destination>/instance.json` instead.
- Not verified: no bundle has been built with the `tui` verb. This is its first packaged run, and it is the open item in both reviews. If the bundle lacks `tools.job_tui` or `curses`, the command fails at start with an import error; the unpackaged equivalent is `cd v12/python && PYTHONPATH=src:. /home/sl/.local/state/baton-v12-venv/bin/python -B -m tools.job_tui --status /var/tmp/baton-w386308-native-job/live/status.json`.
