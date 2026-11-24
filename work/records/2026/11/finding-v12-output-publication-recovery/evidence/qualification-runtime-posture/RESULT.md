# Qualification runtime posture and same-recovery continuation

The recovery-7 script incorrectly asserted the image default USER 65532:65532 against a container whose launch vector overrides it. workspaces.identity_for derives the manager euid and configured workspace group; oci.run_vector uses that exact identity. The captured 1000:1001 is correct. A second stale assertion expected only /output writable, omitting the existing required /scratch, exchange/events and attempt-logs mounts. No product runtime or permission change is made.

The corrected check verifies the expected non-root UID/configured group, network none, exact writable destinations AND their exact attempt-owned host paths, all input mounts read-only and no credential mounts/provider credential variables. It passes the retained publisher capture; negative probes reject root UID, wrong group, writable input and foreign scratch. Four refusal probes retained in negative-checks.json.

The resume script operates on recovery-7's existing admitted decision, checks it is already handed off/published, reuses the exact digest-pinned publisher capture with explicit provenance, restarts only its stopped manager through the existing ownership/cleanup mechanism and waits for review. It calls no decide/create/bootstrap and reruns neither producer nor publication. The new resume.* evidence namespace leaves previous evidence unchanged. No source or image changes, build, installation or live launch during preparation. Python wrapper --check and shell syntax passed.

Owner command: python3 /tmp/baton-w385695-resume-review.py. Reviewer completion and its live confinement probe remain unproved until the script succeeds. The check does not turn the earlier failed qualification into success.
