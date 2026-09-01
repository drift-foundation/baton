# run6 — the control that exonerates the rebuilt image

`baton.claude`, implementer, 2026-08-31.

`attempt-w51487-run5` came back `provider-failed`, status 1, empty patch, with
a candidate byte-identical to the delivery — the run2/run3 shape, not run4's.
Exactly one input had changed since run4 succeeded: the worker image, rebuilt
from the current tree as the standing handoff requires. So the image was the
first suspect and it is the one input a second attempt can hold fixed.

`attempt-w51487-run6` is that control. Everything is fresh — authority
`21dce6fa603a4f1a942f9dec68e5bd03`, Work `21dce6fa-W51487`, offer, attempt,
runtime, incarnation, control store, launch home, storage, credential home and
staged source — and the ONE difference from run5 is the nominated image:

    run5   sha256:8af96742a89489ae974943284fcc65a5fd58e02263a9ae2142b3d0afa4f9c0e6   rebuilt now
    run6   sha256:b471399a7dcb8300795fe884c471b817ec1d61644130d66ec12fbd4fef76c003   run4's exact artefact

## Result: identical failure

|  | run4 | run5 | run6 |
| --- | --- | --- | --- |
| disposition | `verification-failed` (provider ran) | `provider-failed` | `provider-failed` |
| provider status | 0 | 1 | 1 |
| `changed_paths` | `["…/test_harness.py"]` | `[]` | `[]` |
| custody content digest | `sha256:195a0049…` | `sha256:e002024b…` | `sha256:e002024b…` |

`sha256:e002024b…` is the same custody digest run2 and run3 produced: an
untouched four-file candidate, a zero-byte patch and `no verification was
attempted`.

**The rebuilt image is not the cause.** run4's own artefact, replayed 50
minutes later under fresh identities, fails exactly as the new one does.

## What the rebuild did and did not change

Two builds of the same recipe from the same unchanged `v12/worker` tree do not
reach one digest, and the layer comparison says precisely why:

    layers 0-4   node:22-bookworm-slim         SAME
    layer  5     npm install claude-code@2.1.247   DIFF
    layer  6     apt-get ca-certificates python3   DIFF
    layers 7-10  COPY baton_worker.py, claude_agent.py,
                 dogfood_entry.py, worker-control-1.0.schema.json   SAME
    layer  11    useradd nonroot                SAME

The repository's own code layers — including W52800's corrected
`claude_agent.py` — travel into both artefacts byte for byte. What differs is
the two layers whose content is fetched from the network at build time: the
`FROM` tag is not pinned by digest, `apt-get install` takes whatever the Debian
mirror serves today, and the pinned `@anthropic-ai/claude-code@2.1.247` runs a
`postinstall` that fetches its own native binary. Both images report
`claude --version` as `2.1.247 (Claude Code)`.

That is a real reproducibility limit of this recipe and it is worth its own
Work, but it is NOT this blocker: run6 removes it from the causal chain.
