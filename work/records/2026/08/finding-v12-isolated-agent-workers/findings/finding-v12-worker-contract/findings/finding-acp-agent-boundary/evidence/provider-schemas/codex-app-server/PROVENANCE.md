# Captured Codex App Server response schemas

These four JSON Schema documents are the provider's OWN response contracts for
the approval families this boundary must answer. They are captured evidence,
not authored by this record, and they are what
`evidence/test_acp_boundary_model.py` validates every denial payload against.

A self-authored equality assertion cannot prove provider-shape conformance;
only the provider's schema can. This directory exists because the first
revision of `SPEC.md` §10.5 asserted equality against a string the provider
would have rejected.

## Provenance

Generated on 2026-08-21 from the installed Codex CLI:

```text
codex --version
codex-cli 0.149.0

codex app-server generate-json-schema --out <temporary directory>
```

Copied verbatim from that output, re-serialized with sorted keys and two-space
indentation for a stable diff. No content was edited.

## Interface digest

The certified `provider_binding.interface_digest` in
`evidence/traces.json` is the SHA-256 over the RFC 8785-style canonical bytes
of the object mapping each file name to its parsed contents:

```text
sha256:70ff479c2fe907c9146af7d4653bc9cd86f89a470cace6a78a76e5e1fb82b7e0
```

Regenerating from a different CLI build is expected to change this digest.
That is the point: a different build is a different certified interface, and
`SPEC.md` §2.1 refuses one that is not the certified one.
