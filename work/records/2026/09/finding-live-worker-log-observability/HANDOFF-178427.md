# W61599 bounded correction — tuner claim178427

Owner178421 selected correction of review-2026-09-15T13-39-06Z.md. The three
source corrections and test-provenance reconciliation are complete. Return
baton.feat for focused independent review, then baton.ops. No automatic further
implementation cycle; no candidate acceptance or shared-file release asserted.

## Candidate and provenance

All locators below are relative to this canonical dossier under
baton:work/records/2026/09/finding-live-worker-log-observability/.

- correction-178427/candidate.json SHA256 `acabca2d229f984a647626d6feb5244d4d1d0bea95c80b025f802ca9194138b3`
- correction-178427/correction.patch SHA256 `611cae6e173faad87330c268c3d9af1c8c9c81740c3f1e83ab2aaf69c0dfa480`
- correction-178427/verification.json SHA256 `594b052470d75d3d92358283cdce814723192825aad94e28b990d3ccff318b3b`
- correction-178427/author-reconciliation.json SHA256 `4c24794d42f71783bb7a30c0dff8cd73b877aa5dc082da68de905c00798e30ce`

The manifest binds immutable base and candidate snapshots, SHA256 and repository
modes for all12 source/test paths in the original handoff. The base is the exact
current state recorded by review178362, verified before edits, and is explicitly
not a previously accepted candidate. The patch changes exactly three source and
three test files; the other six paths are retained unchanged. No Git mutation.
Custody snapshots are0444; repository file modes stay at their recorded values.

The two mismatched original test hashes are reconciled, not guessed. Author
M178528 supplied /tmp/w61599-cand snapshots. I independently verified both full
submitted hashes, copied them into correction-178427/submitted-177898/, and
compared them with the saved correction base. The resulting two
*.author-reconciliation.patch files show exactly the six edits the author names:
truncation-resumption and meaningful entry-overflow coverage; positive/unknown
values, direct decoder coverage, the publisher helper and transient-observer
recovery. They were the author's edits after computing his handoff hash list.
The subsequent78cf8083/63e12bd4 test hashes he noticed belong to this correction.
Older suite/reversal results are never rebound to the new candidate.

## Correction and changed expectations

| Changed path | Correction / verification |
| --- | --- |
| v12/worker/claude_agent.py | Descriptor-relative native metadata traversal. Every root component rejects links; children open relative to a held directory with O_DIRECTORY/O_NOFOLLOW and compare opened dev/inode with checked entry. Recursive depth and all existing entry/file/count limits remain. No native file content is opened; scan descriptors close on every exit. |
| v12/worker/baton_worker.py | Publisher stop retains the thread reference. Repeated bounded joins remain false while it is live and become true only after observed exit. |
| v12/python/tools/single_worker.py | Enqueue uses only an in-memory path join. Necessary realpath resolution moves to _ingest on the helper thread. Ingestion stop also retains its thread handle, preserving truthful repeated release and same-store exclusion. |
| v12/python/tests/manager/test_claude_agent.py | Adds root-link replacement, child replacement after acquisition, and link/ordinary-directory replacement between stat and open. Checks no foreign9000-byte count and descriptor closure at failed acquisition. |
| v12/python/tests/manager/test_exchange.py | Strengthens blocked publisher stop to require repeated false results while blocked, then an actual join and positive stop after release; always cleans up the captured thread even on failure. |
| v12/python/tests/tools/test_single_worker.py | Tests repeated helper timeout with retained handle/slot and same-thread store close, zero diagnostic realpath/lstat calls during actual refresh, blocked resolver with usable enqueue/manager reads, and correct blocker-release/join order in existing fixtures. |

Standing test-change authority supplies the scoped expectation changes. No
existing defect coverage is removed. The initial test interception was too wide:
ordinary runtime refresh legitimately resolves its workspace; the corrected test
intercepts only the added diagnostic hook while driving the full refresh.

The new scanner replaces the old claim that directory-entry no-follow checks
alone prevent redirection. A missing/inaccessible root now freezes the optional
observation conservatively rather than treating it as a temporarily empty scan.
A child renamed after descriptor acquisition may still contribute its own7 bytes;
it never follows the replacement target. Directory acquisition and all metadata
I/O remain entirely on the publisher thread. Fresh-home admission performs no
scan/stat, and injected/reused/restored HOME remains unknown.

## Focused verification and cleanup

correction-178427/focused-final.log and focused-final.json bind the final bytes:
**82 tests pass**, zero failures/errors and no remaining test threads.
Supervisor duration **7.225550314993598s**, process group positively absent.
The seven explicit classes cover native observation, activity wire/parser,
worker publisher, store-level admission, ingestion and both composition closers.
No discovery/full suite, live provider/model, actual engine or container run.

The retained negative-2 run executes the three exact base product modules in
memory while retaining the test runner's normal imports; it never swaps source
files in the working tree. Five controls reproduce the reported defects: root
and queued-directory replacement both count foreign9000 bytes, each repeated
stop returns true while blocked, and enqueue calls realpath. Six methods fail
(seven subtest failures), but the additional acquisition-boundary subcases are
**not separate baseline race reproductions**: the old walker has no os.open seam
for that injection. Their final passing run proves the new boundary was reached
and rejected both substitution types. negative-2-binding.json records that
qualification and retains the exact tested test_single_worker bytes by hash.

All five supervised invocations, including setup mistakes, are preserved:
regressions-1 (one overbroad test interceptor failure), negative-1 (runner import
setup failure, no tests), negative-2 (expected failures), focused-1 (81 pass), and
focused-final (82 pass after explicit blocked-resolver coverage). Total new
measured supervisor time **17.160464063985273s**. Every process group was absent
at completion; no termination was required. Test cleanups positively join the
controlled blockers, including negative cases. git diff --check passes.

Python3.13.7 used ambient jsonschema4.19.2, referencing0.36.2,
jsonschema-specifications2023.12.1, attrs25.3.0 and rpds-py0.21.0. These versions
are recorded in each receipt. This is focused source verification, not locked
packaging certification. Reproduction uses the retained run-focused.py and
supervise.py scripts with the named modes and explicit180s per-run bound.

Prior author spending remains approximately2966s including approximately190s
estimated focused/probe time; prior review178362 added0s runtime. The author's
baseline89/candidate88 aggregate claims remain attributed and unaccepted here.
M178528 supplied five existing logs, now retained byte-for-byte under
correction-178427/author-177898-logs/ with author-log-inventory.json. They were
copied and hashed only: no broad comparison or historical reconstruction ran.
The mid-implementation full log remains author-designated non-evidence.

For historical resources, M178528 reports all original foreground tests ended
before pass178359 and a fresh no-unittest process check, with no background
runner/provider/engine/container. That is explicitly author testimony. My
before/after ps snapshots have sandbox visibility only; my positive process-group
and thread receipts apply to this correction's own runs.

## Remaining ownership and release boundary

Independent review and owner disposition remain. W161234 receives no shared-file
release until independently accepted final bytes and explicit ownership handoff.
W167896 still owns historical-after-terminal viewer follow-through; no visible
count delivery is asserted. Receipt timestamps may be delayed after completion
without liveness authority. Rich follow/sink/color/pause/search/filter/retention
work remains W39649/v13. Baseline repair remains deferred W165786. No attempts
owner, lifecycle schema, viewer, deployment configuration or unrelated source is
changed by this correction.
