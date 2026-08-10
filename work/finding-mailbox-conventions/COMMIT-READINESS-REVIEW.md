# Stage 1B commit-readiness review

**Outcome:** approved after R1/R2 correction. The packed four-verb help test
passes and the proposed commit message now records all four TUI corrections.

## R1 — `--references` help teaches the superseded address form

The proposed commit message correctly says reference lines are root-qualified
`ROOT_ID:RELATIVE/PATH`. The built executable's help for all four authoring
verbs currently says:

```text
--references FILE  file of repository-relative POSIX paths, one per line
```

That is the pre-ruling form. There is no single implicit repository root in a
multi-root authority, and the strict parser now rejects those bare paths. A
fresh user following `--help` is therefore instructed to produce invalid
input.

Update the shared help text to the exact root-qualified contract (for example,
“file of `ROOT_ID:RELATIVE/POSIX/PATH` references, one per line”). Pin every
verb's rendered help or the shared source plus a coverage assertion that all
four use it. Rebuild the executable/zipapp and distribution manifests after
the user-facing text changes.

## R2 — the commit message omits the fourth TUI correction

The title and body say “three ruled TUI corrections” and enumerate focus
return, simplified headers, and retained drafts. The same candidate also
implements the corrected subject rule: the TUI trims subject edge whitespace
at send while the shared core and agent CLI retain strict refusal.

Call these **four** ruled TUI corrections and state the subject split. It is
important release behavior and the reason subject normalization was explicitly
removed from the protocol-10 bundle. Do not imply that the core or CLI trims.

The recommendation to keep Stage 1B and these TUI corrections in one boundary
commit is otherwise accepted: splitting would require separate deterministic
artifact rebuilds and manifests at each boundary.

## Final-message review after R6 and the live state-sync correction

**Outcome:** one wording revision requested; verification evidence accepted.

The final status evidence is coherent: edits stopped, fresh `just test` reports
2081 passing, diff hygiene is clean, both built artifact hashes match their
manifests, protocol remains 9/tool 5.2.0, and the frozen 5.1.0 oracle hash is
unchanged.

The proposed title/body now undercounts its own TUI scope. It calls the bundle
“five ruled TUI corrections,” enumerates focus return, header simplification,
TUI-only subject trimming, retained drafts, and live detail-state sync, then
adds the separately ruled completed/damaged glyph correction. Avoid another
fragile count: describe these as the TUI trial corrections or explicitly name
the glyph safety in the title.

The closing “Findings recorded, not fixed here” paragraph is also no longer a
faithful summary of the files this commit adds/changes. Since its prior draft,
the repository gained the ruled bulk-selection/recoverable-Trash contract, the
extensible reaction vocabulary (`+`, `-`, `:pin` / `{pin}`), and live evidence
for participant-authorized notice reread. Either mention those protocol-10
findings, or make the paragraph explicitly non-exhaustive and point to the
protocol-10 umbrella; do not present a three-item list as though it accounts
for all deferred work in the commit.

No code, test, artifact, or version change is requested. The stale screenshot
remains an explicit user-owned capture decision and must not be silently called
current in the message.
