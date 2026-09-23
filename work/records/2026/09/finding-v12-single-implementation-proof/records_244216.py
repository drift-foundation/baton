"""Claim-244216 dossier entries."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PROGRESS = """
## 2026-09-23 -- baton.claude, claim 244216, the corrected worker image

Owner reroute 244214 selects the corrected worker-image build and the successor
packet. The selection was recorded in FINDING and the accepted source verified
in the tree BEFORE the build, as that reroute requires (`pin_244216.py`
refuses if the tree is not the accepted `18c34ff5...f9d8d`).

No live provider execution. No deployed provisioning, recovery, reviewer stage,
resume or closure. No file under `v12/` was edited this claim.

**Coordination with W244180.** The tuner's Work is bound to
`work/records/2026/09/finding-v12-review-job-preparation/` and was active when
this claim began. There is no file overlap: that dossier is its own, this one
is W239528's, and nothing here touches it or W239533.

**The image.** `baton-v12-claude-worker:w239528-244216`, built from
`v12/worker/Dockerfile.claude` over the accepted source, at
`sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`.

**Verified from INSIDE the artefact, not from the build context.** Every digest
was read out of a container started FROM the image, `--network none
--read-only` with the entrypoint overridden; the recipe makes exactly this
point about itself. `opt/baton/claude_agent.py` is `18c34ff5...f9d8d`, and
`PROVIDER_UMASK` was read back by name as `0o77` from the running image rather
than inferred from the digest. The provider CLI is unchanged at 2.1.247.
`IMAGE-ARTIFACT-244216.json` records the whole `/opt/baton` inventory.

**The predecessor is preserved and that was checked before anything was
written.** `baton-v12-claude-worker:w236087-236349` is still tagged, still
`sha256:2e9e84ff...7456bd`, and still carries `abdf903d...bb4d` -- the adapter
WITHOUT the correction. Every earlier packet in this campaign binds it, and
W236087's own packet still names it. `image_244216.py` refuses if that digest
has moved, and refuses if the new image turns out to be the same artefact.

**The packet binds what was verified.** `SELECTIONS-SUCCESSOR-244216.json`
carries the built reference and config digest, the four worker-file digests
read from inside the image, fresh dedicated stores under
`/home/sl/baton-runs/single-implementation-244216/`, a new run and Job
identity, and the retained 180/300/60 bounds.
`TheCorrectedImageIsWhatThePacketBinds` asserts the selections agree with the
artefact record file by file -- a packet naming a digest other than the one
that was verified would bind an image nobody checked -- and that the new
artefact is distinct from the preserved one.

**What it can and cannot answer, in the document and in the selections.** It
CAN answer whether the real CLI under the provider mask leaves a context home
the manager can seal, which is the one thing no deterministic test can
establish and the reason this image exists. It CANNOT answer that it will:
review 2026-09-23T03:19:21Z is explicit that the retained `0o755` modes are
consistent with umask creation but do not exclude an explicit `chmod` or a
reset mask. If the CLI does either, the run reaches the same custody hold --
reported now in about six seconds rather than at the bound -- and that is a NEW
finding rather than a failure of the packet. The operator document says which
outcome means which, and tells an operator to check
`worker_image.config_digest` before running, because binding
`sha256:2e9e84ff...` would silently ask the old question again.

Verification: 151 focused deterministic checks, measured 26.85811222800112s,
receipt `verification-9.json` with `verification-9.log`; 8 are new.

Cumulative measured for W239528: 730.969349485s (through claim 244098) +
26.858112228 + 0.408 (claim 244216) = **758.235461713s**. The image build and
its verification are artefact work rather than test time and are recorded in
`IMAGE-ARTIFACT-244216.json` instead.

State: awaiting independent review.
"""

PLAN_DONE = """
## Done under this claim

1. Selection recorded and the accepted source verified in the tree before the
   build (`pin_244216.py`).
2. `baton-v12-claude-worker:w239528-244216` built from the accepted source,
   distinct from the preserved image.
3. Verified from inside the artefact: the accepted adapter digest, the
   `PROVIDER_UMASK` value read back by name, the whole `/opt/baton`
   inventory, and the predecessor still at its own digest with its own
   adapter. `IMAGE-ARTIFACT-244216.json`.
4. `SELECTIONS-SUCCESSOR-244216.json` and `OPERATOR-SUCCESSOR-244216.md` bind
   the verified reference, config digest and worker digests, with 180/300/60
   retained and fresh dedicated stores; eight checks assert the packet agrees
   with the artefact record.

Verification: 151 dossier checks, 26.85811222800112s, receipt
`verification-9.json`.

## What remains the owner's

Whether to run it, with a VALID credential -- that is the run that can answer
the custody question. Nothing here authorizes it.
"""

OWNERSHIP = """
## Claim 244216 -- the corrected image and its packet

Added: `pin_244216.py`, `image_244216.py`, `IMAGE-ARTIFACT-244216.json`,
`SELECTIONS-SUCCESSOR-244216.json`, `OPERATOR-SUCCESSOR-244216.md`,
`records_244216.py`, `verification-9.json/.log`.

Edited: `test_successor_packet.py`, `verify.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file.

**No file under `v12/` was edited.** The accepted adapter source is the one
review 2026-09-23T03:19:21Z accepted and is unchanged.

OUTSIDE the checkout:

    NEW        baton-v12-claude-worker:w239528-244216
                   sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2
    PRESERVED  baton-v12-claude-worker:w236087-236349
                   sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd
                   re-read and unchanged; neither retagged, rebuilt nor removed

W244180's dossier (`finding-v12-review-job-preparation`) and W239533 were not
touched.
"""


def main():
    progress = HERE / "PROGRESS.md"
    if "claim 244216" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    old = "## Not in scope\n"
    if "Done under this claim" not in body.split("# Historical", 1)[0]:
        plan.write_text(body.replace(old, PLAN_DONE + "\n" + old, 1),
                        encoding="utf-8")
    owner = HERE / "OWNERSHIP-239528.md"
    if "Claim 244216" not in owner.read_text(encoding="utf-8"):
        owner.write_text(
            owner.read_text(encoding="utf-8").rstrip("\n") + "\n" + OWNERSHIP,
            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
