# What run5 and run6 establish, and the honest size of the conclusion

`baton.claude`, implementer, 2026-08-31. No credential byte was opened or
recorded by anything below.

## The measurements

**Both attempts resolved cleanly.** `resolved: true`, `unresolved: []`,
`cleanup {retained, absent}`, 18 committed operations each from `offer.issue`
through `runtime.destroy`, conversation `answered` on `describe` and `work`.
The retained-review platform is unchanged and still works; that is the third
consecutive round in which it has.

**Both provider turns did not happen.** `provider-failed`, status 1, zero-byte
`change.patch`, `no verification was attempted`, and a candidate whose four
files are byte-identical to the frozen delivery. The frozen command rerun
outside the worker gives 26 tests, OK, in both retained trees.

**The image is exonerated.** `evidence/w51487-run6/image-control.md`: run4's
own artefact, replayed under wholly fresh identities, fails identically.

**The delivery is exonerated.** Both attempts report
`source_tree_digest: sha256:9e70c7337c…` — the same staged tree as the dry
revalidation, run2, run3 and run4 — and the four staged files still hash to
the frozen digests after each run.

**The credential is readable and the provider launched.** W52800's correction
is what makes this sayable. `_prepared_home` now raises `TaskRefusal` for a
slot this identity cannot open, and a refusal is not `provider-failed`; the
disposition we actually got is only reachable after the provider process ran.
That is the run3 cause and it is not this one.

**The staged credential source is byte-unchanged since run4 succeeded.**
Metadata only: `/run/baton/credentials/claude` is still a regular 509-byte
`0400 sl:sl` file whose mtime is 2026-08-31 09:06:32Z — before run4's 16:33Z
attempt, not after it. The host source it was copied from,
`/home/sl/.claude/.credentials.json`, has an mtime of 2026-08-28 03:59Z and
has not been rewritten since.

## Credential-free probes, in the exact posture

Run in the run5 image as uid 65532, read-only root, `--network bridge`,
nothing of the operator's mounted.

    1. no credential at all
       claude --print --permission-mode acceptEdits 'hi'
       -> EXIT 1, "Not logged in · Please run /login"

    2. egress
       dns api.anthropic.com -> 160.79.104.10
       tcp 443              -> connected

    3. a credentials document I INVENTED, mounted and symlinked exactly as the
       adapter does
       -> EXIT 1, "Not logged in · Please run /login"

So the CLI is present and functional, this is not a network fault and not
W17110's TLS trust-store defect, and the delivery mechanics reach the provider.

## The conclusion, and what it is not

Everything the deployment owns is proven good: task, delivery, image, network,
posture, retention, arc, and now credential READABILITY. What changed between
run4's success at 16:33Z and run5's failure at 17:20Z is not any of them.

**The leading inference — labelled as one — is that the staged credential
SNAPSHOT stopped being accepted somewhere between 16:35Z and 17:20Z.** It is a
copy taken at 09:06Z of a document the provider normally refreshes in place;
this one is delivered read-only into a container that cannot write a refresh
back, so a snapshot with an expiry eventually stops working while its bytes
never change. That fits every measurement above and explains why the same
bytes worked at 16:33Z and not at 17:20Z.

**It is not proven, and a second explanation fits equally well:** an
account-level refusal such as a usage limit, which also exits 1 at the same
instant in the same shape. **I cannot tell these apart from outside**, because
the provider's own diagnostic is deliberately unpublished — the process that
wrote it holds the attempt's bearer.

That inability is the run2 P1 finding arriving a second time, and it has now
cost two rounds. It belongs to `claude_agent` rather than to this Work, and it
is restated in the round's acceptance record rather than taken here.

Deciding between the two explanations needs the operator, who owns the source:
either refresh the staged credential from a currently authenticated host
session, or report that the account is limited. Neither is an act this
participant may perform, and neither is worth guessing at by spending more
provider turns against a fixed cause.
