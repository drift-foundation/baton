# Plan: supported Google-agent ACP trial

**Status — split pending, then close.** Antigravity is postponed until Google
offers supported ACP. Gemini remains approved as the explicit `impl2` route;
its implementation is moving to a separately bound Work. Close W163 only after
that Work exists, so the approved continuation cannot be lost.

1. [done] Inspect the installed `agy` version and local command surface.
2. [done] Verify native ACP status and the OAuth integration boundary against
   Google's current primary sources.
3. [done] Slawomir selected, installed, and authenticated the official Gemini
   CLI; `gemini` 0.55.1 advertises native `--acp` plus policy controls.
4. [ready] Extend the one visible `baton.impl` kind with a configured allowed
   route set and deterministic default. Add per-handoff `route=...` selection,
   recording the selected route authoritatively; default omission to the
   existing `impl` route and reject routes not allowed by the kind or required
   role. The model permits any number of backup routes.
5. [pending] Add isolated participant `baton.gemini`, holding the existing
   `impl` role. Retain `impl` with sole handler Claude and configure `impl2`
   with sole handler Gemini; keep `impl` the default. Add a separate bridge
   session/state directory and Gemini-side deny policy. Do not route ordinary
   production Work to `impl2` during the canary.
6. [pending] Prove initialize, authentication, session creation/load,
   permission mode, hard-denial policy, one Baton wake, one claim/pass cycle,
   explicit `route=impl2` selection, default `impl` selection, restart
   continuity, cancellation, and clean shutdown.
7. [pending] Record whether the canary is certified, rejected, or parked for a
   future native `agy --acp` release.
8. [pending] Accept the configuration generation retaining `baton.impl` as
   the sole visible kind, with default route `impl` and backup `impl2` (while
   allowing later `impl3`+ routes). Restart the independent ACP launchers and
   prove one explicit
   assignment through each route without exposing both candidates on a Work.
