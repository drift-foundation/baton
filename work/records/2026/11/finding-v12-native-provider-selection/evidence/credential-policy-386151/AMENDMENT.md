# D1/D2 credential-policy amendment

Owner approval: current W385830 instruction, pinned in FINDING under
“2026-11-25 — owner approves D1 and D2”. Canonical claim E386151; coordination
M386152. This packet changes SEC-2 only and prepares no I2 implementation.

Apply only DESIGN.patch after validating the current SEC-2 anchor and preserving
other shared DESIGN edits. DESIGN.before.md and DESIGN.proposed.md retain exact
review context; they are not whole-file replacement authority. identity.json
records their hashes. Human checkpoint of the accepted narrow amendment is
required before I2, along with I1 acceptance/checkpoint.

## Required I2 acceptance

- D1 positive: never-successful initialization, verified unchanged home and
  confirmed absence of runtime writers permit only explicit audited withdrawal;
  retain original receipt and recovery decision.
- D1 negatives: any prior success, changed home, incomplete evidence, possible
  writer or uncertain runtime retains the hold and evidence. Restart never
  silently resets/reseeds; refreshed credentials survive without source access.
- D2: synthetic subscription-login files at 1,048,575, 1,048,576 and 1,048,577
  bytes respectively accept, accept and refuse. Accepted copies are byte-identical.
  Include multibyte content whose character count is below the limit while byte
  count exceeds it, plus accepted multibyte content at the byte limit.
- Apply the same byte bound to production copy and successor qualification
  launcher. Refusals contain no secret bytes, snippets or arbitrary decoding
  errors. Existing legacy token limits and unset behavior remain unchanged.

## Verification and boundaries

Documentation only: exact one-anchor replacement; 13 inserted policy lines;
no shared DESIGN or product edit, no test execution, no credential read, engine,
provider, build or native operation. Implementation checks above are required
future acceptance, not claimed passing tests. I1 remains independently selected
under M386147 P1/P2; its ownership confirmation is pending M386152.
