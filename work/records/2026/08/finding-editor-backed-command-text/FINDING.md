# Finding: free-form command text needs an external editor

## Status

Confirmed design direction from Slawomir during the projection-11 v11 trial
on 2026-08-18. This is separate from
`work/records/2026/08/finding-command-buffer-cursor-editing/`: cursor editing
serves small corrections, while this Work serves substantial prose.

## Problem

Several operations require human prose—`body`, `comment`, `rationale`, and
similar description fields. Quoting and editing that material inside the
single-row `:` command bar is costly, fragile, and unsuitable for paragraphs.
Command completion reduces spelling mistakes but does not make prose authoring
comfortable.

## Confirmed requirement

The TUI should be able to open the user's configured external editor for a
free-form text operand. It must never present an unexplained empty file. The
temporary document begins with Git-commit-style comment guidance that names:

- the Baton operation and field being authored;
- the selected Work or Thread and its title when context supplies them;
- how to save, cancel, and distinguish instructional comments from submitted
  content.

The explanatory header is presentation scaffolding and is not submitted as
the operand value.

## Confirmed invocation

Enter first parses the command far enough to identify its operation and
operands. When an editor-capable REQUIRED prose operand such as `body=`,
`rationale=`, or `comment=` is already present, Baton does nothing special and
executes the command normally. When that operand is absent, Enter opens the
contextual editor instead of returning the ordinary missing-operand refusal.

Saving supplies that one missing value and resumes the same canonical command
execution path. Cancelling returns to the intact command draft without
submission. There is no editor token in the command grammar, no extra command,
and no key chord to remember. Grammar metadata—not a separate hard-coded verb
list—identifies which required prose operand has this behavior. A missing
non-prose operand still refuses normally.

## Remaining proposed interaction

- Invoke an argument-vector editor resolved from the conventional environment,
  without shell evaluation. The exact `$VISUAL`/`$EDITOR` precedence and
  fallback remain to be ruled.
- Create the draft with mode `0600`. On successful editor exit, remove only
  the known leading instructional block and preserve the authored UTF-8 body.
- A nonzero editor exit or an unchanged/empty authored region cancels safely
  and leaves the command available for correction rather than submitting an
  invisible empty value.
- Submission still traverses the existing parser and canonical operation path;
  the audit record contains the exact authored value.

## Open decisions

1. `$VISUAL` versus `$EDITOR` precedence and behavior when neither is set.
2. Whether command history stores the complete authored value, a safe
   placeholder, or only the surrounding command.
3. The exact cancellation rule for an unchanged template versus deliberately
   empty text on operations that permit it.

## 2026-08-18 remaining editor policy — approved

The following ruling closes and supersedes every open decision above:

- Resolve the `EDITOR` environment variable only. Parse it into an argument
  vector without invoking a shell. If it is unset, malformed, cannot be
  launched, or exits unsuccessfully, retain the intact command draft and
  report the refusal; never silently choose an editor.
- A successful save with authored content immediately resumes and submits the
  original command through its canonical execution path. An unchanged
  template or empty authored region cancels without submission and restores
  the command draft.
- Session history stores the surrounding command without generated prose.
  Recalling and submitting it therefore opens a fresh contextual editor rather
  than retaining a potentially large or stale body. The authority event and
  operation record still receive the exact text that was actually submitted.
- Remove only Baton's generated leading instructional block. User-authored
  comment-looking lines elsewhere in the document remain content.

This is a TUI authoring facility, not new CLI grammar. A caller that explicitly
supplies the prose operand never invokes the editor.

## Acceptance boundary

- Contextual guidance makes an opened editor self-explanatory.
- Instructional text can never leak into the submitted body.
- Quotes, newlines, Unicode, lines beginning with comment characters, and a
  body larger than the terminal viewport round-trip byte-for-byte after the
  documented normalization.
- Editor invocation performs no authority mutation; only the final explicit
  submission does.
- Failed launch, nonzero exit, interruption, and empty/unchanged drafts fail
  safely without destroying the command draft.
- Tests use a deterministic fake editor and cover argument safety, temporary
  file permissions and cleanup, context seeding, cancellation, and canonical
  submission.

## 2026-08-19 implementation-review clarification

The editor opens only when the required prose operand is the **sole remaining
missing operand**. If another required operand is also absent, the ordinary
parser refusal names the incomplete command before the operator spends time
authoring prose that cannot yet submit. This preserves existing incomplete-
command behavior and still satisfies the confirmed automatic editor contract
once the surrounding operation is complete.

An interrupt delivered while the foreground editor is running is a safe
cancellation, just like an unsuccessful editor exit: clean the private draft,
restore the intact command and caret, report that editing was interrupted, and
perform no authority mutation. It must not escape and terminate the TUI.
