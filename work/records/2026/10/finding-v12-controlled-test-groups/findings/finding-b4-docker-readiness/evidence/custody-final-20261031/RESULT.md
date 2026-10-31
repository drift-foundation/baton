# Docker custody complete candidate — W384944 / E385016

M385013/review-2026-10-31T03-15-49Z.md implemented. Both affected cases pass,
then complete DockerCustody12/12 passes, zero failures/errors/skips. All11 existing
case IDs preserved plus one failed-removal exclusion regression. No product change.

## Exact changes and safety

Only `v12/python/tests/manager/test_custody_engine.py` changed. Candidate `2ac0806afb40faf5aeae1cec5dc9cdff3577d1d82dae065376a9482715b0f6e1`; accepted base `eb5f4d0fad72937440f2f8fab362895288aaa818a7c352276b8eefb4e3897897`.
Exact candidate/base/diff and1133-file selected source manifest retained. Shared target
matched accepted base immediately before transfer; five test overlays and accepted
cleanup product overlay retained. No moving K source, shared helper or product edits.

Existing positive case now proves real000 list/read denial non-destructively,
checks unchanged directory identity/mode and absence of standing removal ownership,
then performs real custody normalization, exact content readback and guarded deletion.
No pre-thaw or admitted destructive removal occurs before normalization.

Added test_failed_removal_ownership_excludes_custody_without_starting_a_helper keeps
the original failed-removal reproduction. OSError is observed to drive that path,
not declared as a new public error contract. The test requires one standing removal,
no completion operation record, precise custody ownership/no-completion refusal,
no helper run call and no derived helper object, unchanged workspace/directory and
unchanged ownership afterward. It never clears ownership or fabricates completion.
Fixture teardown disposes the test root afterward; that is not product recovery.

All prior hostile700/500/000 matrix, nested000 barrier, foreign-owner refusal/not_ours,
outside target/modes, stranger survival, stranded running/exited/restarted helper and
actual derived helper-lifetime assertions remain unchanged.

## Verification and provenance

Affected2/2: 0.716s body/0.964595s wall.
Whole12/12: 16.458s body/16.680154s wall.
Total focused command wall 17.644749s. Full IDs/subtest matrix in ledgers.json.
Both runs use the same candidate, exact selected historical snapshot and one offline
reference-worker build; source-before/after hashes unchanged. Full worker context,
installed pinned base ID, build command/log and exact artifact retained. Build
0.113614s, image sha256:755e3cea9e3cc07f3487ba2e8f35ce054a09bf286c61f6c2c9bfe6aceee0f8f9; --pull=false --network=none,
no second build, pull or live provider. Prepared interpreter and fresh disk roots,
actual workspace group membership/selected environment recorded. No timeouts.

33 exact containers across both runs (3 affected,
30 complete) captured using creation-time
Docker cidfiles, including --rm helpers; all confirmed absent afterward. Prior
container IDs preserved. Both fresh roots empty/removed; own image tag removed and
all pre-existing image IDs preserved. Exact cleanup output in resource-cleanup.json.
No unrelated cleanup/prune. Ordinary build/run caps1800s/600s plus120s cleanup reserve.

## Remaining inventory

All four historical custody errors now have passing coverage on the selected source.
Seven historical engine IDs remain (credentials1, adoption2, lifecycle2, negative
endings2), explicitly retained without rerun in remaining-historical-engine-ids.tsv.
Pure image/driver fixture items remain separate. Earlier accepted input-delivery56,
integration-worker83, initial-access4 and worker-entry5 evidence is preserved.
Independent review, remaining B4 work, joined current-source and full acceptance
remain due; this result is not overall B4 completion.
