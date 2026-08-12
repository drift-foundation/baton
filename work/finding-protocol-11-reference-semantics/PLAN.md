# Plan — protocol 11 reference semantics

1. **Pin the protocol ruling** — **done 2026-08-11**. Protocol 11 removes the
   current external hash-pinned `--attach` contract; references may float,
   change, or disappear without damaging the message or authority. Protocol 10
   and the 1.1.0 release remain unchanged.
2. **Inventory the current boundary** — **started 2026-08-11 with the resolved
   message/ephemeral-folder case pinned in `FINDING.md`**. Complete the map of
   external-part schema, manifest, publication, verification,
   scan/doctor/quarantine, root-regeneration, reread/save, CLI, TUI, dump, and
   documentation surfaces. Separate stored content disposition from external
   filesystem addressing.
3. **Research locator models** — compare Git-only commit/path addresses with
   typed locator schemes; cover repository identity, object availability,
   authorization, submodules, generated evidence, and floating references.
4. **Rule the address and promise types** — decide immutable versus floating
   forms, who resolves them, and whether Git is exclusive. Record the ruling
   here before protocol/schema implementation.
5. **Design the protocol-11 envelope and cutover** — remove or replace
   external-part fields and `--attach`, preserve byte-exact stored content,
   define CLI/TUI rendering, and integrate the fresh-authority retirement
   sequence.
6. **Review across teams** — use changed/deleted/unavailable targets and
   cross-machine repository mappings as concrete trials before freezing the
   protocol-11 contract. Include normal deletion of mandatory-ephemeral
   finding folders after a message is resolved; it must require no recovery
   and leave authority health and root evolution unaffected.
7. **Implement only after authorization** — add focused positive, negative,
   compatibility, health, claimability, and cutover regressions; independently
   review before any protocol-11 authority is activated.

`baton.implementer` creates and exclusively writes `PROGRESS.md` when this
finding becomes the current serial implementation item.
