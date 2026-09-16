# Bounded metadata-only home walk — the exact command

baton.claude, W177936 claim180413, owner selection180411 from
`review-2026-09-15T18-36-00Z.md`. **Run this on the ORIGINAL OPERATOR HOST.**
The private tree was not walked from the managed context — and here that is not
only a rule: the read/search classification is relative to the identity that
runs the script, so an answer computed under the wrong identity would be
confidently wrong rather than merely useless.

## The command

From the baton repository root, one line:

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/walk-180078.py
```

JSON to stdout, nothing written. To keep it with the other evidence:

```sh
python3 work/records/2026/09/finding-v12-production-context-qualification-preparation/walk-180078.py > work/records/2026/09/finding-v12-production-context-qualification-preparation/operator-result-2026-09-15T18-29-34Z/walk-180078.json
```

Exact bytes: `walk-180078.py` sha256 `7cf7dae6651f13dd54228eef1505ad5b3e481d43058569d836640fcf57a80f8d`. It takes **no arguments** and
refuses any with exit 2 — a path operand would make it a general private-tree
lister.

## Why this walk, and what it is looking for

The fixed-path result put the failure in a specific interval:
`private-layout.json`, its tmp sibling and **every** `use-2` operand are absent,
so the run stopped before the layout save and before destination-home creation —
inside first inventory or subset selection. `inventory` reads and hashes every
admitted regular file except `.claude.json` and the excluded credential link.

The fixed paths showed the five top directories are mode-permitted for your
identity and could say nothing about their descendants. **`use-1/home/.claude/projects`
is uid65532 gid1001 mode `0o2755`** — provider-created, group read and search,
no group write. That is where the runtime's own files begin, and a nested file
the collector could not open is the one hypothesis left standing.

## What it reports

Your numeric identity, and for each of `use-1/home` and `use-2/home` an
**aggregate**: counts grouped by `type`, `uid`, `gid`, `mode`, `readable` and
`searchable`, where the last two are what the POSIX bits permit **your** reported
identity. Plus honest coverage — `entries`, `truncated`, `depth_limited`,
`timed_out`, `max_depth_reached`, `complete` — and traversal errors as
`opendir:CATEGORY` / `stat:CATEGORY` / `scandir:CATEGORY` counts from the closed
enum EACCES, EPERM, ENOENT, ENOTDIR, ELOOP, ENOSPC, EDQUOT, EIO, other.

`use-2/home` is absent; it is reported **absent, not an error**.

**Aggregates, not entries.** A per-entry list would be a directory listing of a
private tree wearing a different hat. The grouping answers the question actually
asked — is anything in here unreadable to the collector — without exporting what
is in here.

## Bounds, and what happens at them

1024 entries per home, depth 8, 20 s wall time. **Reaching a bound is reported,
never silently absorbed**: a truncated walk that looked complete would be worse
than no walk at all, so `complete` goes false and the specific flag goes true.

## What it cannot do, by construction

Never opens a regular file, follows a symlink or calls `readlink` — links are
counted where found and never resolved. Never descends into a credential-shaped
entry, using **the fixture's own pattern** so the walk stops exactly where the
collector stops rather than inventing a second rule. Never writes, chmods,
chowns, or resolves a user or group **name**. **No discovered name, path, path
hash, size or mtime is exported**, and no exception string or traceback.

Directories are opened `O_NOFOLLOW|O_DIRECTORY` from their parent's descriptor,
so a symlinked component is refused rather than silently resolved.

## Reading the result

A `regular` group with `readable: false` inside `use-1/home` is the hypothesis
confirmed as far as metadata can confirm it. An `opendir:EACCES` or
`stat:EACCES` count says the walk itself hit the same wall the collector would.
An entirely permitted aggregate makes the permission hypothesis **less** likely
and points elsewhere — an unregistered refusal or a programming error.

**None of that is proof.** POSIX mode bits do not account for ACLs, namespaces or
other policy, so permitted is not proof of readability and denied is not proof of
the failure. **The original exception was never retained** — `failure_code`
collapsed it to `unclassified` — so no metadata inspection can recover it. That
needs the separate closed collection step/category/errno fixture correction,
which is **not** selected and **not** prepared.

## Boundaries

Identity 180078 is **consumed and stays consumed**. Do not chmod, chown, repair,
reset markers, switch collection identity, rerun the fixture or prepare a new
identity on the strength of this output: a permission or copying change requires
its own bounded rationale and must not be bundled with a guess. Both consumed
root sets, 180078 and 178579, stay untouched. Model acceptance is unchanged —
`modelUsage` is expected-plus-other with two keys, `actual_model` stays null, G1
stays unqualified — and this walk cannot identify the other key.

## Verification

`walk-180078-selftest.py` — **21 tests, OK** — against synthetic trees only:
absent home reported absent; closed aggregate shape with counts summing to
entries; an unreadable nested file classified but not opened; unsearchable and
unopenable directories reporting on their **different** handlers; links counted
and not followed; credential-shaped entries skipped; a symlinked home component
refused rather than walked; each of the three bounds stopping and saying so; a
clean tree reporting complete; canaries as a directory name, a filename, file
content and a link target with none reaching the export; no descriptor leaked
across repeated runs; and a before/after walk proving the tree is not modified.

`probes-180413.py` — **ten reversal probes, each failing exactly where it
should**, each in an isolated copy with `__pycache__` removed and `-B`.
