"""Claim-250733: the operands become a preparation step, not questions."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250733

Owner reroute 250730 selected a fresh isolated two-Job proof instance and asked
for complete operator preparation: derive the technical operands from accepted
configuration and supported APIs instead of leaving them as owner questions,
and deliver exact setup commands plus a preparation script.

## Done under claim 250733

  * **`prepare_two_jobs.py`** — one command that refuses a run root that is
    not this run's own or lies under a consumed instance; writes both Jobs'
    task documents and checks their target paths are DISJOINT; derives the
    resolved selections including each Job's full input manifest and its
    `job_input_identity`; performs the Authority acts through the supported
    API (two Works under a derived act identity, both implementers on `impl`,
    both reviewers on `rview`, the integrator on `integration`, four scoped
    grants per Work, the canonical target); and composes and validates through
    the shipped `two_jobs.py`.
  * **Twelve owner questions become four undeciderable operands**: the fresh
    run root, the fixture repository, its base and the bootstrap's uuid.
    Everything else is derived from W239528 claim 244216 and the deployment
    W239533 executed, with the provenance recorded beside each value.
  * **ADOPTION steps 2 and 3 are the setup commands**: the human acts — the
    directory and the fixture commit — then the bootstrap, then the one
    preparation command. Preparation and execution stay separate steps, and
    preparation reaches no container, credential, provider, engine, network or
    deployed store.
  * **Nine cases** drive the derivation, the disjointness refusal, the
    consumed-root refusals, the manifest/task binding, the four distinct
    identities, the absence of credential bytes, and the Authority acts on a
    disposable Authority.

## Two things measured rather than assumed

`create_work` refuses a Work that already exists under somebody ELSE's act —
pointing the step at a Work the witness fixture had minted answered `Work
'0000000a-W1' already exists`. Replay is same-identity replay, and the case
drives it twice to show that.

The manifest digest is the product's own rule. My first draft hashed canonical
text itself and met `a manifest that does not identify itself is not one`; it
now asks `digest()` over every member but `manifest_digest`, which is what
`verify_manifest_digest` recomputes.

## Evidence

`verification-21.json` — 71 checks, 0 failures, 67.84404368200921s, pins agree.

## REMAINING

The operator's own steps: the fresh root, the fixture commit and the bootstrap,
then the preparation command, then — as a separate decision — the run. The
container boundary and the live provider under concurrency stay unproved and
are what the run would answer.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250733

### The questions became a step

The packet asked an owner twelve questions. The owner's answer was that most of
them are not questions: they are derivable from the configuration W239528 and
W239533 were accepted on, and the ones that are not should be a short list.

`prepare_two_jobs.py` is that step. It takes four operands nobody can derive —
the fresh run root, the fixture repository, its base revision and the uuid the
instance bootstrap minted — and derives the rest: the four participants, the
roots, the credential reference and registry, the network, the retention and
policy digests, the profiles, the adapter, the image, both task documents and
both input manifests. Each value carries where it came from.

Then it acts: two Works under a derived act identity, both implementers on
`impl`, both reviewers on `rview`, the integrator on `integration` because the
review worker passes its answered assignment there, the four scoped grants per
Work, and the canonical target. Then it composes and validates through the
shipped composer rather than a second path.

It reaches no container, credential, provider, engine, network or deployed
store, and it performs no Git operation — the fixture commit is the operator's,
and so is the run.

### Disjointness is a refusal, not a convention

The two tasks create `greet_a.py` and `greet_b.py` against one declared base.
Two Jobs writing one path would be one contended change rather than two
independent development lines, so the step refuses it by name and a case drives
that refusal rather than trusting the constants.

### Two things I measured rather than assumed

`create_work` does not adopt a Work that is already there. Pointing the step at
one the witness fixture had minted answered `Work '0000000a-W1' already
exists`. That is the right behaviour and it means replay is SAME-IDENTITY
replay; the case now drives `prepare` twice under one act identity and asserts
it answers the same two Works.

The manifest digest is the product's rule, not mine. My first draft hashed
canonical text and met `a manifest that does not identify itself is not one`.
It now asks `digest()` over every member but `manifest_digest`, which is what
`verify_manifest_digest` recomputes — the same lesson as `input_digest`, where
a hand-filled value disagreed with the manifest it was supposed to identify.

### Verification spending

**`verification-21.json` — 71 checks, 0 failures, 67.84404368200921s**, pins
agree.

Named suite subtotal: 550.379416662s + 67.84404368200921s =
**618.223460344s**.

Also measured this claim and NOT in that subtotal: three suite runs at 67.271s,
67.860s and 67.902s while the new cases were being corrected; one 35.905s run
that loaded the FIXTURE's own accepted cases because it named the class rather
than the module — discarded, and a reminder of why `load_tests` filters; one
67.59736998900189s receipt run taken before the line-length rewrap and re-taken
after it, so only the second is the receipt; and three single-case runs under a
second. Earlier disclosed costs and the ~120s timeout overlap stand unchanged.

State: passed for independent review.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250733" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
