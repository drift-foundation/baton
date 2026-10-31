# Required initial-access slice — W384944 / E384969

Four required InitialPrivateLineEngine cases actually executed and passed, zero failures/errors/skips. One focused run: 2.095s unittest body, 2.316297s command wall. Six real Docker containers, scripted payloads, no live providers. Full IDs/outcomes in ledger.json and first/focused.log.

## Contract and exact candidate

Only `v12/python/tests/manager/test_private_line_access_engine.py` changed. HOST-5 and work/records/2026/09/finding-v12-workspace-shared-identity/OWNER-TRUSTED-IDENTITY-20260917.md allow trusted shared identity; oci.run_vector selects workspaces.identity_for(group), which derives manager effective UID and configured workspace GID. Replaced historical 65532/foreign-owner expectations with this exact identity and added engine Config.User assertions. Updated the foreign-owner explanation. Preserved test IDs, real Git writes, file modes/group, read-only source and reviewer checkpoint denial, same-line device/inode, correction parent commit and both checkpoint references/audit assertions. No product or shared-fixture edit.

Candidate SHA256 `537368420a756891689c2aa5449a77e6e28eb6efbb4331e93f7e8097a21c7d17`; base `20981569e64054222404b4765d3114c4dbb7630c02aa70e81ac7ee0ec06ae2d7`. Exact base/candidate/diff retained. Stable snapshot a8cbc9745d1eff51bcfb04d2fe4bb96a5ea3b12d: all 1133 paths verified, only this candidate and accepted integration-worker overlay differ. Before/after source hashes show no drift. Shared target matched base immediately before same-file transfer; accepted integration overlay preserved.

## Execution and custody

Image: sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4; exact installed image inspected, no image volumes, no pull/build. Prepared Python 3.13.7. Rechecked actual uid1000 and supplementary gid1001 membership; fresh root gid1001/mode2770. Selected variables and root are in first/preflight.json. The external run helper adds only a unique evidence label to each Docker run through a temporary shim, preserving product run restrictions/mounts. 600s execution timeout with exact-label emergency cleanup; no timeout or emergency removal needed.

Engine evidence records each exact ID, image, User, mount access, restriction fields, payload logs, wait and removal. All six declare 1000:1001 and report uid1000/gid1001. All mount /input and /input/source read-only and /output writable. Reviewer actually reads the written content and receives EROFS (30) for tracked, .git/HEAD and reviewer-new while writing its own findings. Correction commit and original frozen history checks pass. These are bounded test observations, not a new startup identity probe or broader deployment qualification.

All six task containers removed by fixture cleanup; post-run task label query empty. All pre-existing container IDs remain present (no historical container/image/cache cleanup). Fresh root empty and removed. Exact resource evidence: first/engine.jsonl, preflight.json, result.json and ledger.json.

## Remaining B4

The accepted integration-worker module is 83/83 on this snapshot; this four-case slice is ready for independent review. Remaining historical engine failure/error IDs are copied without rerun in remaining-engine-inventory.tsv (the four initial-access skips removed from that pending list). Input-delivery shared-identity/store/race fixtures, custody fixtures, ending/adoption cases and worker-entry expectations still need coordinated allocation/revalidation. Pure image recipe contracts and integration-driver retained-root cases remain as recorded in preflight; no new result is claimed. Joined current-tree verification after K stabilizes, full B4 and parent acceptance remain due. No other module/group/full suite or Git repository mutation.
