# RC 1.0.0 final release gate

Date: 2026-08-11

Reviewer: `baton.reviewer`

Outcome: **passed; ready for the reviewed commit-message handoff**.

## Exact candidate

- release: `1.0.0`;
- protocol: 10;
- CLI artifact:
  `8798de0c92d0bbba7ea7ad1d5bf17070b270155ebe1caef7f24e7706dd2330ab`;
- TUI artifact:
  `24f08cb1c73ac0ecbe4108e24c4926dc7c2690e35bbc1626652440543361e04a`.

Both executables report the exact ruled one-line version. Sequential
`just build` then `just build-tui` reproduced the approved artifact hashes and
their distribution manifests without drift. `git diff --check` passed.

## Complete suite

`just test` passed **2318/2318** on the exact candidate in 208.86 seconds.

## Packaged workflow smoke

A copied `bin/baton` ran outside the repository with no `PYTHONPATH` against a
fresh temporary authority. The smoke passed:

- directed send, read-only wait, exact claim, reply, response claim, and close;
- participant-authorized materialization/reread with byte comparison;
- subject-only multi-recipient publication and independent recipient claims;
- scoped notice wake and delivery to both matching participants;
- independent mark-seen receipts and no repeat delivery;
- exclusion of the nonmatching notice author;
- fresh-authority doctor `ok: true`.

## Live authority

The packaged protocol-10 executable reports the live authority at accepted
generation 2, maintenance off, move state `none`, no active claims, no
quarantines, `ok: true`, and no problems. The already-known operational
warnings remain nonfatal: four unrecognized archive/projection entries and one
orphan projection cache. They do not affect authority integrity or delivery.

## Release disposition

The implementation and final gate are approved. K's complete commit message
was reviewed, amended once to include this gate without overclaiming earlier
commits, and approved verbatim at the hash recorded in
`RC-1.0.0-COMMIT-MESSAGE.md`. The full text has been sent to Slawomir, who alone
stages and commits. That commit is RC 1.0.0.
