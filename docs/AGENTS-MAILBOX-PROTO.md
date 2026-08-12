# Baton agent mailbox protocol — v10

An agent coordination channel running **Baton protocol 10** has one SQLite
transactional authority per instance, no filename-state, and is defined
entirely by an explicit config. Consult the Baton distribution's `README.md`
for the command and storage contract.

## Instance selection

    BATON_BIN=/absolute/path/to/baton
    BATON_CONFIG=/absolute/path/to/instance/baton.json
    "$BATON_BIN" --config "$BATON_CONFIG" <command> ...

The config and SQLite authority live outside every participating product
tree. Never copy them into a repository, infer a config from the current
working directory, or omit `--config`. The local deployment supplies the
executable and explicit absolute config path; participating project policy
binds local roles to participant identities without hard-coding host paths.

Participant addresses are `<domain>.<role>`. A domain is a coordination
namespace, not necessarily a Git repository, and roles are open-ended. Each
project binds role-only instructions to concrete addresses in its own policy.

Never consume or claim through another domain's participant, even if a
message looks relevant. Cross-domain work must name the intended scoped
address.

Every identity-bearing invocation passes `--participant <address>`. The
participant address IS the identity: there is no actor and no seed. Filesystem
access to the instance is the trust boundary, so this is cooperative
coordination between trusted agents, not application-level authentication.

Run exactly ONE consumer path per participant. Concurrent `wait`s are harmless
now that waiting writes nothing — what must not be shared is CLAIMING: two
claimers on one address race for the same work and each answers for an
identity the other also speaks as. If two consumers are genuinely needed, give
them distinct participant addresses rather than sharing one identity.

## Working the channel

- Give every substantive message a `--subject`: one line of plain text, at
  most 255 bytes, no control characters. It is what an inbox lists before
  anything is opened, and `scan` shows it. `reply` inherits the subject it
  answers unless you pass your own; retries must repeat the EFFECTIVE subject.
  Status pings may omit it and fall back to `kind`.
- `wait` blocks until work exists and reports it READ-ONLY: channel, message
  id, sender, kind, and whether the head is damaged. It claims nothing and
  writes nothing. Consume with `claim` (directed) or `see` (notice); `claim`
  returns the lossless delivery (claim + envelope + body/attachment). Process a claim
  immediately: `reply` (publishes the response and completes the claim in
  one transaction) or `close` (terminal disposition). Retries are
  effectively-once: an exact retry reports `already_committed`, any
  mismatch fails closed.
- Durable review/response documents: bodies live IN the store; use
  `materialize --participant YOU --dir <finding folder>
  --prefix review|implementation-response` to emit the byte-exact projection
  for humans. The participant is required and the read is authorized against
  the publication-time audience -- you may read back what you sent or were
  addressed in. It also addresses a NOTICE you have already seen, which is the
  way back to a broadcast whose text scrolled past; rereading writes no second
  receipt. Add `--part N` to address a
  specific part of a multipart message (default `0`). Projections are
  caches; the store is the authority.
- Content is TYPED. Every delivery carries `content` with a `content_type`
  and an ordered `parts` list, even for a single part. Each leaf states its
  media type, `disposition`, optional advisory `part_name`, size and hash, and
  carries exactly one representation named by `encoding` — `text` for
  `text/...; charset=utf-8`, `base64` otherwise, never both. Declare
  `--content-type` when publishing anything that is not Markdown; the default
  is `text/markdown; charset=utf-8` and a `text/*` type must state its
  charset. Bytes that contradict the declared charset are refused at
  publication. Baton transports content and never renders it.
- Retries must repeat the WHOLE manifest: the same parts, in the same order,
  with the same media types, dispositions and part names. Identical bytes under
  changed metadata are a different operation and fail closed.
- Evidence files already in the tree travel as EXTERNAL PARTS:
  `--attach ROOT:relative/path` (hash-pinned at publication; mutation fails
  the claim). An external part is an ordinary part — typed, ordered, covered
  by the retry manifest — so it may sit BESIDE an inline `--body` in the same
  message, and a message may carry several. Send the explanation and its
  evidence together rather than as two messages.
- ONE-LINE messages: `--tweet TEXT` on `send` and `reply` makes the text the
  message's subject and publishes no body; `--tweet -` reads the line from
  stdin and drops exactly one trailing newline. It is exclusive with
  `--subject` and every content option, and notices do not have it. An
  explicitly supplied body must contain at least one byte -- a zero-byte part
  claims content exists and is empty, which nobody means. `close` remains the
  contentless disposition.
- One piece of work for SEVERAL participants: repeat `--to`. Each recipient
  gets an independent delivery, claim and disposition sharing one immutable
  content — closing yours resolves nothing for anyone else, and a reply goes
  to the sender, not to the others. `--to` refuses a scope: work addressed to
  `team.*` would have no per-recipient claim, which is what separates a
  directed message from a notice. Your delivery names the whole audience, so
  you can tell shared work from a private request before you start on it.
- Publication is AT-LEAST-ONCE. If a `send` or `send-notice` was interrupted
  after it may have committed, repeat it with `--possible-duplicate`: an
  immutable, sender-supplied warning that YOU could not tell whether the first
  attempt landed. Baton has no token to correlate the two and never claims to
  have proved a duplicate — recipients see what you asserted and decide. Two
  deliberate identical sends are two ordinary sends. `reply` and `close` are
  addressed by `claim_id` and stay effectively-once: retry redelivers the
  committed result or fails closed.
- Broadcasts: `send-notice` (finite TTL), to everyone or to one team with
  `--scope 'team.*'` — QUOTE it, or the shell may expand it. The audience is
  expanded and FROZEN at publication in both cases, so a participant added
  later never acquires an older notice. `see` RECEIVES them; `wait` only
  reports that one is there — a notice wakes a waiter, which reports
  `{"ready": true, "channel": "notice"}` and leaves it unread for `see`. The
  notice is deliberately NOT named: `see` drains oldest-first, so naming one
  would invite consuming a specific notice under another one's name. A
  directed message always wins when both are available. Notices are never claimed, so there is nothing to `reply`
  or `close`; the seen receipt commits with the read, which makes broadcast
  at-most-once per participant. Directed messages remain the durable
  channel for anything that must not be missed. Authors may `expire` early.
- Never mutate the database with raw SQL; every table is guarded and
  doctor treats bypasses as corruption. `doctor`/`scan`/`dump`/`inspect`
  are the read-only views.

## Retention

Transient messages lose their bytes when consumed (identity/hashes
remain); durable messages are permanent. `gc` (any participant) collects
aged transient metadata per `retention_days`; the transition ledger and
audit tables are permanent.

To propose a config change, an administrator writes a valid JSON document at
the same explicit config path with `generation` exactly one greater than the
authority's accepted generation. A participant with the `config` capability
then runs Baton's audited `regen` ceremony. The file is only a proposal until
`regen` accepts it transactionally; while its generation or digest differs
from the accepted state, ordinary operations refuse. If `regen` refuses, the
authority remains unchanged: correct and retry the still-generation+1 proposal
or restore the exact accepted JSON before resuming ordinary work. Never edit
the SQLite authority directly or treat an unaccepted config file as active
state.

Finding-folder workflow policy and concrete deployment identities belong in
the participating project's policy, not in this protocol.

## Conventions

**Recommended practice, not enforced.** Nothing in Baton validates anything in
this section. No error is raised, no message is refused, and no `doctor` check
covers it. An instance whose participants ignore all of it is fully
protocol-conformant; the mailbox is just less pleasant to work in.

They are written down because a convention nobody wrote down is not a
convention -- it is a habit that decays as soon as the next participant
arrives.

Each says what actually happens when it is ignored, so the cost is visible and
anyone can decide it is not worth paying.

**Adding one.** This section is expected to grow. A convention belongs here
when it is a practice that makes the mailbox easier to work in but that Baton
neither enforces nor should. Give it a `###` heading, state the practice, and
state what happens when it is ignored -- that last part is what keeps this
section from turning into a wish list. Anything Baton actually enforces is not
a convention; it belongs in the protocol sections above, where a reader can
expect the authority to back it up.

**A convenience that checks its input is not enforcement.** A convention here
may have a CLI option that helps you follow it, and that option may be strict
about what it accepts. What makes the practice a convention is that nothing
requires you to reach for it: the message is conformant without it, and the
general authoring surface will publish the same leaf unchecked. Reaching for
the convenience is a request to be checked. That is the difference between a
convenience and an alias, and it is why a strict option can sit under a
heading that says "not enforced" without contradicting it.

### File references travel as their own part

When a message refers to or discusses repository files or changes, carry a
REFERENCES leaf in its multipart content.

    content type   text/vnd.baton.references; charset=utf-8
    disposition    inline
    content        one ROOT_ID:RELATIVE/POSIX/PATH per line, ordered by
                   first material mention

    source:baton_core/_impl.py
    source:README.md

Paths here are NAVIGATIONAL METADATA: they say where to look. They are not
copied content and not hash pins. When the sender means "this exact evidence,
immutable", that is an EXTERNAL part, which carries a hash and fails closed
when the bytes change. Those are different promises and should not be
confused -- and that distinction IS enforced, by the manifest.

THE ROOT IDENTIFIER IS PART OF THE ADDRESS. One authority may coordinate
several repositories, so a bare `README.md` does not say which repository owns
it, and a reference that resolves on only one machine is not a reference. Root
IDs are the same ones an external part uses, and follow the same grammar.

The alignment of the two addresses does not collapse their meanings. An
external part resolves the root, reads the file, pins its bytes and may later
fail verification; a reference reads nothing, pins nothing, and does not
require the path to exist. One address vocabulary, two different promises.

Recommended for the relative half: no leading `/`, `..`, home expansion,
backslash separators, empty components, or edge whitespace.

*If ignored:* the reader hunts for the file by hand, or asks. Nothing breaks.
This is the weakest convention here and the most obviously optional.

*Authoring it:* `send`, `send-notice`, `reply` and `close` all take a
repeatable `--references FILE`, which reads one `ROOT_ID:RELATIVE/PATH` per
line. It validates the root against the authority's configured roots and
refuses a relative half that cannot travel — a leading `/`, `..`, `~`, Windows
separators — naming the offending line rather than quietly rewriting it. It
reads nothing from the filesystem and does not require the paths to exist. The
strictness is the convenience, not the convention: a sender who wants an
unchecked references-typed leaf can author one through `--part` and get no
checking at all.

The same four verbs take a repeatable `--part DESCRIPTOR` for the general
case:

    --part 'source=notes.md&type=text/markdown;%20charset=utf-8'
    --part 'source=q3.pdf&type=application/pdf&disposition=attachment&name=Q3.pdf'

Fields are URL-query named, percent-decoded per RFC 3986, and split at the
first `=` so a media type carrying its own `=` travels unencoded. `source` and
`type` are required; `disposition` defaults to `inline`.

Option order is leaf order, across all three content options — `--part`,
`--references` and `--attach` interleave in the order they are written. That
matters beyond presentation: leaf order is part of the manifest digest, and the
manifest is what retry compares. At most one part may read standard input, and
that collision is refused before anything is read.

### One live consumer per active turn

Baton is vendor-neutral and stays that way. There are no Baton-to-model
bridges: the number of adapters would scale with the number of model runners,
and none of them belong in a portable protocol.

- While an agent is actively assigned, keep its turn alive around exactly ONE
  foreground `wait`, and `claim` what it reports in the SAME turn.
- READINESS returns to the live turn; the DELIVERY arrives from the `claim`
  you then make in that same turn. Resolve the claim, re-arm, continue.
- `wait` exits 0 when work exists and 3 when the timeout elapses with nothing.
  A runner loop can branch on the status alone; 3 is idle, not an error.
- Never end a turn holding an unanswered claim.
- A `wait` is safe to leave running; a CLAIM is not. That is the whole reason
  the two are separate verbs.

*If ignored:* the teeth are on `claim`, not on `wait`. Terminal output does
not itself wake an idle agent, so a claim taken by a process whose turn has
ended is stranded -- held, invisible to the sender, and blocking the queue
until someone recovers it. Nothing here prevents that; the protocol correctly
refuses to guess whether a holder is alive.

`wait` used to claim, which put those teeth on the most obvious command in the
tool. Protocol 10 moved them: a missed wake now delays work instead of holding
it. The convention above survives because claiming still has to happen inside
a live turn.

Waking is a RUNNER concern, not protocol behaviour. A future standard runner
signal can improve idle wakeups without changing anything in this document.
