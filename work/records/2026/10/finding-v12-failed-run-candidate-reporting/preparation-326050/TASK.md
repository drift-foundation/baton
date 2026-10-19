# W321528 exact-file continuation

Private committed base 03b94fc80744671150cca1997712ee95a6537df5. Existing read-only nominated source at
/input/source carries retained input files; they are separate from tracked base.
Do not transcribe or decode patch text. From private checkout root run this short
command exactly; it reads the mounted script, verifies its digest, runs that same
buffer, validates base files, copies five exact file buffers and checks all5 results.
On absent/mismatched input or base, stop with exact failure; no reconstruction
from prose, old blobs or fallback. Do not edit any mounted source.

```sh
python3 -c 'import hashlib,pathlib; p=pathlib.Path('"'"'/input/source/work/records/2026/10/finding-v12-failed-run-candidate-reporting/preparation-326050/restore.py'"'"'); b=p.read_bytes(); assert hashlib.sha256(b).hexdigest()=='"'"'1a258a9317d6a0633aad63dd90951a6e0454360e476d7e4cb5bc8efac5d803c5'"'"'; exec(compile(b,str(p),'"'"'exec'"'"'),{'"'"'__name__'"'"':'"'"'__main__'"'"','"'"'__file__'"'"':str(p)})'
```

# Bounded continuation checkpoint — claim325711

Continue exact retained0addd2afca3c4ebe3a4cec9f2936791f58a6591d; do not restart.
Required correction: baseline.py _retained_bytes uses os.path.isdir(place), which
suppresses PermissionError from an inaccessible ancestor and falsely reports no
retained tree. Use real filesystem permission-denial regression, preserving valid
custody, actual missing/non-directory/damaged/substituted versus unreadable evidence,
locator, assignment, exact task id/digest/argv, unreported/no-status, unobserved
acceptance, effective provider timeout and cleanup uncertainty. Do not weaken checks.
Reviewer real uid1000 probe: valid artifact -> chmod its parent0 -> os.stat EACCES13
but collector state refused/claims absent. Restore permissions in finally. Cover
ancestor as well as root/file denial; do not silently treat privileged bypass as proof.

Prior provider status0; formal verification1. Exact186 focused tests independently
pass7.688s outside worker. Descriptor TMPDIR independently reproduces40 failures/
20 errors7.145s: child subprocess closes inherited descriptor and nested adapter
rejects alias. W325695 owns this separate environment defect. Do not redesign
verification environment, remove credential/anti-substitution guards, alter TMPDIR
to force formal green, or label independent evidence as worker formal success.
Keep full diagnostics in owning evidence/review-325674; no raw native logs in task.

Milestone: only unreadable-versus-missing collector correction plus necessary
regression tests. Deterministic focused checks: test_candidates, test_baseline and
five selected worker classes in the packet verification argv. Existing186-pass
observation is prior evidence, not proof of new candidate. Run focused checks for
changed behavior, stop once required checks pass; report environmental failure
honestly and preserve candidate even if formal verification fails. No broader
suite, live provider/authentication probes or Docker inside task.

Read v12/DESIGN.md REC-1 ART-7 OBS-2 DB-1/DB-4; public store boundaries, no filesystem
I/O inside transactions. Preserve W324214 visibility and W321776 task /3 ownership.
No host product edits, integration, self-acceptance or historical evidence mutation.
Independent review and human checkpoint remain required. Adapter owns publication.

Latest run325711 is spent: provider1/api-error with native refusal after11 turns,
no restored source or verification. Earlier encoded-input transcription failed.
Preserve refusal without bypass; this packet fixes byte transport only through
existing nominated-source mount. Prior0add remains the input, not accepted product.
