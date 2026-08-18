# Plan

- [x] Compare the reviewed and deployed archives at member and byte level.
- [x] Pin the reproducibility ruling and cutover hold.
- [x] Record Slawomir's evidence-bound exception allowing `137d7fc` to cut
  over while this packaging defect remains open.
- [x] Replace the mtime-sensitive v11 zipapp construction with a deterministic
  writer or shared deterministic helper.
- [x] Add a regression that perturbs source mtimes and proves identical
  executable bytes and digest across two fresh deployments.
- [x] Run focused deployment/package tests and the complete v11 gate.
- [x] Independently review the resulting diff and evidence. Round 1 requested
  fixed member-mode assertions; round 2 accepted the correction after 16
  focused deployment tests and a clean diff check.
- [ ] (Slawomir; requires a commit, which agents never make) After the correction is committed, deploy it to a new immutable release
  directory and verify stable rebuild digests before using that release.
