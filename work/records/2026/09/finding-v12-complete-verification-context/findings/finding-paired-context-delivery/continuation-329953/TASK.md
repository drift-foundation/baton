# W321776 paired verification views — isolated continuation

Private committed base `bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c`. The
read-only nominated source at `/input/source` carries this packet's exact input
buffers; they are **separate from the tracked base** and are not accepted
product. Do not transcribe, decode or retype any file content. From the private
checkout root run this short command exactly — it reads the mounted script,
verifies its digest, runs that same buffer, validates every base file, copies
five exact buffers and re-checks all five results:

```sh
python3 -c 'import hashlib,pathlib; p=pathlib.Path('"'"'/input/source/work/records/2026/09/finding-v12-complete-verification-context/findings/finding-paired-context-delivery/continuation-329953/restore.py'"'"'); b=p.read_bytes(); assert hashlib.sha256(b).hexdigest()=='"'"'4db9bfc9aed97cddb0425ace19cbb0364d20fbe2da66a8bc42e5486d272fb830'"'"'; exec(compile(b,str(p),'"'"'exec'"'"'),{'"'"'__name__'"'"':'"'"'__main__'"'"','"'"'__file__'"'"':str(p)})'
```

On an absent or mismatched input, or a base file that is not its declared
bytes, stop with the exact failure. No reconstruction from prose, from an older
blob or from any fallback, and no edit to anything mounted.

## What the restored checkpoint already is, and what it is NOT

The five restored files are the independently reviewed **Stage A** slice of this
Work (reviewer evidence `evidence/review-329794/`): the shared contract module
`v12/python/src/baton_v12/verification_context.py`, its 96 focused cases, and
the three files that carry it into the worker image (`Dockerfile.claude`, the
`.dockerignore` allowlist re-include, and the travel/allowlist cases in
`tests/manager/test_claude_agent.py`). They are **preserved input, not an
accepted base**, and the two view materializers are **not** delivered by them.
`v12/worker/claude_agent.py` and `v12/python/tools/dogfood_operator.py` are
untouched at the base, so no holder reads a `/3` task yet.

Read the governing packet in the mounted source before editing:
`work/records/2026/09/finding-v12-complete-verification-context/findings/finding-context-packet/`
— `PACKET.md` (the eight-stage lifecycle trace and the layout), `CONTEXT-CONTRACTS.md`
(the `/3` definition and the closed member sets), `VERIFICATION.md` (VER-1..5
and the negatives), `TASK-INSTRUCTIONS.md`. Read `v12/DESIGN.md` VER-1..VER-5
and ART-3.

## The milestone, and it is exactly these five things

1. **Stage 6 — the worker's fresh disposable view.** `claude_agent._verify`
   today runs "the task's OWN command, in the candidate copy", and for a line
   profile the candidate *is* the retained worktree, which VER-3 forbids. Build
   a view the worker owns: the candidate's own bytes with the measured
   `changed_paths` applied and every `removed` path absent, each sealed input
   materialized **by `name`** at its view-relative destination and verified
   against `content_digest`, the view the only thing this step may delete, and
   the retained candidate and every sealed input byte-unchanged on success, on
   test failure, on timeout, on a failed start and on a partial
   materialization.
2. **Stage 8 — the operator's fresh disposable view**, from the retained output
   only: the accepted-base object source (the deployment's own retained
   repository, advanced solely by `tools/accepted_base.py`), the
   `objects.bundle` for `base..HEAD` resolving the published `head`, and the
   same seal. No fallback to an ambient host checkout, and no inference that a
   digest supplies a missing object.
3. **Stage B — view preflight in BOTH views**, with the causes the packet
   assigns: absent `working_directory` or `import_root` → `invalid-layout`;
   absent `required_path` → `missing-input`; input bytes, pins, reported
   changed and reported removed → `materialization`; `git-line` ancestry →
   `invalid-layout`; a base missing from the object source → `missing-input`;
   an unsatisfied bundle prerequisite or a transport resolving another head →
   `materialization`. The base is never checked out into a view.
4. **`/3` accepted at both holders** — `claude_agent.py` (`TASK_SCHEMA`, the
   closed equality at :117) and `tools/dogfood_operator.py` (`_TASK_SCHEMA` at
   :768) — using the restored module's own `generation()` rather than a second
   copy of the rule: a `/2` document carrying `verification_context` is refused
   and a `/3` document lacking it is refused. **`/2` MUST REMAIN STAGEABLE.**
   The envelope that launched this very turn is `/2`; a change that accepted
   only `/3` would refuse its own launch.
5. **`baton.dogfood-proposal/3` and `baton.dogfood-operator-evidence/1`**
   emitted with the members `CONTEXT-CONTRACTS.md` closes, including
   `result_digest`, `result_head` and `transport` bound to the retained output,
   and the generic-candidate case where head and transport are null.

## Where the new tests go, because the gate names them

The verification argv is sealed and cannot name classes that do not exist yet,
so the module names are the convention and they are part of the contract:

| new module | what it must cover |
| --- | --- |
| `v12/python/tests/manager/test_verification_views.py` | the worker view (stage 6) and Stage B in it, including every refusal cause above and the preservation/cleanup outcomes |
| `v12/python/tests/tools/test_operator_verification_view.py` | the operator view (stage 8), its object-source and bundle prerequisites, and Stage B in it |

Extend `tests/manager/test_claude_agent.py` and `tests/tools/test_dogfood_operator.py`
for the `/3` acceptance and refusal direction at each holder. Do not weaken,
delete or loosen any existing case, and do not edit
`tests/manager/test_verification_context.py` or
`src/baton_v12/verification_context.py` except where a named reviewed defect
requires it — they are the reviewed input, and a silent rewrite of them is a
rewrite of the contract both views must agree on.

## Boundaries

- No edit to anything under `/input`; the mount is read-only on purpose.
- No image build and no container inside this task. The module's travel into
  the image is already delivered and is covered by the recipe cases.
- No broad suite sweep. Run the focused checks for the behaviour you changed,
  and stop once the sealed verification argv passes.
- `tests.manager.test_dependencies` fails at this base for reasons that predate
  this Work (operand declarations plus a sweep that finds build output under a
  git-ignored `v12/python/build/`). Do not "fix" it here and do not report it
  as this candidate's.
- **W325695** owns the verifier-descriptor-in-descendant-processes defect and
  touches worker and test paths. Do not redesign the verification environment,
  do not alter `TMPDIR` to force a green run, and do not label an environmental
  failure as formal success. If the descriptor defect blocks verification,
  report it honestly and preserve the candidate.
- No host product edit outside the private checkout, no integration, no
  self-acceptance, no deployment, no mutating version-control operation beyond
  what the line profile itself performs, and no edit to historical evidence.
- Independent review and the human checkpoint remain required. A retained
  candidate is not an accepted one.

Report honestly if the milestone is only partly reached: a preserved partial
candidate with an exact account of what is missing is worth more than a green
claim. State cumulative verification spending.
