# An external part in a `parts` list defaults to `text/markdown`

`normalize_parts` gives every node whose `content_type` is absent the single
default `DEFAULT_CONTENT_TYPE` — `text/markdown; charset=utf-8`. That is the
right default for an inline authored leaf. It is the wrong one for a node that
carries `attach`, which is by construction a pinned file of unknown type, and
for which the module already defines the correct default one screen away:

    DEFAULT_CONTENT_TYPE    = "text/markdown; charset=utf-8"
    DEFAULT_ATTACHMENT_TYPE = "application/octet-stream"

`DEFAULT_ATTACHMENT_TYPE` is applied only on the `send(..., attach=...)`
convenience path. Nothing applies it inside `normalize_parts`, so the general
parts surface — the one every multipart caller must use — cannot reach it
except by naming the type explicitly.

## What it looks like

Reachable from the library alone, no CLI involved:

    >>> content_spec(None, [{"attach": "r:report.pdf", "disposition": "attachment"}])
    nodes[0]["content_type"] == "text/markdown; charset=utf-8"

    >>> content_spec(None, [{"attach": "r:report.pdf", "disposition": "attachment",
    ...                      "content_type": "application/pdf"}])
    nodes[0]["content_type"] == "application/pdf"        # explicit is honoured

The same call against `baton_v6.py` returns the same wrong type, so this
predates the multipart CLI work and is not a regression introduced by it.

Side by side, the two surfaces disagree about the same file:

    baton send --attach root:two.txt                  ->  application/octet-stream
    baton send --attach root:two.txt --references r    ->  text/markdown; charset=utf-8

The second command differs only by carrying a second leaf, which is what moves
it from the convenience path onto the parts path. Nothing about the attachment
changed.

## Why it matters more than a cosmetic default

A media type on a stored part is not decoration. It is what a reader dispatches
on: the human console decides whether to render a leaf as text, the materialize
path decides what it is writing out, and any future renderer will trust it. A
PDF, a tarball, or a JPEG published as `text/markdown; charset=utf-8` is an
assertion the store makes on the sender's behalf that the sender never made,
and it is recorded in the manifest digest — so it is not correctable after the
fact without republishing.

`README.md` already documents the intended behaviour, under "Inline and
external parts": *"An external part whose type the caller does not declare
gets `application/octet-stream` — the RFC 2046 unknown-bytes type, not a guess
sniffed from the file extension."* The parts path does not do this. So the
defect is a divergence from the documented contract, not merely an unfortunate
default nobody had thought about.

The failure is silent in the direction that matters. Declaring binary content
to be text invites a reader to decode it; the reverse would merely be
unhelpful.

## The correction

`normalize_parts` should choose its default from the node it is normalizing: a
node carrying `attach` and no declared type defaults to
`DEFAULT_ATTACHMENT_TYPE`; an inline node keeps `DEFAULT_CONTENT_TYPE`. An
explicitly declared type continues to win in both cases. That makes the
convenience path's behaviour a consequence of the general rule rather than a
second rule, which is what it should have been.

This touches `_impl.py`, which is measured against `baton_v6.py` by
`test_core_parity.py`.

**The oracle is not moved to make parity pass.** An earlier draft of this
paragraph said landing the fix could mean "moving the oracle in the same
change", which is exactly backwards: editing the reference alongside the
behaviour it measures destroys the measurement and would let any future
divergence through unnoticed. `test_oracle_stays_frozen` exists to prevent
precisely that.

Protocol 10 has two legitimate routes and this correction takes one of them:
either the oracle is RETIRED, because protocol 10 supersedes what it pins, or
the divergence is RECORDED — a named, explained exception asserting that the
core deliberately differs here, in this one respect, for this reason. Which
route applies is a protocol-10 decision, not this finding's.

That is why this is a finding and not a one-line edit: it is a deliberate
behaviour change measured against a frozen artifact, and it belongs with the
protocol 10 work rather than smuggled in beside a CLI feature.

## Short-term stopgap, stated as such

The multipart authoring path in `baton_core/authoring.py` emits an explicit
`content_type` of `application/octet-stream` on the node it builds for
`--attach`, so that the two CLI surfaces agree with each other today.

That is a stopgap and not the fix. It makes one caller stop reaching the bug;
every other caller of the library's parts surface still reaches it, which is
exactly why the correction above has to land regardless. It is recorded here
first, per `AGENTS.md` § "Baton defects and workarounds", because a workaround
that is not written down becomes the specification by default.

## Status

**IMPLEMENTED, 2026-08-10.** This section previously read "Open ... stopgap in
place", which was the opposite of the code by the time anyone read it. A
finding that contradicts the source is worse than no finding: it is a
confident statement that sends the next reader looking for a workaround that
is not there.

What landed:

- `normalize_parts` chooses its default FROM THE NODE. A node carrying
  `attach` with no declared type gets `DEFAULT_ATTACHMENT_TYPE`; an inline
  node keeps `DEFAULT_CONTENT_TYPE`; an explicitly declared type wins in both
  cases. The `send(attach=...)` convenience path's behaviour is now a
  consequence of the general rule rather than a second rule.
- **The stopgap in `baton_core/authoring.py` is REMOVED.** It declared
  `application/octet-stream` itself so the two CLI surfaces would agree; with
  the general rule fixed, leaving it would have masked a regression in that
  rule from every test that goes through the CLI.

The oracle route this finding described is moot: `baton_v6.py` was retired at
the protocol-10 bump, so there is no parity measurement to move or to record a
divergence against. The file remains byte-identical as protocol-9 evidence.

Evidence:

- `test_the_store_defaults_an_untyped_attachment_to_binary` — the correction
  at the layer that owns it, through the general parts surface;
- `test_an_explicit_type_still_wins_over_the_attachment_default`;
- `test_an_inline_leaf_still_defaults_to_markdown` — the fix chooses per node,
  so it must not have moved the inline default with it;
- `test_the_authoring_layer_no_longer_declares_the_attachment_type` — replaces
  the test that pinned the stopgap, whose own docstring said "If that lands
  and this line is removed, this test is what says so out loud";
- `test_the_two_cli_attachment_surfaces_agree_on_the_default_type` — the same
  property, measured after normalization, which is where the type is now
  decided.

Break-checked: reverting the node-based default fails the first and the last
of those by name.
