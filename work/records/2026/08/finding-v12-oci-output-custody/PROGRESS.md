# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-27 — claimed; PLAN 1, the W6634 revalidation

Claimed W26283 at seq 26319. This is the successor Work I asked for while
holding W6636: that round found W6634 closed non-satisfying with no successor,
so freeze, collect, destroy and positive absence were unreachable on certified
code. The approver ruling authorized this provider.

PLAN item 1 is "revalidate the W6634 spike against current contracts", and the
finding is explicit that **provisional code is evidence, not accepted
implementation**. So this is a search for what is wrong, not a confirmation of
what is right.

### The contracts still say what the finding says they say

Checked against the frozen `worker-control-1.0` schema rather than against the
W6634 dossier:

| pinned | current tree |
| --- | --- |
| `completionManifest` — assignment_ref, disposition, outputs | present, `unevaluatedProperties: false` |
| `resultManifest` — requires `completion_manifest_digest`? | **optional**, and the code treats it so |
| `outputDescriptor` / `outputConstraints` | present; `link_policy` is `const: "forbid"` |
| `contentManifest` / `contentEntry` | present, entries/entry_count/total_bytes/tree_digest |
| W19784 owns assignment identity | unchanged; consumed, not redefined |

### Six of the seven obligations are met by the provisional code

Read in full rather than sampled:

- **bounded, no-follow, nonblocking read of the worker output** —
  `_read_without_following` opens `O_RDONLY|O_NOFOLLOW|O_NONBLOCK` and checks
  `S_ISREG` on the *descriptor*, not the path;
- **exact manifest comparison** — shape by the shipped validator, then
  `assignment_ref` against this attempt's, then §12 rule 15 both ways;
- **digest from the bytes opened** — recomputed over the read body;
- **live-secret rejection** — `check_no_durable_secret` runs over each staged
  file's *content*, decoded leniently so a binary file cannot be the way past;
- **atomic publish** — private name, `fsync`, `os.replace` onto `sealed.json`;
- **replay above every state read** — the committed record is consulted before
  the worker's envelope, and is bound to six members of the request so one
  attempt's stored answer cannot settle a different operation.

### [P1] The seventh does not hold: staging reopens by path

`_staged` copies each measured entry with a plain `open(source, "rb")`.
W6631's measurement is race-safe — it descends by opened directory identity and
opens every file `O_NOFOLLOW` relative to that descriptor — and the staging copy
throws that away by resolving a path string again.

**Proved, not inferred.** Two harms, both driven against the real code:

1. **Host material reaches custody.** After the measurement, renaming a
   measured subdirectory and putting a symlink in its place makes the copy read
   through the link: custody ended up holding a file from outside the workspace
   entirely. The double measurement afterwards refuses the *result*, but only
   after the bytes were read, scanned and written.
2. **One `mkfifo` hangs the manager.** Replacing a measured regular file with a
   FIFO makes `open` block forever. A 12-second probe timed out. This is
   exactly the failure `_read_without_following` added `O_NONBLOCK` to prevent
   for `output.json`, reintroduced one function away.

This is the same defect class this module has already fixed twice — once for
the completion envelope, once inside the walker, whose own comment records that
"a no-follow open of the FINAL file does not stop a raced ANCESTOR from
becoming a symbolic link". Staging is the third place it appears, and it is the
place the acceptance names directly: *"Symlinks, non-regular files, path
escape... fail closed"* and *"the sealed manifest describes the
manager-custodied bytes, not a path later reopened from worker storage."*

### What that implies for the fix

Re-opening safely would still be two opens with a window between them. The
measurement already reads every byte through a descriptor it proved; staging
should write *those* bytes rather than fetch them again. That closes the window
by construction instead of by comparison, and it is what the acceptance means by
custody describing bytes rather than a path.

The traversal belongs to `workspaces` (W6631) — sealing's own docstring warns
that "a second walker here would be a second thing to keep true" — so the
one-pass measure-and-copy goes there as an additive function, with the §13
secret rule staying in `sealing`, which owns it.

## State

Revalidation done. Implementing PLAN items 2–3 next.
