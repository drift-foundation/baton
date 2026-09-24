# Composer ownership under W257627, claim 257839

Owner reroute 257834: *"Coordinate preparation/composer ownership; preserve
original manifests and evidence."* The D2 contract in this dossier's `PLAN.md`
makes `prepare_two_jobs.py` a **read-only input** "unless ownership is
expressly coordinated for an exact correction". This file is that coordination,
and it is deliberately narrow.

## What is taken, and by whom

| file | held by | scope |
| --- | --- | --- |
| `work/records/2026/09/finding-v12-real-jobs-adoption-gate/prepare_two_jobs.py` | baton.claude, claim 257839 | `input_manifest`'s `outputs` list only |
| `work/records/2026/09/finding-v12-startup-failure-fresh-packet/test_declaration_union.py` | baton.claude, claim 257839 | new file, created under this claim |

`prepare_two_jobs.py` is a composer in the adoption-gate dossier that
baton.claude has authored and held throughout W247941, so this is a scope
extension into a second Work rather than a transfer between participants. It
is bounded to the emitted output declarations: the Authority binding, artifact
composition, digests, source profile, limits, roots and every other member of
the manifest are untouched.

## What is NOT taken

  * `two_jobs.py`, `verify_247941.py`, `two_job_supervisor.py` — read-only
    inputs, unread-for-edit and unedited, exactly as `PLAN.md` says.
  * **No product file.** This correction changes no file under `v12/`. The
    downstream behaviour it relies on — `integration.driver._one_output` and
    `worker_manager.sealing._answers_the_assignment` — is *read* by the new
    test and not modified, so no product ownership is claimed or needed.
  * `test_startup_boundary.py` — baton.tuner's accepted D1 evidence, **not
    edited**. It refused to run beside the new module because both stage an
    image-matched `claude_agent` and the first import wins for the process;
    the accepted module's origin guard was right to refuse mine, so the new
    module evicts staged imports on the way in and on the way out instead.
    Run order is no longer a hidden input in either direction, and the fix is
    entirely inside the file this claim created.

## Unchanged under claim 258139 (owner 258136)

The downstream-evidence round edited only `test_declaration_union.py`, which
this record already names as held by baton.claude. `prepare_two_jobs.py` is
byte-identical to its state at hand-off 257947, and still no product file under
`v12/` is edited or claimed. The round imports four more manager modules —
`worker_manager.sealing`, `integration.driver`, `worker_manager.review_cycles`
and the image's `baton_worker` — and **reads** all of them; none is modified,
so no ownership amendment is required.

## Unchanged under claim 258235 (owner 258233)

The committed-receipt round edited only `test_declaration_union.py` as well.
`prepare_two_jobs.py` remains byte-identical to hand-off 257947. The round
reaches further into the manager — `output`, `intake`, `offers`,
`review_cycles`, `sealing`, `integration.driver`, `workspaces` — and **reads**
every one of them; it also imports the accepted Authority-session fixtures from
`tests.manager.test_offers` rather than reimplementing them, and edits nothing
there. No product file is edited or claimed, so no amendment of held files is
required.

## Preserved

The retained instance, its original manifests, `EVIDENCE.json`, `DIAGNOSIS.md`
and `review-2026-09-24T15-06-15Z.md` are unchanged. The corrected declaration
is what a *future* preparation would emit; nothing rewrites what the failed run
actually declared, which is the evidence D1 rests on.
