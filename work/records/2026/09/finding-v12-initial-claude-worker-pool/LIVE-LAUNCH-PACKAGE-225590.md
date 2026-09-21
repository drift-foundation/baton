# The live-launch package, revised per review225576 (claim225590)

SUPERSEDES `LIVE-LAUNCH-PACKAGE-225533.md`, whose deployment bound a
verification argv that could not run from the candidate root (R1) and — found
by R1's own demonstration — a provider image that could not import the suite
it verifies. Both are corrected, demonstrated, and REDEPLOYED ON A FRESH
INSTANCE; the two authorized commands below are the only steps left. Nothing
here has started a stack, reached a provider, or submitted a Job.

## The deployment this package is bound to

- Instance: `/home/sl/baton-v12/instance-2026-09-21T01-28-41Z` — installed
  this claim from the SAME reviewed candidate 225452 distro
  (pre/post identity: executable `786af0d5…`, 81-file bundle `7305d1c7…`,
  both equal the reviewed records). A fresh root was REQUIRED: the manager
  refuses to change an existing deployment's task bytes in place
  ("a repeated bootstrap preserves what is there"), which it did, correctly,
  on the 01-12-21Z instance.
- Authority: `13c91b695bfe4625b4f22dabd35a54a4`.
- Preserved untouched: the owner-installed `instance-2026-09-21T01-12-21Z`
  (its deployment still binds the superseded argv/image and was never
  started) and the A/B evidence instances.
- Nominated source (per-instance, populated by the installer):
  `/home/sl/baton-v12/instance-2026-09-21T01-28-41Z/repo/workspace`, whose
  `refs/heads/main` == accepted base
  `446fa8f79d9569799a77e888e8236070e1dc78f7` (verified read-only this
  claim). The 225533 package's naming of `/home/sl/src/baton` as the
  nominated source was wrong (that is the workspace's own origin);
  corrected here per review225576.

## R1 correction — the frozen verification argv, demonstrated

The argv runs shell-less with cwd at the candidate root, so the interpreter
itself enters the subtree:

    python3 -c "import os, sys, unittest; os.chdir('v12/python'); \
      sys.path[:0] = [os.path.abspath('src'), os.path.abspath('.')]; \
      unittest.main(module=None, argv=['unittest', \
      'tests.tools.test_pool', 'tests.tools.test_bootstrap'])"

Demonstrated from a repository-root candidate context (a scratch clone OF THE
ACTUAL nominated-source shape at exactly the accepted base, HEAD `446fa8f7…`,
root `tests/` holding only `conftest.py` and `work` — reproducing R1):

- With a CLEARLY-LABELED fixture `v12/python/tests/tools/test_pool.py`
  ("LAUNCH-PLUMBING FIXTURE — NOT the task's deliverable"; discovery proof
  only, no implementation coverage claimed, never enters the repository):
  the exact argv ran **126 tests OK, exit 0** — the fixture module plus the
  ENTIRE existing bootstrap family.
- With a deliberately failing fixture test: **exit 1** — the gate's verdict
  travels in the exit status (`unittest.main` semantics).

## The second blocker R1's demonstration found — the provider image

Inside the previously configured image (`9ff3322f…`), the same argv died at
COLLECTION: `ModuleNotFoundError: jsonschema` — the product's one declared
third-party dependency (pyproject: the Worker Manager consumes frozen JSON
Schema) absent from the image that runs the product's tests; that image has
`/usr/bin/python3` only, no pip, no venv. No cwd correction can fix that.

Correction: `worker/Dockerfile.claude` adds `python3-jsonschema` to the one
apt line (rationale in-recipe: the `git` rule's second instance — a
capability must exist where it runs; the Debian package brings its own
closure, no pip, no build toolchain). Candidate image
`baton-v12-w202663-provider:claim225590`, content digest
`sha256:448c98c937849e5c6dcdd03cc33936084f698d0175520b2a5cbe9a9af92e8559`.
Demonstrated INSIDE that candidate image, network-disabled, candidate
mounted read-only, entrypoint overridden to the bare interpreter: the exact
frozen argv ran **126 tests OK, exit 0**. The recipe's own serial gate
(`tests.manager.test_dogfood_image`, 16 tests) passes. Per the recipe's
selection doctrine the image is a CANDIDATE; your launch authorization is
the selection event.

## Redeployment on the fresh instance — gates re-run

- Composition at `--base 446fa8f7…`: complete, zero refusals; job input
  identity `sha256:87033f1b…` (moved from `1ad3c142…` because the frozen
  task bytes and image digest changed — exactly what review225576 required
  re-checking).
- Staged task at the instance verified: argv is the corrected vector; the
  configured worker image digest is the candidate `448c98c9…`.
- Policy pin GATE: configured 14 == Authority generation 14. (The gate
  refused twice more first and both refusals were prediction defects it
  exists to catch, now recorded in the composer: "first" means no CONFIGURED
  CAPACITY — this installer writes an empty `deployment.json` at install, so
  a file-existence test misread fresh roots.)

## Owner input preparation (unchanged, the one thing only you supply)

Credential slot `claude` → provider `operator-file`, reference
**`w202663-development`**, sources file
`/home/sl/.baton/credential-sources.json`, credential homes under
`<dest>/workers/{implementation,review}/credentials`. Ensure the reference
resolves to a live Claude credential you intend to spend. This Work read
nothing behind the locator.

## The two authorized commands (run only on your authorization)

    DEST=/home/sl/baton-v12/instance-2026-09-21T01-28-41Z
    just --justfile "$DEST/justfile" start
    cd /home/sl/src/baton/v12/python
    PYTHONPATH=src:. python3 -m tools.job_manager \
      --store "$DEST/db/jobs.sqlite3" \
      --incarnation w202663-claude-job-submit \
      --authority-uuid 13c91b695bfe4625b4f22dabd35a54a4 \
      submit --document /home/sl/src/baton/work/records/2026/09/finding-v12-initial-claude-worker-pool/pool-submission.json

On your signal after submit, I observe to terminal report-and-hold and
extract candidate/verdict/stream evidence through the supported public
readers — the same cadence as A and B.

## Enforced limits — RESOLVED NUMBERS for this exact Job

From `execution_limits` (compatibility generation, pinned at submission so a
later default change cannot retime this Job):

- `provider_turn` = **3600 seconds** per provider invocation
- `ordinary_verification` = **900 seconds** per verification command run
- (`integration_verification` 1800 s / `host_verification` 300 s exist in
  the generation but no integration stage composes here)

EPISODE vs MODEL TURNS, distinguished: ONE authorized episode = one
container invocation of a stage's worker. Inside it the model may take many
internal tool/conversation turns; the 3600 s bound is on the whole provider
invocation, not per internal turn. Report-and-hold opens ONE offer per
stage and re-offers only through recovery, which is NOT authorized — so the
authorized spend is at most one producer episode and one reviewer episode,
each hard-bounded as above. These are per-invocation ceilings; they are NOT
a claimed total-spend bound beyond the two-episode structure stated.
Nothing merges without you (OWNER-PR-FLOW-220329.md governs acceptance).

## What this package does NOT do

No start, no submission, no provider contact, no credential read. The
scratch demonstration context lives in `/tmp` and never enters the
repository. Do not rerun deterministic A/B; their instances and the
01-12-21Z instance are preserved evidence.
