# Docker custody partial correction — W384944 / E385008

Final11 existing case IDs executed:10 pass, one error, no failures/skips. The700/500/
000 subtest matrix passes; nested000 barriers pass. One before/after ownership-contract
conflict remains; no green-class/B4 acceptance claimed.

## Candidate and contract distinctions

Only `v12/python/tests/manager/test_custody_engine.py` changed; candidate `eb5f4d0fad72937440f2f8fab362895288aaa818a7c352276b8eefb4e3897897`, base `9dfa24b0a048aa48efa46cd661ee4c3ad8d38d9437a90e943a739faa933568ce`.
Exact base/candidate/diff and selected1133-file source manifest retained. Four prior
accepted test overlays and cleanup-only product overlay preserved. Shared target
matched base before same-file transfer; no shared/product/helper edits.

Test-local explicit immutable image selection avoids hidden builds. Worker fixtures
and stranded actual helpers use effective manager UID/configured workspace GID per
HOST-5. The same-prefix stranger deliberately retains65532 and no workspace mount.
A new actual65532-created foreign file at0400 proves manager chmod refusal; custody
reports not_ours and leaves its owner/mode unchanged. An outside0400 sentinel reached
by a workspace symlink retains content/mode. Existing input/workspace root modes and
confinement assertions remain. This is not a blanket numeric replacement.

The helper-lifetime case now checks the actual derived helper identity rather than
an unrelated random name and requires successful custody before absence. All original
case IDs remain. Before/after deletion case uses actual runtime-created nested000
access denial under shared UID instead of pretending0700 same-owner data is foreign.
It requires PermissionError13 before custody, unchanged inaccessible mode and a still
present workspace, then exact content readback and successful removal after custody.
The latter assertions remain required; they currently cannot be reached.

## Confirmed remaining conflict (M385009)

Initial discard_workspace raises PermissionError during its admitted removal attempt.
workspaces.py:4802-4806 explicitly retains removal ownership on any exception.
custody.py:2004-2012 then refuses _claim_episode because that ownership has no
completion. The test therefore cannot perform its normalize/after-removal half.
This intentional overlap guard must not be bypassed or silently cleared by a fixture.
The historical remove-first/normalize-next sequence conflicts with current ownership
semantics; this evidence does not alone establish which product behavior should change.
Coordinator/K must classify the supported recovery/pre-custody denial path and return
an accepted fixture sequence or reviewed product change while preserving both halves.
No shared edit, synthetic completion receipt, pre-thaw or skipped assertion made.
Exact reproducible trace: final/focused.log; same error preserved in first/focused.log.

## Verification and resources

First11:10 pass/1 error,15.755s body/15.979726s wall.
Final11:10 pass/1 same error,16.054s body/16.279500s wall.
Total focused wall 32.259225s. Final run adds
explicit foreign-owner/outside-target preservation and stronger helper absence proof.
The passing mode-matrix method establishes all three subtest iterations; exact custody
JSON accounts retained, all report actual1000:1001. No missing/duplicate top-level IDs.
Source hashes stable during each run; fresh disk roots empty/removed.

One selected offline reference-worker build 0.113589s, exit0; image
sha256:5fc457541dd86bdac4ad02595138c8872948fcbcc22256aeb5a4facbc03ecc27. Exact context/base/command/log retained; pinned base already installed,
--pull=false --network=none, no additional build/pull/live provider. Explicit image
reused for both focused iterations. Normal caps1800s build/600s run+120s cleanup.

Docker shim supplies a unique task label and --cidfile per run. Docker writes the exact
ID into that file at creation, before --rm can erase the object; the shim retains it
in engine.jsonl, then removes the temporary cidfile. Thus even foreground auto-removed
workers/helpers have exact IDs, without changing --rm semantics. All27 first-run and
28 final-run IDs confirmed absent, old container IDs preserved, fresh roots removed.
Own tag removed, all pre-existing image IDs preserved; resource-cleanup.json records
exact removals. No blanket pruning, historical cleanup or lingering task helper.

## Remaining inventory

Three of four historical custody failures now pass; the fourth has the specific
ownership conflict above. Eight historical engine IDs remain (custody1, credentials1,
adoption2, lifecycle2, negative endings2), retained in remaining-historical-engine-ids.tsv.
Pure image/driver items remain separate. Prior accepted56-case input-delivery join and
other accepted slices preserved; final current-tree/full acceptance remains pending.
