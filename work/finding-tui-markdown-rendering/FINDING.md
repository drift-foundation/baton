# Finding: safe Markdown rendering in `baton-tui`

Status: deferred from the human-console trial; not part of the current
wrap/layout/recipient-picker correction.

Raised by Slawomir during the `baton-tui` human trial on 2026-08-08.

## Problem

Protocol messages already declare `text/markdown; charset=utf-8`. The console
displays that content as sanitized plain source, which **contradicts the
declared type**.

A media type is a statement about how content is meant to be interpreted. A
sender who declares `text/markdown` is asking for Markdown; a sender who wants
no interpretation already has `text/plain`, and one who wants markup has
`text/html`. The protocol therefore already gives every party the raw-versus-
rendered choice, and it is the SENDER's choice — a console that always shows
source silently overrides it, and one that always renders would override the
`text/plain` sender in the other direction.

So "safe because it interprets nothing" was the wrong justification for the
current behaviour. The correct reason to ship source-only first was that no
renderer existed yet. Interpreting a declared type is the contract, not a
hazard; the hazard is interpreting it as something it did not declare.

This is not folded into the current wrapping fix. A renderer must share the
same display-cell-aware wrapping, viewport and hostile-text rules; a quick
second formatting path would reintroduce clipped text, divider drift or escape
sequence injection.

## Pinned direction

- Dispatch from the declared media type, and honour it as the DEFAULT.
  `text/markdown` renders by default; `text/plain` stays literal; unsupported
  types keep the existing honest summary/fallback. Defaulting Markdown to
  source would override a choice the sender already made.
- Source view is always available on demand, and byte content is never
  silently dropped. Rendering is presentation, so the exact bytes must remain
  reachable.
- **Interpret the declared type, never a different one.** `text/markdown`
  means Markdown, so raw HTML embedded in it (which CommonMark permits) stays
  inert text — a sender wanting markup declares `text/html`. This is the line
  that matters: presentation is the contract, executing or fetching is not.
- Rendering never executes or fetches anything. Inline HTML is inert text;
  links are displayed but never opened automatically; images and remote
  resources are not fetched.
- Markdown syntax, untrusted content and terminal control handling remain
  separate concerns: sanitize hostile controls first, parse structure without
  executing it, then wrap/style by terminal display cells.
- Headings, paragraphs, lists, blockquotes, fenced/inline code, emphasis and
  links need explicit behavior. Code preserves meaningful whitespace while
  remaining horizontally visible through wrapping or a deliberate code-block
  viewport contract.
- Styling must use semantic spans with text fallbacks, not colour alone, and
  must coexist with inbox selection highlighting and the persistent status
  bar.
- Resize and J/K scrolling operate over the final rendered visual lines.
- Any new runtime dependency belongs only to the independently shipped TUI;
  it must never enter or enlarge the agent CLI artifact. The existing
  stdlib-only rule may be revisited only with evidence that a correct small
  parser is riskier than the dependency.

## Decided: what happens to a type this console cannot render

Slawomir, directly: *"when we encounter a mime that we cannot render (pdf,
image, etc) we just offer to show raw (if it's text-based encoding) or save to
file."*

The declared type still selects the contract; when the console cannot honour
that contract it says so rather than approximating it.

- **Renderable** (`text/markdown` today, `text/plain` always): presented as
  the type asks, with an explicit source view.
- **Unrenderable but text-based** (`encoding: text` — the typed envelope
  already decided this by declared type, not by sniffing): offer **show raw**.
  The bytes are legible; withholding them helps nobody.
- **Unrenderable and binary** (`encoding: base64`): offer **save to file**
  only, through the existing `m` materialize path. There is no raw view to
  offer, and dumping base64 or decoded binary into a terminal is how a
  console emits control sequences it never parsed.
- The offer is **stated in the pane**, not implied: the part header says which
  of the two is available, so an unrenderable part reads as a deliberate
  outcome rather than a blank pane.

This decides `text/html` too, and it needs no separate ruling: this console
has no HTML renderer, so `text/html` is unrenderable-but-text-based and gets
the raw view. A tag-stripping half-renderer was the other candidate and is
rejected — it would silently discard structure the sender declared as
meaningful, which is the failure the typed envelope exists to prevent. If an
HTML renderer is ever written, `text/html` moves into the renderable row by
that decision, not by drift.

**Not decided here:** whether a `text/markdown` part may be saved to file as
well as rendered. Rendering and saving are not exclusive, but adding a save
path for renderable parts is scope beyond this finding.

## Decided: overlong unbroken content is elided, not fractured

Slawomir's ruling, applying to READ-ONLY detail content and headers: wrap at
whitespace; if one token is wider than the whole pane, do not fracture it
across rows -- show the fitting prefix ending with U+2026 so the hidden part
is explicit. The underlying bytes are untouched; this is presentation.

Fracturing a 200-character token across four rows produces four rows of
nothing readable, and pushes the rest of the message off the pane. An
ellipsis at least says what happened.

**Editable text is exempt and must stay lossless.** Hiding characters someone
is currently typing is a different and worse fault than hiding characters they
are reading, so reply and compose keep the full-fidelity wrap and keep the
active tail and caret visible. Picker addresses are exempt for a different
reason: two accounts differing only in their tail would render identically,
and the picker exists to prevent exactly that mistake.

Horizontal panning of clipped detail lines is the obvious follow-up and is
explicitly deferred.

## Acceptance evidence

- Common Markdown fixtures cover nested lists, headings, blockquotes, fenced
  code, long links, long unbroken tokens, explicit blank lines, CJK and
  combining characters.
- Hostile ESC/C0/C1/bidi input cannot reach the terminal as an active control.
- Every rendered line respects the detail-pane display width at representative
  terminal sizes; resize reflows without losing text and scrolling reaches the
  last visual line.
- Rendered/source toggling creates no claim, notice receipt, disposition or
  other authority write.
- Built-artifact tests prove the CLI contains no Markdown renderer or TUI-only
  dependency.

## Decided: what a part header shows

Every leaf header carries manifest address, declared media type, disposition
and the advisory filename:

    [1] image/png  attachment  diagram.png

The filename is a **display label only, never a path**. `m` keeps writing to
its own generated destination, because a sender-supplied name is
sender-controlled input and a console that turned it into a path would be
writing wherever the sender chose.

Two independent defences cover a hostile filename, and neither is the only
one:

1. The authority refuses a filename containing control characters at
   publication, so one cannot enter the mailbox through `send`.
2. Every rendered row is sanitized regardless, so a filename arriving by any
   other route reaches the terminal as visible text (`bell<U+0007>.bin`)
   rather than as an active control.
