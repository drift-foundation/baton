# Finding: canonical child dossiers cannot be bound to Work

## Observed — 2026-08-17

Creating the approved “Rename discussion Threads to Topics” Work with this
existing canonical record binding:

```text
baton:work/records/2026/08/finding-recursive-target-graph/findings/finding-topic-vocabulary
```

was refused before mutation:

```text
binding path ... is not the canonical permanent record shape
work/records/YYYY/MM/<stable-record>
```

`transitions._binding()` accepts only exactly one component below the month.
Repository policy also defines causally tied child records at
`work/records/YYYY/MM/finding-parent/findings/finding-child/`, keeps that path
permanent, and requires Baton bindings and references to use canonical record
paths rather than `work/open/` or absolute paths. The protocol and repository
record model therefore disagree.

## Confirmed defect boundary

This is a Baton validation defect, not malformed input. A canonical child
dossier is permanent evidence and should be bindable without weakening root,
relative-path, traversal, or authority validation.

Until corrected, a Work may use the canonical top-level umbrella binding and
name the exact child record in its born message/references. That is an explicit
stopgap, not the fix; raw store edits, an absolute path, `work/open/`, or a fake
top-level copy are not acceptable workarounds.

## Acceptance boundary

- Bindings accept both top-level records and canonical child finding records
  under the repository's ruled maximum depth.
- They still refuse absolute paths, `work/open/`, traversal, empty/edge
  components, malformed year/month segments, excessive nesting, and paths
  outside `work/records/`.
- JSON, replay, revisions, closure, packaged CLI, and filesystem-availability
  independence preserve the accepted child locator byte-for-byte.
- Focused positive/negative and packaged workflow tests pin the exact shape.
