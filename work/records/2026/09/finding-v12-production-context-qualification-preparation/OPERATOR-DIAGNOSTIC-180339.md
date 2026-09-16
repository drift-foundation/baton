# Fixed-path metadata diagnostic — the exact command

baton.claude, W177936 claim180339, owner selection180325 from
`review-2026-09-15T18-36-00Z.md`. **Run this on the ORIGINAL OPERATOR HOST.**
It was not run against the private tree from the managed context, whose identity
and mount view are not the operator's — that is the whole reason the review asks
for the host view.

## The command

From the baton repository root, one line:

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/diagnostic-180078.py
```

It prints JSON to stdout and writes nothing. To keep the result with the rest of
the evidence, redirect it — the operator chooses the path, and the script never
creates one itself:

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/diagnostic-180078.py > work/records/2026/09/finding-v12-production-context-qualification-preparation/operator-result-2026-09-15T18-29-34Z/metadata-180078.json
```

Exact bytes: `diagnostic-180078.py` sha256 `386f23a4b2e37110ea42fdc733004642ed2e998522c6a180b5dae87bbaafb1c5`.
It takes **no arguments** and refuses any, with exit 2: a path operand would turn
a fixed-path diagnostic into a general private-tree reader.

## What it reports

The operator's **numeric** identity — real and effective uid/gid and the
supplementary groups — and one row for each of the eleven fixed operands under
`/tmp/baton-w177936-qualification-180078`:

| # | operand | # | operand |
| --- | --- | --- | --- |
| 1 | `<root>` | 7 | `private-layout.json.tmp` |
| 2 | `use-1` | 8 | `use-2` |
| 3 | `use-1/home` | 9 | `use-2/home` |
| 4 | `use-1/home/.claude` | 10 | `use-2/home/.claude` |
| 5 | `use-1/home/.claude/projects` | 11 | `use-2/home/.claude/projects` |
| 6 | `private-layout.json` | | |

Each row carries exactly: `operand`, `state` (present / absent / error),
`type`, `uid`, `gid`, `mode` (numeric), `links`, and `errno` from the closed
enum EACCES, EPERM, ENOENT, ENOTDIR, ELOOP, ENOSPC, EDQUOT, EIO, other.

## What it cannot do, by construction

It never opens a regular file, lists or traverses a directory, calls
`readlink`, writes, chmods, chowns, or resolves a user or group **name**.
Account names are arbitrary strings, so identity is numbers only. No content,
hash, size, mtime, link target, exception string or traceback is produced, and
**every operand label is a constant in the source** — nothing the tree contains
can become a label.

**No component is followed, not just the last one.** Plain `lstat` protects only
the final component: if `use-1/home` were a symlink, an `lstat` of
`use-1/home/.claude` would silently describe a different location and look like
a clean answer. Each operand is walked component by component through
`O_PATH|O_NOFOLLOW|O_DIRECTORY` descriptors instead. **A symlinked intermediate
is refused as `ENOTDIR` on Linux** — `O_DIRECTORY` is consulted before
`O_NOFOLLOW` — and as `ELOOP` elsewhere; both are in the closed enum.

## Reading the result

The failed run reached collection and stopped somewhere between the first-home
inventory and the subset-reconstructed event. So the interesting half of the
list is the **absent** half: `private-layout.json` present or absent separates a
failure before the layout save from one after it, and any `use-2` operand
existing means destination-home creation had begun. An `EACCES` on
`use-1/home/.claude` or below is consistent with the review's permission
hypothesis — **consistent with, not proof of.** POSIX mode bits do not account
for ACLs, namespaces or other policy.

**This cannot recover the stopped attempt's original error**, which was never
retained: `failure_code` collapsed it to `unclassified`. Recovering the substep
needs the separate closed-diagnostics fixture correction, which is **not**
selected here.

## Boundaries

Identity 180078 is **consumed and stays consumed**; metadata inspection cannot
convert its result into success. Do not chmod, chown, repair, reset markers,
switch collection identity, rerun the fixture or prepare a new identity on the
strength of this output — the review says a permission or copying change needs
its own bounded rationale and must not be bundled with a guess. Both consumed
root sets, 180078 and 178579, stay untouched.

**Not selected by owner180325 and not prepared:** the review's conditional
bounded no-content walk of the two homes, and the closed collection
step/category/errno fixture correction. Either may be selected after reading
this output.

Model acceptance is unchanged: `modelUsage` is expected-plus-other with two
keys, `actual_model` stays null, and G1 stays unqualified.

## Verification

`diagnostic-180078-selftest.py` — **14 tests, OK** — exercises the script
against a **synthetic** tree only: present/absent rows and the closed field set,
a symlinked intermediate refused rather than resolved, an unsearchable directory
reporting EACCES, a non-directory component reporting ENOTDIR, canaries planted
as a project name, a session filename, file content and a link target with none
reaching the export, and a before/after walk proving looking at the tree does not
modify it. A static check over comment-stripped source confirms no `readlink`,
`listdir`, `scandir`, `walk`, bare `open`, write, chmod, chown, `pwd`, `grp`
or `subprocess`, and that both `os.open` calls carry the no-follow directory
flags. The real 180078 tree was never touched.
