# MANUAL research field test, corrected packet (r3)

Prepared by K (`baton.prompt`, Fable 5.2) on the owner's instruction after the second field run. I wrote r2, r3 and the packaging correction; none is independently reviewed. Manifest `SHA256SUMS`: `df46073ef97dc30a232c65ff6098b2ff42620817b3612b223177c4b3cd706f9e`. Packets `../field-76b2f2b2/` and `../field-76b2f2b2-r2/` and both failed run roots are unchanged.

## What the second run showed

Root `/var/tmp/baton-manual-field.Enw7qwzp` (preserved). The packaged preflight passed, the image and network were built, the worker was installed, the stack started and `manager create` recorded **field-survey**. `manager add-phase … --phase guide` then refused:

> this deployment has no declared base; select source_commit

A pool that configures only a research worker has no deployment-wide declared base in `deployment.json` (it is `null` there, although the install inputs name one). `v12/QUICKSTART.md` says such a deployment needs a full `source_commit` in each assignment. The r2 phase documents did not carry one. This was the packet's error, not a product defect.

One product observation from the same transcript, recorded and not changed here: the packaged command printed a Python traceback for this refusal instead of a one-line `refused:` answer.

## The change

`phase_doc` now writes `source_commit: 76b2f2b2…` into both the `guide` and `overview` documents, and the launcher asserts that before use. It also asserts the condition itself: the installed deployment declares no base. Nothing else differs from r2; the packaged preflight before Docker and the packaging patch are unchanged.

## Rehearsal before this packet was returned (`rehearsal/`)

Run by K against a disposable instance at `/var/tmp/baton-k-w386295-pre`, using a copy of the bundle the second run built (`76b2f2b2` plus the packaging patch, commit `52e917f9…`, clean stamp) and a clone of its source. No engine, no manager process, no build. The worker was composed with a labelled placeholder image identity.

| Step, through the packaged executable | Result |
| --- | --- |
| deployment after installing the one research worker | `line_declared_base` is `null`, workers `["research"]` (`deployment-facts.json`) |
| `manager create --mode manual` | receipt for `field-survey` (`create.out`) |
| `add-phase guide` with the r2 document | refused with the same sentence as the field run (`add-guide-old.out`) |
| `add-phase guide` with the r3 document | receipt (`add-guide.out`); an exact repeat returns the same bytes |
| `add-phase overview` with the r3 document | receipt (`add-overview.out`); an exact repeat returns the same bytes |
| both phases afterwards, read through the product's read-only store API | `planned`, no selection instant, 0 ms charged, no execution Job exists (`unselected.json`) |

Not rehearsed: `start-phase`, the worker turn, restart, close and the three views. Those need the manager and a real container and are what the run is for.

## Rerun command

From `/home/sl/src/baton`, in a terminal:

```sh
bash work/records/2026/11/finding-v12-owner-paced-manual-jobs/evidence/field-76b2f2b2-r3/owner-run.sh --run
```

It makes a new `/var/tmp/baton-manual-field.*` root. The five typed choices and expected observations are those in `../field-76b2f2b2/README.md`. `owner-run.sh --check` passes (`CHECK.txt`).
