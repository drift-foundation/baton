# W62098 retained-proposal import research — 2026-09-01

## Scope and labels

This is reviewer research for W62098. It does not authorize an import or claim
that W52821's current repository integration is the retained candidate byte for
byte.

- **Observed** describes retained bytes or current code inspected on
  2026-09-01.
- **Confirmed** is a relationship independently rederived from those bytes.
- **Proposed** is a contract boundary awaiting an approver ruling.

The retained reproductions remain at `/tmp/w52821/run2`,
`/tmp/w52821/run4`, and `/tmp/w52821/run5`. They are evidence locations, not
portable proposal identities. The durable identities below are content
digests.

## The measured lineage

The operator evidence records one immediate source-tree digest and one retained
proposal digest per attempt. It records no parent-proposal identity and no
canonical import-base artifact.

| layer | immediate source tree | retained proposal tree | independently reported delta |
| --- | --- | --- | --- |
| run2 | `sha256:e2f1c69c16ef39b2e02d8f1bc25b017173f48e58bafcd5463da49a7edc19f312` | `sha256:a1816054d69bf8858e52837f23f65d35c18a83fc4976f2deb152d99a2a813aba` | 5 paths |
| run4 | `sha256:d68acac58ca82336f72bebcfc065eebbf551534959f19c2341869fdbc29506e6` | `sha256:bee7b85d63783f2c79e42755226e1d6542750b274f50a20c94470e9973ae203d` | 4 paths |
| run5b | `sha256:0b04928d40473ba59c40d2d3521f9f0afbc19ff68c41127e881110a5cf847d34` | `sha256:416d79a230fe090bf95d9d71e716ff09d67c4efdf2bb3373d618c19937a838aa` | 6 paths |

**Observed:** run5b's input manifest is a complete 123-entry tree. On the
relevant paths its bytes are the retained run4 candidate, including
`tools/dogfood_operator.py` at
`sha256:97e19492d72dc177a5060a27395b0080bde27408ca904f48c508fa067f9ddd61`.
Run5b did not change that file, so neither the worker's `changed_paths` nor the
operator's independently rederived `changed_paths` named it.

**Observed:** `baton.dogfood-proposal/1` contains `changed_paths`, disposition,
provider status, verification status/argv, source entry count and task ID. It
contains no canonical base, parent proposal, lineage, or complete import
closure. `baton.dogfood-evidence/1` adds the immediate `source_tree_digest` and
the retained output artifact digest, but still no relationship to a canonical
base or earlier candidate.

**Confirmed:** the v12 authority's immutable proposal row is stronger but not
complete for byte import. `Authority.publish` binds result, candidate, input,
policy and target digests. `Authority.integrate` compares the current
`canonical_target` digest to the proposal target, then advances that digest.
It neither retains the base artifact bytes nor derives or applies a path-level
three-way plan. The target digest is therefore a necessary stale-target fence,
not a sufficient filesystem import contract.

## Complete W52821 closure

Direct byte comparison of the original canonical base states against the
signed run5b final candidate produces seven intended paths, not run5b's six.
The base states below were also checked against the original run2 source on the
relevant paths. `absent` is a first-class state; it is not the digest of an
empty file.

| path | canonical-base state/digest | final-candidate state/digest |
| --- | --- | --- |
| `DEPLOYMENT.md` | file `sha256:20fe882b4a20767cc07bd444ddfa7dad071fd92190fbf6327d49701619405ab1` | file `sha256:56c9ad635955f22050c8e77d32168def9e28ec049de4f1f83dbfb5d9737caea4` |
| `src/baton_v12/worker_manager/credentials.py` | file `sha256:7b0b6750216e9b090a446e25f118f6e359103b2a6a83db6204e7c289941144d6` | file `sha256:09eef2cc97a6f62b43dac0352a71017fced3b6c5556f6ad691f38c4267f4a8df` |
| `tests/tools/test_dogfood_operator.py` | file `sha256:ee11a680a393c1e8d0de4b49767c9781eafdd4ead3465ea2dc9389dc0415c309` | file `sha256:4949fad55e331b4d30e614a021c3449e21d1553e52f6e29d5cffd25a8aa4679b` |
| `tests/tools/test_user_credentials.py` | absent | file `sha256:728f2964ae28de8e437840284feeb2b15ff5332718676c584b42f8740eecfb4e` |
| `tools/dogfood_operator.py` | file `sha256:ec9f132acbee691a48225eddbd196ec850542dc387472e17859e22b2f6f7610f` | file `sha256:97e19492d72dc177a5060a27395b0080bde27408ca904f48c508fa067f9ddd61` |
| `tools/parallel_test.py` | file `sha256:59f15de301df76d43178147102effcfa6220855d701a0b3d0fcaa3329f49ae06` | file `sha256:62eb44f9fb50b25ebe7a754c8c4550bf1f1feea556711aeecb58f69fa160362e` |
| `tools/user_credentials.py` | absent | file `sha256:162420d0be3a3c24063443a9a590eacbd4146ec8504a30563f4fba13eb9543ad` |

**Confirmed:** `tools/dogfood_operator.py` is the omitted inherited path. Its
run2, run4 and run5b candidate bytes are identical. The current repository
file is instead
`sha256:cc09c6b814ab709fe48e588b2a53b503212a116225df5c245e4f4f2eae3aceff`:
it differs from both the canonical-base byte and the signed candidate byte
because the bounded manual integration preserves concurrent W61599 work. A
three-way importer must report this as overlap. It must not replace the file or
claim that the current repository is byte-identical to the final candidate.

## Current code boundary

**Observed:** `tools.dogfood_operator.stage_source` copies exactly one source
tree into `/input/source`. `input_manifest` emits exactly one source entry.
`run_dogfood_task` retains the manager-measured manifest for that immediate
tree. `_derived` then calls `_changed_paths(source, candidate)`, which walks
only that immediate source and final candidate and compares regular files by
bytes. It correctly detects additions, changes, and deletions for one layer,
but cannot recover changes inherited before that layer.

**Confirmed:** the immediate delta must remain. It proves what the current
worker did and must not be redefined to mean canonical import closure. The
defect is the absence of two additional, separately held facts:

1. the ordered provenance by which the immediate staged source inherited
   retained candidates; and
2. the direct canonical-base-to-final-candidate closure used for import and
   review.

## Proposed closed contract

### Identities and retained artifacts

Create a new closed dogfood import-context/result version rather than widening
the meanings of `changed_paths`, task v1, or proposal v1 in place.

Before launch, the deployment records:

- an immutable, manager-copied canonical import-base artifact reference and
  its independently measured content/tree digest;
- the immediate staged-source tree digest;
- an ordered inherited lineage whose entries bind proposal/result identity,
  retained output-artifact digest, candidate-subtree digest, and the
  source-tree digest that consumed that candidate at the next layer; and
- the canonical-base identity that the v12 authority proposal's `target`
  digest denotes.

The canonical base must be a retained byte artifact, not only a mutable
checkout path, ambient Git state, or unresolvable digest. Git may corroborate
the artifact during repository work, but it is not the portable primary
locator. A lineage link whose predecessor candidate-subtree digest does not
equal the declared successor source-tree digest refuses before provider work.

After custody, the trusted operator independently compares the retained base
artifact directly with the retained final candidate. It emits a sorted,
bounded closure with one canonical relative path per difference. Each entry is
exactly:

- `path`;
- `base`, whose state is `absent` or `file` and whose file state carries bytes
  and content digest; and
- `candidate`, with the same closed state shape.

The closure header binds the base tree digest, final candidate-subtree digest,
retained output-artifact digest, entry count, and canonical closure digest.
Direct comparison, rather than unioning per-layer `changed_paths`, handles
changes later reverted to the base, additions, and deletions correctly.
Ordered lineage remains provenance; it is not trusted as the closure
algorithm.

The authority proposal and every verification/review/approval/integration
receipt must bind the import-base and closure digests in addition to the final
candidate digest. A review that signs only the immediate delta is not an
import authorization. The independently derived closure must equal the
retained result's closure byte for byte before review can accept it.

### Three-way import decision

For every closure entry, compare a fresh current-target state with the signed
base and candidate states:

- current equals candidate: `already-applied`, no write;
- current equals base: `apply`, writing or deleting exactly the candidate
  state; or
- current equals neither: `overlap`, refuse the entire import.

Preflight every entry before any repository mutation. Any malformed artifact,
digest mismatch, missing closure path, extra candidate difference, current
overlap, or target change during the operation produces a typed refusal and
no partial import receipt. Disjoint current paths are outside the closure and
remain untouched. The first slice performs no textual merge and offers no
“take candidate” override.

The filesystem writer must operate under the repository integrator's exclusive
write/fence boundary and revalidate the current states at that boundary. The
existing authority `canonical_target` compare remains the ledger fence; it
does not replace the path-level byte preflight. If the implementation cannot
provide an all-path no-partial-write boundary, it may produce a signed import
plan but must not advance the authority integration receipt.

### Separation from W61981

W61981's approved `baton.dogfood-task/2` owns verification materialization:
contained working/candidate/input destinations, Python import roots, and the
closed context/result axes. W62098 owns import provenance and repository
integration. The canonical base may travel through the same bounded
manager-copied source machinery when useful, but it is not implicitly a
verification input, and task/2's context source is not implicitly an import
base. Each role is named and digest-bound separately.

## Required focused regressions

1. Single run: base `B` to candidate `C` yields the same immediate delta and
   import closure, including added and deleted files.
2. Multi-run: run2 changes `a` and adds `x`; run3 starts from run2's candidate
   and changes only `b`. Run3's worker delta is only `b`, while its complete
   closure is `a`, `b`, and `x`.
3. Reversion: run3 returns `a` to its base byte; `a` is absent from the final
   direct closure even though it appears in lineage.
4. Disjoint work: current target changes `y`, which is outside the closure;
   import preserves `y` byte for byte.
5. Overlap: current target changes inherited `a` to a third byte. Preflight
   reports bounded `overlap`, writes nothing, and records no integration
   receipt.
6. Idempotence: a current path already equal to the signed candidate is a
   no-op, while the remaining base-equal entries apply.
7. Tampering: wrong base/candidate/lineage/closure digest, broken lineage link,
   non-canonical or duplicate path, extra candidate difference, and target
   movement all refuse before mutation.
8. Review: changing any base state, candidate state, closure entry, final
   candidate digest, or closure digest invalidates the review binding.

## Decisions required before implementation

1. Approve a distinct versioned import-context/result contract, preserving
   task/2 for verification and preserving proposal-v1 `changed_paths` as the
   immediate worker delta.
2. Approve retained base artifact plus ordered digest-linked lineage and a
   direct base-to-final closure with explicit `absent|file` states.
3. Approve all-entry three-way preflight, whole-import overlap refusal, no
   automatic merge, and no integration receipt without an exclusive
   no-partial-write boundary.
4. Decide the exact owner and representation of that repository write/fence
   boundary. No such filesystem importer exists in the current dogfood
   operator; the v12 authority currently advances only a canonical target
   digest.
