# OCI output custody provider

Date: 2026-08-27
Parent discovery: W6636, `work/records/2026/08/finding-v12-local-oci-lifecycle-composition/`
Upstream implementation history: W6634, `work/records/2026/08/finding-v12-sealed-output-credentials/`

## Finding

**Confirmed:** W6636's diagnostic lifecycle review found that W6634's shared output/credential implementation remains provisional and cannot be used as the certification boundary for local OCI lifecycle composition. The W6636 approver ruling authorizes a separate provider Work for manager-owned output custody.

**Confirmed:** This provider owns the fresh-run path from a quiescent worker's `/output/output.json` to a durable manager-owned result. It must:

- open the worker output through a bounded, no-follow, nonblocking regular-file read;
- validate the `completionManifest` and compare it exactly with the assignment and output declaration;
- derive the result digest from the bytes actually opened;
- stage each declared regular-file tree into manager custody under explicit size and entry limits;
- reject live-secret material while the live-secret registry is still armed;
- freeze the staged copy and atomically publish the manager-owned `resultManifest` as `sealed.json`; and
- make exact replay prove request and receipt before any read from transient worker storage.

**Confirmed:** W19784 remains the upstream owner of assignment identity. This Work consumes that identity; it does not redefine it.

**Confirmed boundary:** Credential delivery, the shared quiescence/removal/settlement crossing, restart adoption, reconciliation, and orphan convergence remain outside this provider. W6636 owns those cross-provider and restart concerns.

**Proposed implementation boundary:** Revalidate the W6634 spike against current contracts, then adopt only the portions that meet this finding. Provisional code is evidence, not accepted implementation.

## Acceptance

- A real OCI worker output is copied into manager custody only after exact manifest validation.
- Symlinks, non-regular files, path escape, oversize trees, duplicate or undeclared material, and live-secret bytes fail closed.
- The digest and sealed manifest describe the manager-custodied bytes, not a path later reopened from worker storage.
- Replay is idempotent and does not re-read transient output after a recorded receipt.
- Focused unit, mutation, and real-engine tests cover success, malformed output, bounds, races, replay, and secret scanning.

## Open

- Exact module and type placement must be revalidated against the current v12 manager tree before implementation.

## 2026-08-27 — independent review

**Confirmed P1:** The single-pass copy still performs its final source-file
open as `O_RDONLY | O_NOFOLLOW`, without `O_NONBLOCK`. A worker-controlled name
that was a regular file when listed can become a FIFO before `_read_exactly`
opens it; the manager then blocks inside `os.open` before the descriptor's
regular-file check can run. The existing FIFO cases create the pipe before the
walk lists it, so they exercise the directory-entry refusal but not this race.
`evidence/w26283-review-fifo-race.py` deterministically replaces the entry in
that interval and records the current three-second timeout.

**Open approval gate:** The implementation replaced an existing sealing test's
expected behavior. Repository policy requires clear, case-specific confirmation
for that edit even when the replacement is intended to be stronger. The Work
dossier requires race coverage but does not itself explicitly authorize
replacing that existing expectation; retain the edit only after the approver
confirms this exact replacement.

**Confirmed approved, Baton message 27064:** `baton.slaw` approved the exact
replacement of
`test_a_tree_that_moves_during_the_pass_cannot_reach_custody`. Under the
single-pass descriptor-bound design, custody correctly seals the bytes already
opened even if the source path changes afterwards; the former refusal asserted
a retired two-read window. This approval does not waive the independent FIFO
finding: source opens still must be nonblocking, prove a regular descriptor,
and carry bounded regression and mutation coverage.

## 2026-08-28 — independent re-review

**Confirmed corrected:** the FIFO substitution no longer blocks. The source
open carries `O_NONBLOCK | O_NOFOLLOW`, the descriptor still decides whether
the object is regular, the bounded regression passes, and the original reviewer
reproduction now returns `integrity/path`.

**Confirmed P1:** the byte bound is still applied only after an unbounded
read. `_read_exactly` checks `st_size` once, then `_read_all` loops until EOF
without a ceiling. A worker can grow that open regular file after `fstat`, so
the manager reads beyond both global and declared allowances—or forever—before
`copied_manifest` gets a chance to refuse. The entry ceiling is also checked
after `_read_exactly`, so the over-limit file is read first. Deterministic
evidence is `evidence/w26283-review-read-bounds.py`; required corrections and
verification are in `review-2026-08-28T04-15-23Z.md`.

## 2026-08-28 — the re-reviewed P1, corrected

**Confirmed corrected:** both ceilings now bound the operation they govern
instead of judging it afterwards. `_entry_ceilings` answers with nothing
opened, so the file that crosses a global or declared entry ceiling is never
read; `_byte_allowance` hands the descriptor reader what is left of the
SMALLER of the two remaining byte ceilings and `_read_all` takes at most that
plus one byte. A worker that keeps appending to a file this manager already
opened can therefore no longer widen the work, the memory, or the time before
the refusal — the case that never terminated now refuses in nine bytes.
`directory_manifest` carried the identical late check one function above the
copy and was corrected with it, because the pass that measures a delivered
input root reads worker-controlled bytes too.

**Confirmed decision — the rule this pins, beyond the two call sites.** A
ceiling is a bound on WORK, not a verdict on work already done. Where the
quantity is known before the operation (the entry count) the ceiling runs
before it; where only the operation can discover it (the byte count) the
operation is given the remaining allowance and one byte past the line, which
is exactly what proves the line was crossed. A guard placed after an
unbounded operation is not a bound on that operation, and this is the second
time in this Work that the same shape produced a live defect — the first was
the blocking FIFO open whose descriptor-level proof was unreachable.

**Confirmed unchanged — the taxonomy and its precedence.** A global `MAX_*`
crossing is `policy/denied`; a delivery's declared ceiling is
`integrity/limit`; when both cross at once the global one answers, because
what this build will not do at all is decided before what this delivery was
allowed. The correction moved WHEN each ceiling runs and never which answer it
gives, and both crossings carry a regression that would fail if that changed.

**Evidence.** `evidence/w26283-read-bounds-corrected.py` is the reviewer's
`evidence/w26283-review-read-bounds.py` re-run against the correction, plus a
third probe for the non-terminating case the review named. The reviewer's file
is kept exactly as produced; the corrected copy exists because the required
correction gave `_read_exactly` its allowance operand, so the original's
three-parameter interposition on that function now raises `TypeError` instead
of reporting on the bound. Its byte probe is unaffected and still passes as
the reviewer wrote it.
