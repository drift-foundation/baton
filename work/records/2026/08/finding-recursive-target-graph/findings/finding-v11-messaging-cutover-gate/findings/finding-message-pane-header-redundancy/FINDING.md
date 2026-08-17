# Finding: the split message panes repeat their selected context

## Parent

`finding-v11-messaging-cutover-gate` — observed during the live v11 TUI trial
on W163.

## Observed

The Work detail screen already presents the selected Thread and its subject:

```text
Threads (1):
  T1 Drive Claude and Gemini through one ACP readiness client ...
```

The split message area then repeats a truncated copy of that subject and the
selected message identifier in its shared heading:

```text
Msgs — Drive Claude and Gemini th  »M163
```

The message list identifies and highlights M163 again, while the detail pane
starts with `#163`. The repeated subject and identifier consume scarce width,
truncate useful text and do not explain the two panes.

## Decision — 2026-08-16

The split-area headings identify pane roles, not content already visible in
the selected Thread and Message rows:

```text
Threads (1):
  T1 Drive Claude and Gemini through one ACP readiness client

Messages (1)                         Message M163
```

- The Thread row remains the owner of the discussion subject.
- The left message row remains the owner of selection highlighting.
- The detail heading identifies the selected message once as `Message M…`.
- Remove the truncated subject and `»M…` treatment from the shared message
  heading.
- Reserve one blank separator row between the Thread list and the lower
  Messages/Message panes. Spacing, not a border or repeated label, separates
  the two navigation levels.
- Preserve useful counts and degrade the two labels cleanly at narrow widths;
  do not recover space by merging message metadata back into the body.

## Acceptance

- Wide and narrow virtual-screen tests pin the Thread, Messages-list and
  selected-Message headings as distinct regions.
- The lower panes begin after exactly one blank separator row beneath the
  Thread list.
- Long and wide-character subjects cannot leak into or distort the lower pane
  headings.
- Selection remains visible in the message list and changes the detail
  heading/body together.
- Empty, one-message and multi-message Threads render honest counts without
  duplicated identifiers or subjects.
