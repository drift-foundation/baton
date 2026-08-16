# Progress

Owner: `baton.implementer` only.

## 2026-08-10 — implemented, revalidated against this contract

State: **complete, pending review**.

Implementation: `_tweet_subject` in `baton_core/_impl.py`, wired into the
`send` and `reply` dispatch. `--tweet` on those two verbs only.

Revalidated line by line against the contract above:

- value becomes the subject, publication uses the parent's contentless
  representation — yes, `CONTENTLESS_CONTAINER` with no part rows;
- kind/outcome/retention/audience/claim/reply/close/retry/thread unchanged —
  yes, and pinned by `test_the_stored_message_keeps_its_caller_supplied_kind`;
- `--tweet -` reads UTF-8, removes exactly ONE terminal LF or CRLF, then the
  ordinary subject validator — yes, CRLF checked before LF so no CR survives
  to fail as a control character;
- every refusal class fails before publication — yes, parametrised over empty,
  bare newline, multiline, tab, invalid UTF-8 and leading whitespace, each
  asserting nothing was published;
- mutual exclusion in BOTH argument orders — yes. This was the one gap found
  while revalidating: the test covered `--tweet` first only. Both orders now.
- implicit stdin preserved without `--tweet`, explicit body still needs a
  byte, notices unchanged — yes.

Evidence 1-7:

1. direct and packaged CLI, send and reply;
2. packaged stdin LF and CRLF;
3. every refusal, no publication;
4. every exclusion, both orders;
5. preserved implicit stdin, unchanged notice refusal;
6. subjects and content type read back through `dump` in the packaged test;
7. README and `--help` updated; packaged tests run the built artifact.

Break-checked: exclusivity, the one-terminator trim, the empty refusal and the
stdin bypass each fail named tests when removed.

Deleted during implementation: a `validate_subject` call inside the helper.
The break check showed removing it failed nothing, because every refusal
already arrives from the store — a second gate on one property is a second
thing to keep in agreement, not extra safety.

## 2026-08-10 — corrected after review R1

State: **corrected, pending re-review**.

The exclusivity check was reading namespace attributes only.
`--part`, `--references` and `--attach` have none: `authoring_opts` collects
all three into one ordered `ns.content` list so leaf order is the order the
human typed. Three of the eight checks were therefore permanently false, and
`--tweet x --attach root:file` exited ZERO while discarding the attachment.

That is the same class of defect as the earlier `--body` loss, and I
reintroduced it: I wrote a list of option names without checking that the
options were stored the way the list assumed.

Corrected: `_tweet_conflicts` reads BOTH shapes and names the actual flags in
the diagnostic. `_TWEET_EXCLUSIVE` now carries only the attribute-backed
options, with a comment saying why the other three are absent, so the next
reader does not "fix" it by adding them back.

Added evidence:

- `test_a_tweet_refuses_the_shared_list_options_too`, all three options, both
  argument orders, asserting nothing was published. `missing:nowhere` proves
  refusal happens before anything is read, resolved or pinned;
- `test_reply_refuses_the_same_combinations` — `reply` has its own dispatch
  and was an assumed caller;
- a packaged-artifact pin for `--attach`, because the executable is the
  public surface and is where this defect actually mattered.

Break-checked: removing the shared-list read fails four tests by name.
