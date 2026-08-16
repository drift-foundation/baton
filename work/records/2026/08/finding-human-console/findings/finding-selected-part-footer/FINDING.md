# Selected-part metadata belongs in a fixed DETAIL footer

Status: **ruled; ready for implementation**.

Parent: `work/records/2026/08/finding-human-console/`.

Discovery context: live TUI reading showed transport metadata occupying the
first line before the message body while omitting the immediately useful total
part count.

## Finding

The first line a reader reaches before ordinary message text is currently:

    ▸ [0] text/markdown; charset=utf-8  inline

`[0]` is the manifest address, not a part name. The line promotes transport
metadata over the message and forces the common single-part reader to skip it.
At the same time it does not state the total number of parts, so it is noisy
without answering the multipart question a human actually has.

Moving the line after all scrollback would still hide it below a long first
part. Slawomir approved a persistent bottom-of-DETAIL footer instead.

## Required contract

- Scrolling body content begins where the leading part header used to be. A
  single-part text message presents its text before transport metadata.
- One fixed footer row at the bottom of DETAIL shows the selected part:

      ▸ [0] text/markdown; charset=utf-8  inline  (1/1 parts)

- The footer remains visible while body content scrolls vertically or
  horizontally and while the list/detail focus changes.
- `[address]` is the part address. If `part_name` exists, display it separately
  and unambiguously; never call the address a name.
- `[`/`]` update the selected part and `(N/TOTAL parts)`, and bring that
  part's content into the viewport without moving list selection or writing
  authority state.
- Multipart content retains a quiet visual boundary between bodies, but does
  not repeat the full media/disposition line before every body.
- A contentless subject-only message shows `0 parts` and never manufactures
  `[0]`.
- The footer consumes one DETAIL row. Layout, page size, overflow indicators,
  navigation, and resize calculations account for it. It never replaces or
  displaces the global status bar.
- Narrow terminals truncate safely by display cells and preserve the part
  count when possible; no control/wide-cell regression.
- This is presentation only: no core, protocol, schema, manifest, delivery,
  receipt, claim, or materialize semantics change.

## Required evidence

1. Single-part body text precedes metadata and the fixed footer says `1/1`.
2. Long body scrolling leaves the footer fixed.
3. Two inline text parts remain visually distinct; `[`/`]` updates footer and
   viewport to `1/2` and `2/2`.
4. Mixed inline/external and named/unnamed parts render honest metadata.
5. Contentless messages show `0 parts` with no fabricated address.
6. DETAIL height/page/end calculations, narrow width, Unicode, resize, and
   focus toggles preserve the footer and status bar.
7. Pure renderer/state tests plus a packaged PTY screenshot/replay test.
