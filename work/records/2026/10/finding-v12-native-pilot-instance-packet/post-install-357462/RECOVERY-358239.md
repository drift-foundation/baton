# The recovery question, answered: the capability is ABSENT

`review-2026-10-23T04-08-43Z.md` required the next bounded preparation to
*"identify a supported fresh review/checkpoint adoption path preserving this
exact implementation result, or explicitly report that capability absent."*

**It is absent.** Reported rather than worked around, and no operation is
invented.

## Why the same Job cannot be re-reviewed

`outputs` is part of the Job's input identity. `contracts/manifest.py:659`
lists it directly: *"`human_contract`, `sources`, `outputs`, `record_binding`,
`role_instructions_digest`, `policy_digest` and the resource, network, mount,
tool and retention policy digests **are the Job's input**, and a worker that
moved one of them is still refused."*

So the corrected shared contract — which it must be, because the delivered
proposal-only declaration refuses the review adapter before any provider call —
produces a **different `job_input_identity`**. The accepted Job
`quickstart-b` / `sub-w321608-quickstart-2` was admitted against the old
identity. Editing the delivered `inputs/input.json` in place and rerunning the
review would be presenting changed Job input under an unchanged admission, and
the manifest check exists precisely to refuse that.

## Why no adoption path exists either

Searched the reviewed build for an operation that would carry the completed
implementation result into a new Job's review stage:

- **No `adopt`, `adopt_checkpoint`, `retry_review` or `rereview`** function
  exists in `tools/` or `src/baton_v12/job_manager/`.
- **No `freeze_checkpoint` surface** in `tools/stage_execution.py` that takes a
  prior Job's retained result as a new Job's implementation input. The word
  "adopt" appears there only about a *live* attempt adopting its own exchange
  delivery (`:1488`) and about receipt adoption within one Job (`:706`).
- The installed manager CLI exposes **`submit`, `status`, `serve`** — the
  review confirmed this from the bundle's own help. There is no generic
  review-retry verb, and I did not invent one or touch store state.

## What this means, stated without softening

A new Job carrying the corrected contract would run its **implementation stage
again**. The completed implementation result — `objects.bundle`,
`change.patch`, `result.json`, `verification.txt`, confirmed still readable by
the reviewer's `RETENTION.json` — would be **retained as evidence but not
consumed**. There is no supported way to spend it.

So the owner's choice is between:

1. **A fresh Job with the corrected contract**, accepting that the
   implementation turn is repeated and the retained result becomes history
   rather than input. The repeated turn is a real provider cost and a second
   non-identical result, not a re-run of the same one.
2. **Establishing the missing capability first** — a supported operation that
   adopts a retained implementation result as a new Job's implementation input
   under a corrected output contract. That is **product work with its own
   bounded Work, dependencies and acceptance**, and the review is explicit that
   it must be separated only after bounded research establishes it. This
   document is that research, and it finds the capability absent.

**Neither is selected here**, and no execution, cleanup, resubmission or
deployment change is proposed. The failed review attempt's evidence, the
completed implementation custody, and the current token and cleanup facts are
all left intact.

## What is corrected offline, and what it does not do

`configure.py` now composes the shared union contract and the proof exercises
both role adapters — see `INDEX.json` and `evidence/PROVE.json`. That makes the
packet **executable for a future Job**. It does **not** recover the failed
review, and does not claim to.
