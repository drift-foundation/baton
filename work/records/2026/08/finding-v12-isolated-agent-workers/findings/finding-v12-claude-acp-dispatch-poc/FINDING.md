# Finding: disposable Claude ACP natural-dispatch proof

## Status

Confirmed proof-of-concept Work `W76` (`5f717eee-W76`), contained by v12
roadmap Work `W2`. Implementation has not started. The implementer may claim
only after the parent decisions and this complete handoff are committed and the
Baton repository reports a clean baseline.

This Work proves or disproves one thin vertical slice. It is not production v12
implementation and creates no compatibility promise.

## Question to answer

Can an operator submit and route an ordinary Baton Job, then have a trusted
prototype Worker Manager naturally dispatch it to one isolated Claude ACP
worker, obtain the explicit claim, materialize typed input, collect declared
output, and return the Job for review without manually launching or prompting
Claude for that Job?

Success means the complete Baton-to-manager-to-worker-to-manager-to-Baton
lifecycle works and is observable. Merely proving that Claude runs in Docker or
answers an ACP prompt is not success.

## Isolation and source ownership

Prototype source lives in a separate disposable root, initially
`/home/sl/src/baton-v12-poc`, with its own dependencies, tests, fixtures, draft
manifests, worker image and runtime state. The operator establishes its clean
source-control baseline; agents do not initialize, stage or commit it.

No prototype implementation may modify existing Baton application, bridge,
lifecycle, test, recipe, release-template or deployment files. Within the
Baton repository the implementer owns only this child's `PROGRESS.md` and
explicitly requested evidence files. Discovery is reported through the normal
W76 discussion and draft evidence; it does not justify opportunistic fixes to
v11.

The prototype may snapshot or copy any useful material from Baton release
commit `8835cd5` into its external root and modify the copy without limit.
Copied material records its original repository-relative path and commit in a
small provenance manifest. Runtime imports, symlinks or writes back into
`/home/sl/src/baton` are forbidden. Reuse is encouraged; coupling the
prototype to a mutable live checkout is not.

The immutable deployed executable
`/home/sl/opt/baton/v11/8835cd5/bin/baton` may be invoked only as a black-box
documented CLI/JSON client against a disposable authority. Neither the model
nor prototype opens SQLite directly. The production coordination home and
managed services remain untouched.

## Deliberately narrow first slice

- One model and participant: Claude through ACP.
- One local OCI runtime: Docker is installed on the host; Podman parity is not
  required by this Work.
- JSON contracts and CLI operation only. No TUI work.
- One disposable authority and harmless fixture Job.
- One typed `directory` input and one declared `directory` result.
- One happy path plus the minimum negative claim-fencing proof.
- No Git proposal, integration, Gemini, Codex, SSH, fan-out, production
  credential, cache, retention or signing implementation.

## Natural dispatch scenario

1. A test operator starts the prototype manager and submits an ordinary Job
   through CLI/JSON to the disposable authority. The Job is routed to the
   prototype Claude participant; no Claude process is launched manually for
   that individual Job.
2. The manager observes the actionable Job through the public Baton boundary,
   creates a runtime attempt and issues a short-lived single-use claim token.
3. A read-only pre-claim Claude ACP turn receives the human contract, typed
   input metadata and token. It may accept or decline but has no execution or
   publication capability.
4. Claude returns a structured token-bearing claim intent. The manager
   validates it and submits the canonical atomic claim. Only success mints the
   prototype assignment generation and permits the isolated execution worker
   to start.
5. The bootstrap materializes and verifies a digest-bound read-only directory
   input at a stable path and exposes a separate declared writable output path.
   Claude receives no Baton executable/config/database and no external output
   destination.
6. Claude performs a deterministic, reviewable transformation, emits at least
   one meaningful activity update, and declares completion with the named
   result.
7. The manager fences further writes, freezes the output, validates containment
   and the expected shape, computes the input/output manifests and digests, and
   binds the trace to Work, participant, runtime attempt and assignment
   generation.
8. The manager returns the Job through the public Baton boundary with a concise
   recap and result references. The operator can inspect the authoritative
   claim/handoff plus the prototype trace without reconstructing hidden state.

The fixture transformation should be simple enough to verify independently,
for example producing a deterministic JSON index of supplied text files and
their first headings. Its purpose is lifecycle proof, not model evaluation.

## Minimum negative proof

An expired or replayed pre-claim token must fail closed. The manager commits no
claim, starts no writable execution worker, accepts no result, and leaves the
Job safely available for a fresh offer. A status claim such as "working" or a
successful ACP response without the valid token grants nothing.

## Required evidence

- Exact prerequisite and launch commands with secrets removed.
- Versioned draft IN/OUT and control envelopes.
- A machine-readable chronological trace covering offer, token, claim intent,
  canonical claim, worker start, materialization, activity, completion,
  freeze/validation, collection and return.
- Disposable-authority CLI/JSON snapshots proving the Handler before and after
  claim and after return.
- Input and output manifests/digests plus an independent expected-result check.
- Expired/replayed-token negative trace.
- Container identity and termination/quiescence evidence.
- Provenance manifest for copied v11 material.
- A concise list of contract assumptions that held, failed or require revision.

Evidence must not contain credentials, auth tokens, environment secrets or a
copy of the production authority.

## Acceptance

The Work is ready for independent review only when:

1. the Baton repository contains no prototype product-source edits;
2. the external prototype is independently inspectable from a clean baseline;
3. an ordinary CLI/JSON Job naturally wakes Claude without a per-Job manual
   launch or prompt;
4. the manager alone accesses Baton authority and the canonical claim precedes
   all writable execution;
5. typed input is verified and immutable, output is separate, declared,
   frozen, validated and digest-bound;
6. the expired/replayed-token case starts no execution and publishes nothing;
7. the Job returns for review with sufficient public state and trace evidence;
8. rerunning the fixture from a fresh disposable authority produces the same
   lifecycle result; and
9. `PROGRESS.md` gives an explicit go, revise, or no-go recommendation without
   representing prototype code as adopted Baton code.

## Stop conditions

Stop and return `needs-help` rather than widening scope if the proof requires a
change to existing Baton source, direct SQLite access, a production mailbox,
manual per-Job prompting, TUI implementation, embedded long-lived credentials,
or weakening the claim-before-execution boundary. File separately any actual
v11 defect encountered; do not repair it inside this Work.
