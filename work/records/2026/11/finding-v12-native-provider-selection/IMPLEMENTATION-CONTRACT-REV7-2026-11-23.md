# W385830 — proposed implementation contract, revision 7 (delta)

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-23. Authority: M385865 and the FINDING entry "Subscription
credential refresh in retained home — owner 2026-11-23".

**PROPOSED — NOT APPROVED.** Research and design only. Nothing built,
launched or tested; no provider call; no credential or registry read; no
runtime edit.

Base text: `IMPLEMENTATION-CONTRACT-PROPOSED-2026-11-23.md` as amended by
`-REV2-` to `-REV6-`; all six preserved unchanged. This file replaces REV6
§3.5 (credentials) and REV6 verification items 13, 14 and 16, marks REV6
§3.4 and the managed-entry list as settled with the owner's limits,
withdraws REV6 §7 (the API-key credential I recommended was not selected),
and raises the next decision.

## 1. Settled

| Settled by the owner | Source |
| --- | --- |
| **D3: the Codex worker uses subscription login credentials.** The provider may keep its refreshed credential copy in its own stable retained home | M385865 |
| API-key billing is not substituted | M385865 |
| Refreshed credentials are never written back to the operator's home, and never appear in ordinary candidate, evidence or log output | M385865 |
| The credential registry entry and reference, the seed delivery, and the pinned build's refresh behaviour remain to be established and qualified. No credential read or provider call is authorized | M385865 |
| **One writer:** a new container on a home is refused until the earlier runtime is confirmed stopped. Once prior runtime settlement establishes that, admission proceeds with no further owner approval | M385865 |
| A stale or missing observation is not positive cessation | M385865 |
| **Baton-managed replacement is limited to explicitly identified Baton-owned instruction and configuration files.** Provider session data and refreshed credentials are never overwritten at start | M385865 |
| The home is retained work storage, not a per-attempt directory. Existing execution ownership and work-area machinery; no manual babysitting; no general successor-access gate | M385865 |

REV6 §3.4 (allocation plus holder check) is therefore settled as written,
with the clarification in §3 below. REV6 §4's managed-entry list is settled
with the limit in §4 below.

## 2. Credentials in a retained home (replaces REV6 §3.5)

### 2.1 Two credential modes, declared per adapter

| Mode | Used by | Behaviour |
| --- | --- | --- |
| **Delivered** | The Claude worker, as today | Unchanged by this ruling: the credential is the read-only delivery, and the home refers to it |
| **Seeded and retained** | The Codex worker | §2.2 |

The mode is part of the adapter's identity, so a worker cannot change mode
without becoming a different composed worker.

### 2.2 Seeded and retained (Codex)

1. **Seed.** The registry's login credential reaches the container by the
   existing read-only credential delivery. Nothing new delivers it.
2. **First use.** If the home holds no credential at the provider's
   location, the adapter copies the seed there, owner-only. That is the
   only time Baton writes it.
3. **Afterwards.** The copy in the home belongs to the provider. It may
   refresh and rewrite it. Baton does not replace, compare, re-link or
   remove it at start, whatever the delivery then contains.
4. **Never outward.** Nothing copies the home's credential anywhere: not to
   the delivery source, the registry, the operator's home, an output,
   custody, a proposal, a log or a diagnostic. The delivery is a read-only
   mount; the home is in no manifest (REV6 §3.2).
5. **No key substitution.** The Codex worker's credential profile has no
   API-key slot and its provider environment carries no key variable. If
   the login cannot authenticate, the turn fails with a typed cause; no
   other billing route is tried.
6. **When the retained copy stops working.** The provider fails to
   authenticate; the attempt ends as a provider failure; the home is left
   as it is. Automatic re-seeding is excluded by item 3. Proposed: one
   explicit operator act replaces the home's credential from the registry,
   allowed only while no runtime holds the home. This is exceptional
   recovery after a login is revoked or expires, not a routine step.

### 2.3 Keeping it out of ordinary output

- The adapter never reads the credential's content except to make the
  first copy, and never places it, its digest of content or its path
  contents in a record. Records may say "credential present: seeded /
  retained".
- The provider's own log is already retained as evidence. Whether the
  pinned build can print credential material into its output is not
  established; it is a named check at qualification (§5), and until then
  no claim is made that provider logs are free of it.
- The home can be read by every later attempt of that worker. That is the
  selected arrangement, stated here so it is not mistaken for an
  oversight.

## 3. One writer (clarifies REV6 §3.4)

"Confirmed stopped" means the positive facts the system already settles
for a runtime: it is recorded absent or destroyed and its cleanup is
`complete` or `retained`. These are not confirmation, and a start meeting
them is refused and stays pending:

- no observation at all;
- an observation older than the holder's last recorded activity;
- a runtime recorded `uncertain`;
- a stop that was ordered but not confirmed;
- an attempt ending, provider exit or token expiry by itself.

The refusal is a state, not a request to anyone: the same start succeeds on
a later pass once settlement records the earlier runtime gone. No owner
item is opened by it.

## 4. Baton-managed entries (limits REV6 §4)

- The list in each adapter names **only** Baton-owned instruction and
  configuration files, each by exact path in the home.
- Credentials are not on it. Provider session files, history, caches and
  anything else the provider or a model writes are not on it and are never
  replaced, truncated or removed at start.
- An entry is on the list only when Baton delivers its content from a
  digest-bound input. Today no such delivery exists, so **the list is
  empty** until W385853's instruction delivery is selected and names its
  files.
- A path cannot be both managed and provider-written. Which paths each
  pinned build writes is an inventory item; a collision found there is
  reported, not resolved by overwriting.

## 5. Qualification limits, stated

Nothing below is established. None is authorized by any ruling so far.

| # | Not yet known | Answered by |
| --- | --- | --- |
| U1 | Whether Codex 0.169.0 starts under the v12 container posture with a disk home at the chosen path | Engine-only image gate |
| U2 | Where 0.169.0 keeps its credential and session files, and which home files it loads as instructions or configuration | Engine-only image gate |
| U3 | Whether 0.169.0 authenticates from a seeded login copy and completes one fixed turn | Real-provider question Q1 |
| U4 | Whether and when it refreshes, and that the refreshed copy lands in the home and nowhere else | Q1, observed on the retained home afterwards |
| U5 | Whether a refresh made in the worker's home invalidates other copies of the same login — the registry seed, another worker's home, or the operator's own session | Not answerable by one call. I have assumed nothing; if it does, one login cannot seed more than one place |
| U6 | Whether the build can emit credential material into its own output | Q1 output examined for the seeded value's presence, by a check that does not record the value |
| U7 | What 0.169.0 reports as model participation | Q1 |
| U8 | Which registry entry is the seed, and whether it is a login made for this worker or a copy of one in use elsewhere | Owner selection; I have read no registry |
| U9 | What the pinned Claude build writes into a retained home, including at its credential location | Engine-only image gate |

Q1 is extended accordingly (amends first contract §6.3): beyond
authentication, events and reported models, it records where credential
and session files appeared, whether the home's credential changed during
the turn (by size and time only), and the U6 check.

## 6. Verification (amends REV6 §6)

REV6 items 1–12, 15, 17 and 18 stand. Items 13, 14 and 16 are replaced and
19–27 added. Deterministic; fake provider.

13. *Delivered mode:* behaviour is today's; the credential's bytes exist
    nowhere under the home after a turn.
14. *Seeded mode, empty home:* the seed is copied once, owner-only.
16. Managed entries are re-placed at every start; with an empty list,
    start changes nothing in the home.
19. *Seeded mode, credential present:* start leaves it byte-identical,
    including when the delivery now holds different bytes.
20. A fake provider rewrites the credential during a turn; the next
    attempt of that worker sees the rewritten bytes.
21. After such a turn the delivery source, the registry fixture and every
    path outside the home are unchanged.
22. A sentinel credential value appears in no result, manifest, custody,
    proposal, attempt log written by Baton, diagnostic or status document.
23. The Codex provider environment contains no API-key variable and the
    worker's credential profile no key slot; an authentication failure
    ends the turn with a typed cause and nothing else is tried.
24. Session-like files a fake provider leaves in the home are untouched by
    the next start.
25. A start is refused and pending for each non-confirmation in §3, and
    proceeds on the next pass after settlement records the runtime gone,
    with no owner record created.
26. An adapter declaring a managed path that is also the credential
    location is refused at composition.
27. The explicit re-seed act is refused while a runtime holds the home,
    and otherwise replaces only the credential.

## 7. The next decision for the owner

**Does the Claude worker image stay on CLI 2.1.247, or move?** (D1,
Claude half.)

It comes next because the Codex side is now specified down to
qualification, and the Claude reviewer is the other half of the pipeline.
The image is rebuilt in any case, because the worker adapter changes; the
question is only which CLI it contains.

What is known:

| Fact | Source |
| --- | --- |
| 2.1.247 is the build every native review so far ran on | `worker/Dockerfile.claude:63` |
| Whether 2.1.247 accepts the Fable selector you want is unknown | Never asked; real-provider question Q2 |
| On 2.1.247 the result names models only in per-model usage entries | September qualification dossier (first contract F5) |
| The vendor documents loading of project `AGENTS.md` only from 2.1.277. A newer build could therefore read host instructions from a source checkout by itself; 2.1.247 is not documented to | W385853 `LOADING-BOUNDARIES.md`; not verified in either image |
| This host runs 2.1.330; its help output is retained | This dossier and W385853's packet |

- **A — Stay on 2.1.247, and move only if Q2 shows it cannot select the
  model (recommended).** One variable changes at a time: the adapter, not
  the CLI. The known result shape and the known instruction-loading
  behaviour stay as they are while W385853's delivery is unfinished. Cost:
  if 2.1.247 rejects the selector, Q2 is repeated on a newer build and the
  image is qualified a second time.
- **B — Move to 2.1.330 now.** Most likely to know a recent model
  selector, and the build whose help is retained. Cost: its result shape,
  its home files and its instruction discovery all have to be inventoried
  fresh; and if it loads project instructions unaided, native Claude
  workers would see host policy until W385853's delivery exists — making
  that delivery a prerequisite for using the Claude reviewer.
- **C — Another build you name.** Cost: no evidence of either kind.

I recommend A. I have not assumed it. As with the Codex pin, the answer
fixes the design and the image recipe only; no build or provider call is
selected by it.

## 8. Still open after that

| # | Item | Kind |
| --- | --- | --- |
| U8 | Which registry login seeds the Codex worker | Owner decision |
| D2 (values) | Selector and mapped identity for the Fable reviewer and the Codex implementer | Owner decision, informed by Q1 and Q2 |
| D7 | Selection of the engine-only image gates and the two real-provider calls | Owner decision |
| Order with W385853 | Editorial candidate, then N2, then its delivery change | Coordination in progress (T385853 M385863, review M385866); no overlapping runtime edit is assigned to anyone |
| Deferred by M385859 | Model-switch and sharing behaviour for a home | Not raised |

## 9. Limits

- Nothing executed; no credential, registry or operator-home content read.
- The explicit re-seed act (§2.2 item 6) is my proposal. Without it a home
  whose login has lapsed cannot be made usable except by removing the
  home. It is not automatic and not part of normal operation.
- What happens when a Claude worker's retained home already holds
  something other than the expected reference at its credential location
  is left unspecified until U9 shows whether that can occur. The settled
  rule already forbids overwriting it.
- U5 is a real risk to the selected arrangement that I cannot assess from
  this repository.
- The 2.1.277 instruction-loading statement is the vendor's documentation
  as recorded by W385853; neither image has been observed.
