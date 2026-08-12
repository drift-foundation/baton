# Plan — deployment recipe

Ordered so that every step that needs a human decision reaches one before code
is written against a guess.

**Current scheduling — 2026-08-11:** payload correction, independent review,
and a non-activated versioned 1.1 candidate publish are release gates for
Slawomir's soak. Stable activation, permanent destination design, and
production documentation remain deferred to the next major release. The human
chooses the candidate `DEST`; do not hard-code a mailbox or repository path.

1. **Pin the direction as a finding** — completed 2026-08-11.
2. **Propose the concrete destination layout** — completed 2026-08-11, below,
   at Slawomir's instruction. The remaining version and example-payload choices
   were both ruled later the same day.
3. **Write the recipe as a tool, not a shell incantation** — **done and source
   signed off 2026-08-11**. Implements exact `just deploy DEST VERSION`, ruled
   example/dynamic-release-note payload, complete manifest preflight, staged
   atomic no-replace publication, and no-follow/read-only destination safety
   from `review-2026-08-11T16-55-31Z.md`.
4. **Add a `verify` mode over a deployed tree** — **done and source signed off
   2026-08-11**, including manifest-pinned protocol verification, protocol
   agreement, regular/no-symlink entries/root, exact permissions, recursive
   fsync, and activation no-disturbance.
5. **Deploy the current 1.0.0 release as the production baseline** — deferred
   to next-major permanent-deployment design.
6. **Publish the 1.1 candidate for Slawomir's soak** — required after source,
   artifact, payload, and independent-review gates. Use `just deploy DEST
   1.1.0`; do not activate a stable pointer.
7. **Document both in the README and the effective-use guide** — pending, and
   deliberately last: the paths a team is told to use must not be written down
   until they exist and verify.
8. **Independent review and human trial** — review the recipe before the
   candidate publish; Slawomir then runs the deployed tree for a soak and
   separately clears the release.
9. **Re-review changes requested 2026-08-11**: replace cooperative
   check-plus-rename with a true atomic no-replace publication; create and
   clean only genuinely owned staging even after hardening; make `verify`
   enforce root/no-symlink and exact-mode rules; and fsync final metadata plus
   every nested directory entry. Add the boundary regressions required by
   `review-2026-08-11T19-27-39Z.md` and return once for re-review. Do not deploy
   or activate anything.
10. **Source review signed off 2026-08-11** in
    `review-2026-08-11T19-35-31Z.md`. Actual 1.1 candidate publication,
    deployed-path verification, and human soak remain steps 6 and 8 after
    coherent release artifacts/manifests exist.

---

## The proposed layout

    <deploy-root>/                     e.g. /opt/baton, or ~/baton
      current -> v1.0.0                the stable path teams point at
      v1.0.0/                          one immutable directory per release
        bin/baton
        bin/baton-tui
        docs/AGENTS-MAILBOX-PROTO.md
        docs/EFFECTIVE-BATON.md
        docs/RELEASE-1.0.0.md
        dist/DISTRIBUTION.json
        dist/DISTRIBUTION-TUI.json
        examples/baton.json
        README.md
        LICENSE
        DEPLOYMENT.json
      v<next>/                         a beta lives beside it, with no pointer
        bin/baton
        bin/baton-tui
        …

Teams use `<deploy-root>/current/bin/baton`. Beta testers use the versioned
path directly, which is what keeps a beta opt-in: there is no way to reach it
by accident from the stable path.

### Why this shape

**A version directory is immutable and the recipe refuses to overwrite one.**
This is the property everything else rests on. If a deployed version can be
rewritten in place, then "teams keep pointing at a stable path" is a hope
rather than a fact, and no verification result means anything five minutes
after it is taken. Replacing a bad deployment is a human act — delete the
directory deliberately, then deploy again — not a flag.

**`current` is the only mutable thing in the tree, and switching it IS the
release.** A symlink swapped by rename is atomic: no reader ever observes a
half-switched deployment, and rollback is the same operation pointed
backwards. That is worth more than it costs, because the alternative — copying
a new release over the stable path — has a window in which the tree is neither
version.

**No timestamps inside the tree.** A deployed tree is then byte-reproducible
from the same release, so `verify` can be exact rather than approximate, and
two people deploying 1.0.0 get identical trees. The filesystem already records
when. `DEPLOYMENT.json` therefore holds only facts about WHAT was deployed:
release version, protocol version, and every deployed file with its SHA-256.

**Deploy copies certified bytes; it never builds.** The recipe reads `bin/`
and `dist/` as they are and refuses to deploy a tree whose artifacts do not
match their own manifests. A deployment is then the last link in the release
gate's chain rather than a second, weaker way to produce artifacts — and an
uncertified working tree cannot be deployed by accident, which is exactly the
state this repository is in right now.

**The authority is never part of a deployment.** The ruled example config is a
template, not accepted instance state: no live config, no SQLite, none created,
none discovered. A deployed tree is inert until a participant supplies an
explicit external `--config`. Next-gen's development authority is created
separately by whoever runs the beta.

**Superseded:** the earlier proposal gave a beta a distinct executable name as
well as a distinct path. Slawomir ruled on 2026-08-11 that binaries keep the
same names under every `v<version>/` tree. The complete identity is the
versioned path plus the version the executable reports; beta isolation also
requires its separate development authority/config and no `current` pointer.

### Contents, and what is deliberately excluded

Included: both executables, both manifests, the protocol document, the
effective-use guide, the release announcement, README, LICENSE, and
`examples/baton.json`.

Excluded: `src/`, `tests/`, `tools/`, `work/`, other `examples/`, `schema/`,
`compat/`, `justfile`, `AGENTS.md`. A deployment is what a consumer runs and
reads, not what a developer needs — and `AGENTS.md` in particular is this
repository's own policy, not a deployed artifact.

**Superseded 2026-08-11:** the earlier proposal excluded
`examples/baton.json` because a shipped config might be mistaken for an active
authority. Slawomir ruled that it ships. It is a template only: deployment
still carries no SQLite store, does no config discovery, and activates no
authority.

### Interfaces

    just deploy DEST VERSION          copy a certified release to DEST/vVERSION
    just deploy-activate DEST VERSION point DEST/current at it, atomically
    just verify-deployment DIR        re-hash every file against DEPLOYMENT.json

Deploying and activating are SEPARATE commands on purpose. Putting bytes on
disk is safe and reversible; changing what every team runs is neither, and one
command that does both would make the safe half impossible to do alone.

### Ruled release identity

The next version is **1.1.0**. The candidate destination is therefore
`<deploy-root>/v1.1.0/`, still with no `current` pointer until the separate
human activation decision.
