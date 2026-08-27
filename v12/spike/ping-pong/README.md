# SPIKE ONLY — the first v12 Docker ping-pong trials

**Nothing in this directory is a v12 contract, a production component, or
conformance evidence.** W17110's ruling says so in terms, and it says it twice:
the trials "may use provider-specific spike images, native CLIs, ACP adapters or
small temporary drivers", and "W6633, W6634 and W6636 later decide what to reuse
and must not silently promote the spike as production implementation or
conformance evidence".

So this is deliberately not built out of `v12/python/src/baton_v12`. It shares
no module with the Worker Manager, imports nothing from it, and answers a
different question.

## The question

Can a **real** Claude agent runtime, and then a **real** Codex agent runtime, be
packaged into Docker and complete the smallest possible assignment — receive a
correlated `ping`, return the correlated `pong` — with credentials supplied at
runtime from an operator-controlled read-only provider, and with the container
cleaned up afterwards?

A scripted echo worker cannot answer that. That is why the earlier
deterministic-worker boundary was superseded.

## What the outer shape holds, and it is the same for both providers

That sameness is the point: it is what makes the two trials comparable at the
wrapper boundary, which is what the ruling asks the experiment to compare.

- a spike-only image per provider, named `baton-w17110-spike-*`;
- staged input mounted **read-only** at `/input`, carrying one correlation
  identity;
- a separate **writable** `/output`;
- the credential provider mounted **read-only**, from a path the operator
  nominates — never copied into an image, a repository, a result, an evidence
  file or a log;
- `output.json` written **last**, so its presence under its final name is the
  completion signal;
- host-side validation that the `pong` carries the same correlation identity;
- and positive cleanup, proved by asking the engine rather than by remembering.

## Credentials

`preflight.py` reports whether a provider is present and **never reads one**.
Every evidence line about credentials names the provider and the method; a
failure is recorded as a redacted category.

If authentication fails, the trial records the exact redacted boundary failure.
It does not move the agent onto the host and call that a success — the ruling
forbids exactly that, and it is the one shortcut that would make the whole
experiment worthless.
