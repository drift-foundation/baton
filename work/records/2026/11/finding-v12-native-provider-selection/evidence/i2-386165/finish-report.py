from pathlib import Path
import json, hashlib, re, subprocess, os
root=Path('/home/sl/src/baton');e=Path(__file__).resolve().parent;d=e.parent.parent;source=root/'work/scratch/i2-386165/source'
manifest=json.loads((e/'candidate-manifest.json').read_text()); final=json.loads((e/'final3.summary.json').read_text());baseline=json.loads((e/'baseline.summary.json').read_text())
assert set(final['nonpassing'])==set(baseline['nonpassing'])
assert not final['source_drift'] and not final['unaccounted'] and not final['duplicates'] and not final['timed_out']
pattern=r'^(FAIL: [^\n]+)\n-+\n(.*?)(?=\n=+\n|\n-+\nRan \d+|\Z)'
def failures(name):
 return [(a,b.strip()) for a,b in re.findall(pattern,(e/(name+'.stderr.log')).read_text(),re.S|re.M)]
old=failures('baseline');new=failures('final3');assert old==new,(old,new)
comparison={'baseline_failed_ids':baseline['nonpassing'],'final_failed_ids':final['nonpassing'],'failure_blocks':len(old),'failure_text_exactly_equal':old==new,'waived':False,'final_run_passed':False}
(e/'baseline-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
runs={p.name.removesuffix('.summary.json'):json.loads(p.read_text()) for p in e.glob('*.summary.json')}
seconds=sum(v['duration_seconds'] for v in runs.values());total={'runs':{k:{x:v[x] for x in ('collected','executed','passed','duration_seconds','exit_status','timed_out')} for k,v in sorted(runs.items())},'cumulative_seconds':seconds}
(e/'verification-account.json').write_text(json.dumps(total,indent=2)+'\n')
fixture=Path('/var/tmp/baton-i2-386165');children=sorted(p.name for p in fixture.iterdir());assert not children,children;fixture.rmdir()
check={'candidate':manifest['archive_sha256'],'paths':len(manifest['files']),'shared_targets_match_baseline':all(manifest['shared_target_matches_baseline'].values()),'prerequisites_match_retained':all(manifest['prerequisites_match_retained'].values()),'fixture_root_empty':not children,'fixture_root_removed':not fixture.exists(),'source_retained':str(source),'protected_git_mutations_selected':False,'engine_build_provider_real_credential_operations':False}
check['diff_check_exit_status']=subprocess.run(['git','diff','--check'],cwd=source,capture_output=True).returncode
assert check['diff_check_exit_status']==0
(e/'CHECK.json').write_text(json.dumps(check,indent=2)+'\n')
sha=manifest['archive_sha256'];count=len(manifest['files'])
report=f'''# W385830 I2 candidate — independent review

2026-11-25 UTC, baton.codxpc. Successful claim E386173 after routing/ownership
M386168–M386172. Incoming canonical discussion read through M386172; own progress
M386174/M386175. Base **2d9a1f5afd84bfdcef461798d2418be3e6d65a9d** contains both
required I1 and D1/D2 checkpoints. The earlier ownership-pending preflight is
historical; its source copy and baseline were reused, not repeated.

## Candidate and ownership

**sha256:{sha}**, **{count} paths**. `candidate.tar`,
`candidate-manifest.json` and `candidate.patch` retain exact reviewable bytes,
baseline hashes, member hashes and target-drift checks. All shared target bytes
still match baseline. Implementation is in the isolated independent repository
`work/scratch/i2-386165/source`; no product import or protected Git mutation.
The archive excludes DESIGN and all five W386057 isolation prerequisite paths.
The five prerequisites were used unchanged, retained separately and hashed in
the manifest. K/owner retains shared import/checkpoint ownership.

## Delivered behavior

- Production Codex realization from retained 0.169.0 evidence: HOME
  `/run/baton/provider-home`, CODEX_HOME `$HOME/codex`, `codex/auth.json`, managed
  `instructions/WORKER.md`. Closed environment, explicit instruction label,
  fresh implementation role, exact-build probe and R1 guards remain. No ambient
  configuration, source discovery or execution activation is added.
- Host first-initialization automatically resolves the configured source once.
  Explicit file-slot delivery uses exact bytes; the source resolver, volatile
  delivery/adoption, home seed/retained validation and qualification launcher
  enforce the same inclusive 1,048,576-byte bound. Empty files refuse. Legacy
  token handling/limits and Claude remain unchanged. Byte secrets enter the
  reference-counted durable-secret guard before file writes and leave only on
  confirmed cleanup. Tests use synthetic data only.
- D1 explicit `recover_failed_initialization` API: exact admitted manager/home/
  holder/path binding, exclusive home lock, durable failed-preparation proof
  with no runtime start and unchanged bounded metadata snapshot. Original receipt
  and withdrawal audit remain outside the mounted home. Concurrent/repeated
  withdrawal returns one audit. Separate retry authorization is required; the
  next initialization creates a new linked receipt. Missing credentials after
  success, changed home, old unsupported receipt, wrong binding or uncertain
  runtime retains the hold. Restart never needs the original source or silently
  reseeds. No conversation resume is implemented.
- Production-mapping simulated Codex implementation reaches independent Claude
  review through real owners. Codex remains labelled configured-model, actual
  participation unknown, contributors empty; Claude retains stronger participation
  evidence. The simulation also checks actual child environment, managed bytes
  and copied synthetic login file. It is not native/provider qualification.

## C5–C8 dispositions

| Follow-up | Disposition and limit |
| --- | --- |
| C5 | Contract refusal in image retention writes a content-free immutable refusal hold, then returns the lifecycle observation. A previously good receipt cannot mask failed contradictory retention, including after reopen. A globally unwritable control journal cannot persist lifecycle either; no promise to bypass broken authority storage. |
| C6 | Late engine resolution appends an immutable supplement bound to the original receipt. Both orders agree before assessment; absence never erases resolution. Frozen assessment/recovery bindings are never silently rewritten or upgraded. |
| C7 | One attempt has one start. Changed StartedAt, including a same-container restart, is conflicting execution evidence and keeps the hold. |
| C8 | Existing engine image-identity normalization accepts Podman bare hexadecimal IDs for exact-container observation and image resolution. Tags/malformed IDs still refuse; no profile-derived digest-kind assumption. |

Claude/legacy attempts acquire no image-receipt hold. All image evidence here is
synthetic engine output at the normal boundary. CLI identity remains
adapter-recorded/host-validated, not independently measured backend identity.

## Focused verification and accounting

Affected groups: **manager-pure, tools-pure, job_manager**. Prepared interpreter,
supported `just --justfile v12/justfile test-one`, external disk-backed fixture
root and unchanged isolation preflight. No new modules/registry changes.
`final-selection.json` names the exact selection. This is explicit ID accounting
around test-one, **not registry-accounted test-group/full-suite verification**.

Final run `final3`: **{final['collected']} collected / {final['executed']} executed /
{final['passed']} passed / 3 failing IDs**, {final['duration_seconds']:.6f}s, exit1.
No skips, duplicates, unaccounted/uncollected IDs, source drift or timeout.
**The run is not green.** All three failures and all five failure blocks exactly
match the retained pre-change baseline (`baseline-comparison.json`):

1. `tests.manager.test_secrets.EveryDurableWriterIsGuarded.test_every_durable_writer_is_covered`: six existing uncovered review_cycles writer/table pairs.
2. `tests.manager.test_secrets.EveryDurableWriterIsGuarded.test_no_declared_coverage_is_stale`: three stale freeze_checkpoint table declarations.
3. `tests.manager.test_secrets.EveryPublicSurfaceIsAccountedFor.test_every_exported_callable_is_in_exactly_one_class`: existing unclassified `retained_output_of`.

These are reported, not waived or removed. No additional failure remains.
The correction selection passed18/18 before final joined verification. Boundary
checks include below/at/above file limit, multibyte/invalid UTF-8/whitespace exact
bytes, empty and oversized retained files, secret-free refusals, legacy token
limits, failed initialization/no automatic retry, real owner start fencing,
concurrent withdrawal, separate retry/new receipt, foreign binding, unchanged
home verification, refreshed-source independence, production role/home pipeline,
image supplement/reopen/tamper and frozen-binding refusal.

All {len(runs)} retained runs (baseline included) total **{seconds:.6f}s** measured
wall time (`verification-account.json`). Intermediate implementation/fixture
mistakes are retained in their logs and corrected; the stale no-realization
expectations were replaced by approved mapping plus unknown-provider/role guards.
All raw logs, collected-ID lists, JSON outcomes, headers and before/after source
identities remain together. Fixture root was empty and removed; source and durable
candidate/evidence retained. `git diff --check` passed. No protected metadata
cleanup, build, container, real credential read or provider call occurred.

## Review and remaining finite route

Next milestone: **K independent exact-byte I2 review**, routine corrections
returned directly to the implementer; then owner import/checkpoint. Suggested
commit: `Realize Codex homes and audited subscription credential lifecycle`.
No unresolved owner decision blocks this source candidate.

Native-readiness plan remains `../native-readiness-386143/PLAN.md`: Q1 selected
coherent-image build/offline engine/mount/tool qualification; Q2 selected editing
turn capture; I3 only evidence-backed editing event support if needed; Q3 final
image qualification; Q4 explicitly selected Codex implementation → qualified
Claude review and retained verdict. Existing detached login/instruction evidence
is reused, not relabelled native. The recipe pins0.169.0 and includes Git/Python;
actual built tool availability, entrypoint/source/UID bindings and engine receipt
capture still require Q1. Explicit Claude model/source/qualification and execution
limits remain at the selected live boundary. Refresh/shared-login service safety
is unqualified; keep its finite separate criterion. Fast, resume, W386048 and
W386057 remain separate/unselected. No native activation is enabled by this report.
'''
(e/'REPORT.md').write_text(report)
entry=f'''\n\n## 2026-11-25 — I2 implementation complete for independent review (baton.codxpc, E386173)\n\nM386168/M386172 resolved the historical ownership gate; canonical claim E386173\nresumed the retained source from2d9a1f5a. [I2 report](evidence/i2-386165/REPORT.md):\n{count}-path candidate `sha256:{sha}`. Production mapping,\nautomatic exact-byte first copy, D1 audited withdrawal/separate retry and D2\n1MiB handling implemented; X1–X3 verified synthetically. C5–C8 dispositions are\nin the report. Actual Codex participation remains unknown; Claude requirements\nare preserved. No engine/build/real-credential/provider/native action.\n\nFinal focused selection: {final['collected']} collected/executed, {final['passed']} passed,\n3 pre-existing failing IDs (five failure blocks exactly equal to baseline),\nzero skips/unaccounted/drift; {final['duration_seconds']:.6f}s. Full selection is not\ngreen and no failures are waived. Total retained verification {seconds:.6f}s.\nAll shared candidate targets remain baseline; DESIGN and five isolation paths\nexcluded, prerequisites unchanged. Fixture root empty/removed; archive, manifest,\ndiff, logs and source identity retained. Next: K exact-byte independent review,\nroutine corrections directly; owner import/checkpoint after acceptance. Suggested\ncommit: `Realize Codex homes and audited subscription credential lifecycle`.\nRemaining selected-execution gates Q1–Q4 and editing I3 stay in the finite\n[native-readiness plan](evidence/native-readiness-386143/PLAN.md); W386048/W386057\nremain separate. No new owner decision requested.\n'''
for name in ('FINDING.md','PLAN.md','PROGRESS.md'):
 with (d/name).open('a') as f:f.write(entry)
print(json.dumps({'candidate':sha,'paths':count,'collected':final['collected'],'passed':final['passed'],'baseline_failures_only':True,'seconds_total':seconds,'report':str(e/'REPORT.md')}))
