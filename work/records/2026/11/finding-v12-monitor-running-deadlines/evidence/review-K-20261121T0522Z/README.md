# Independent review evidence — K (`baton.prompt`), W385427 E385443 candidate

- `custody.json`: per-path SHA-256 of candidate, base, `git show 7ac02c7f:path` and host bytes against the manifest; tree/manifest/handoff/patch digests.
- `focused-K.log`: the author's `run_focused.py` (copied here) run by K on an ISOLATED tree outside the checkout (`git archive 7ac02c7f` + the 13 candidate files overlaid, every byte re-digested), prepared interpreter, `PYTHONPATH=src:.`, bytecode disabled, disk-backed TMPDIR/roots under `/var/tmp/baton-v12-w385427-review/`, the author's `no-git` shim first on PATH. Result: Ran 347, OK, 2.305 s unittest / 2.905 s wall.
- `git-confinement-scan.json`: every logged Git invocation of the author's five confined compatibility runs scanned for a target or path argument outside `work/scratch/w385427/`; none found (1434 invocations, 32 refusals in runs 1–4 as diagnosed, 0 in run 5).
- The two deep compatibility cases were NOT rerun by K (their fixtures mutate Git in disposable repositories under the owner's exception granted to the implementation run); their retained logs were inspected instead.
No host import, no live-instance read or change, no product edit, no Git mutation.
