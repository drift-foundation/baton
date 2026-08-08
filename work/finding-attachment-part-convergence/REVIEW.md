# Protocol-9 release-gate review

Reviewer: `baton.reviewer`  
Status: **one consequential blocker; polish deferred**

The complete venv suite passes independently: **394 passed**. The core
message-owned convergence works: mixed inline/external delivery, per-message
fail-closed damage, queue skip-and-continue, manifest identity, quarantine,
and schema replacement are coherent.

## Release blocker — non-message external parts bypass integrity

External leaves are accepted for all part owners, including notices and close
dispositions. Publication pins them, but subsequent verification is restricted
to message-owned parts:

- `see` commits the participant receipt for a notice without verifying its
  external leaves; `_notice_delivery` then emits the pin without verification.
- `doctor` verifies external file hashes only for `owner_kind='message'`.
  Damaged external notice and close-disposition parts therefore report healthy.

Independent reproduction on fresh protocol-9 instances:

1. Publish a notice whose Store-level `parts` contains an external leaf, then
   mutate the file.
2. `see` commits a receipt and `_notice_delivery` returns the external part;
   `doctor` reports `ok: true`.
3. Separately, close a claim with a durable external disposition part, mutate
   the file, and observe `doctor` again reports `ok: true`.

This is consequential: receipt and integrity semantics diverge by owner kind,
and a damaged broadcast becomes at-most-once data loss after the seen receipt
commits. Fix before cutover. Either fully verify external leaves for every
owner that accepts them, with the notice receipt committed only for verified
content, or reject external leaves at publication on owner kinds whose damage
lifecycle is deliberately unsupported. Add regressions for the chosen
contract, including notice `wait`/`see` receipt behavior and `doctor`.

## Small correction while touching the path

R4 reappears in attachment-only `send` sugar:

```python
content_type or DEFAULT_ATTACHMENT_TYPE
disposition or DISPOSITION_ATTACHMENT
```

An explicitly empty value is silently defaulted. Use `is None`, and add the
Store-level regression. This is a small validation correction, not the reason
cutover is held.

## Release blocker — the inbox has no human subject

Slawomir identified this during the release-gate discussion and classified it
as a major omission. `kind` is a machine routing label and `thread_id` groups a
conversation; neither is a human-readable subject. A console that lists N
teams' pending questions cannot present a useful triage queue without parsing
the body, and Baton core must not parse Markdown or other content to invent
metadata.

Add a structured plain-text subject in protocol 9 while its authority is still
undeployed, so the human console does not force protocol 10:

- directed messages store and deliver an immutable optional `subject`;
- `scan` exposes it without claiming, enabling queue triage;
- new sends and replies accept `--subject`; a reply with no explicit subject
  inherits the subject of the message being answered;
- reply retry identity compares the effective subject so a changed subject
  cannot wildcard-match an already-committed response;
- validate a supplied subject as non-empty, single-line plain text with a
  bounded UTF-8 byte length and no control characters; Baton does not render
  it;
- notices use the same subject metadata, so the console can label broadcasts
  without consuming their content merely to discover what they concern;
- CLI, Store API, delivery, `scan`/observability, README, protocol document,
  standalone artifact, and regressions move together.

The field may be optional at the protocol boundary so machine/status traffic
does not become ceremony; the console can fall back to `kind` when absent.
What must land now is the schema and lossless surface, because adding that
later would require another fresh-authority protocol bump.

## Deferred polish — does not hold communications

- `config-schema.json` still labels itself “protocol 8” while requiring 9.
- README and code docstrings still mention a separate attachment tuple.
- README says the CLI publishes one part per message although `--body` plus
  `--attach` publishes two.
- General representation text says every leaf has text/base64, while external
  leaves deliberately have `encoding: null` and an attachment pin.

Correct these in the next cleanup, but do not delay service restoration on
their account.
