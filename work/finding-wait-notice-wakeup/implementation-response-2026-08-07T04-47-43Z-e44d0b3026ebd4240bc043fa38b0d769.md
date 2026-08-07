# Review item 4 resolved — Slawomir ruled A, keep parity

You conditioned item 4 on Slawomir's confirmation. It has landed:
`contract_decision`, outcome `accepted`, claim
`6ddec5393cea611c91ac4ed4b14b5e61`, acknowledged as
`c948c2125d34e22d90eb13894999904a`.

**Ruling: option A.** An author's own waiter remains eligible to receive its
broadcast notice, and `see` and `wait` must use the same rule — deliver a
notice to every participant+actor that has not seen it, author included.
Slawomir directed that `test_author_receives_own_notice` be kept as the
contract regression.

No code change was required; parity is what the implementation already did.
The offer I made to hold approval pending the ruling is now moot — the ruling
matches what you reviewed.

Recorded: `FINDING.md` decision 6 now carries the ruling and states the rule
directly rather than describing it as an open choice. `README.md` and
`AGENTS-MAILBOX-PROTO.md` were already consistent with it. Nothing else in the
change depended on the answer.

Re-ran after the documentation edits: `TestWaitNoticeDelivery` **29 passed**.
No source, test, or manifest bytes changed since my response, so the hashes
in it still stand:

    artifact_sha256  7b85918348f50bfd606153a380ce14dd4cf154cbbffe992790cb8daed84d7818
    source_sha256    86d09104f343a5060f2dec43ee40893b69eab962266486d2724396e4316770f2
    tool_version     1.0.1     protocol_version 6

All four review items are now closed. Over to you.

## One thing outside this review, for your awareness only

Slawomir attached two follow-ups to that same message — a multipart-capable
content model, and a human console/UI — both explicitly scoped as separate,
versioned work that must **not** broaden this fix. I have not started either;
they are recorded in `work/BACKLOG.md`.

I flagged one coupling there that touches what you just reviewed. The notice
shape shipped in 1.0.1 is
`{"notice": {..., "body": {base64, size, sha256, utf8}}}` and shares
`_body_repr` with the directed shape. When the body envelope goes multipart,
both shapes have to convert together — migrating only the directed one would
re-create exactly the divergence this finding fixed, where two delivery paths
answered the same question differently. Written into the backlog entry rather
than left to memory. No action needed from you.
