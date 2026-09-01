# Progress

## 2026-09-01 — first implementer round (`baton.claude`, W55361 impl claim)

**The approved sequence is done, bounded exactly as ruled: prose at three
boundaries, one executable regression, and no build.** No image was built, no
provider called, no credential touched and no supply-chain redesign smuggled
in.

### Item 1 was already satisfied and I verified rather than assumed it

The ruling had to be appended to any active dogfood Work whose plan still said
a fresh attempt requires a rebuild. That was W51487, and I appended the dated
supersession to its `FINDING.md` and `PLAN.md` while I held its claim in an
earlier round — recording the selected digest
`sha256:8af96742a89489ae974943284fcc65a5fd58e02263a9ae2142b3d0afa4f9c0e6`, the
selection event, the reason, and the layer evidence. W51487 has since closed
non-satisfying; the historical attempt account was not rewritten.

### Item 2 — the convergence claim is now conditional by construction

`tools/worker_image.py` ended a paragraph with "Two independent executions of
the recipe reach one digest." full stop, and an operator read that as a promise
that rebuilding was free. It now reads **"GIVEN THE SAME BASE IMAGE AND THE
SAME FETCHED CONTENT"**, followed by what that condition cost: the two measured
digests, the layer-by-layer localisation, and the three moving inputs.

The paragraph also now says the thing the module does NOT do, because that is
the half a reader could otherwise get backwards: it removes the build clock and
the builder's receipt, and it must never normalize away different fetched
bytes — two images built from different upstream content are two
artefacts, and
a normalizer mapping them to one identity would lie about what a manager
pinned. **The content-sensitive normalizer and every existing assertion are
unchanged.**

### Item 3 — the boundary is documented where an operator meets it

`tools/dogfood_operator.py` gains a fourth NOT- clause in the paragraph that
already lists what the command is not: it is **not the place the image is
selected**. Selection lives chronologically in the owning Work's record; the
command consumes the exact digest grant and reports what it launched; a new
attempt reuses the current selection; a build result is a candidate until a
recorded upgrade/source/security/platform/refresh event validates and selects
it. It says in as many words that writing a fresh digest into a new grants file
is not a selection — it is an operator claiming an authorization no record
made. The existing not-an-authorization boundary is preserved, not replaced.

`v12/worker/Dockerfile.claude` carries the same fact at the recipe, beside the
`FROM` that is one of its three causes, and names the locking design as
presented-and-not-selected so a later reader does not mistake the comment for
authority to implement it.

### Item 4 — the fences revalidated, and the one that was documentary made
executable

Checked against the current tree rather than the record:

    a mutable tag is refused as a digest
        test_a_mutable_image_tag_is_not_a_digest
    sealed input and evidence name it
        worker_image_digest in _held_identities and the evidence set
                                            and in the evidence member set
    a retry refuses a changed digest
        worker_image_digest is in _RETRY_BINDING

The third was true in the code and had no case of its own — the retry-binding
tests drove the disposition and the agreeing path. Added
`test_a_retry_cannot_quietly_select_a_different_worker_image`, which is the
smallest regression that makes "a new grants file is not a selection"
enforceable rather than documentary.

**Mutation-checked**: dropping `worker_image_digest` from `_RETRY_BINDING` is
CAUGHT. Without the new case it would not have been.

### Item 5 — focused gates only, no build

    tests.manager.test_worker_image + tests.tools.test_dogfood_operator
      + tests.manager.test_dogfood_image                     277 tests, OK

`test_dogfood_operator` is 160 where the recorded baseline is 159; the one new
test is the regression above. The recorded 36 worker-image/recipe and 159
operator baselines are otherwise unchanged, and no rebuild or provider attempt
was run — this Work does not authorize either as evidence of a policy
correction.

### State

Awaiting independent review. Item 6's "record the selected digest in the next
dogfood attempt's durable record" belongs to that attempt, not to this round.
Passing back rather than closing.
