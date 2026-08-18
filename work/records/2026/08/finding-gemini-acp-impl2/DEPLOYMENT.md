# W230 deployment material — the `impl2` route for Gemini

W230 steps 2 and 3. This is what the next accepted Baton generation must
carry, and what the deployment-owned Gemini bridge configuration needs. It is
recorded rather than applied: accepting a configuration is the approver's act,
and the currently deployed binary predates the `alternates` field.

## The configuration additions

Merged into `teams.baton`. The visible endpoint stays `baton.impl`; `impl`
remains the deterministic default handled by `baton.claude`, and `impl2` is
selected explicitly or not at all.

```json
{
  "kinds": {
    "impl": {
      "alternates": [
        "impl2"
      ],
      "display": "Implementation",
      "route": "impl"
    }
  },
  "participants": {
    "gemini": {
      "display": "Gemini",
      "roles": [
        "impl"
      ]
    }
  },
  "routes": {
    "impl2": {
      "handlers": [
        "gemini"
      ],
      "role": "impl"
    }
  }
}
```

Note what is NOT here: nothing changes for `baton.claude`, for the existing
`impl` route, or for any Work already routed to it. An omitted route selection
resolves to `impl` exactly as it does today.

`gemini` holds the existing `impl` role. That is enforced, not merely
intended — an alternate whose route carries a different role is refused at
acceptance, because the endpoint's meaning must not change with the route.

Every role needs instructions (W101), so `impl`'s existing text covers Gemini
too: instructions are role-owned and inherited by every member launched in the
role.

## The Gemini ACP bridge

`examples/acp-bridge-gemini.json` is the template and already ships. The live
instance file is deployment-owned and must give Gemini its OWN:

- participant (`baton.gemini`) and explicit role (`impl`);
- agent command — the official `gemini --acp`;
- session/state directory, separate from Claude's;
- authentication, which Gemini manages itself;
- permission mode and a deployment-owned deny policy.

Nothing about that file is shared with the Claude bridge. Two consumers need
two participant addresses, and the ACP bridge already refuses one participant
assigned twice.

## Applying it (approver)

1. Edit the coordination home's `baton.json`: merge the block above and
   increment `generation`.
2. Accept it with `regen` as the config-capable participant.
3. Write the deployment-owned Gemini bridge configuration from the shipped
   example and start it through `just start MAILBOX`.
4. Run the canary in `PLAN.md` step 5 and record certification or a concrete
   rejection.

## Using it, once accepted

    baton pass work=W123 to=baton.impl route=impl2 comment="…"

Omitting `route=` selects `impl`. Baton never fails over to `impl2`, never
races both, and never displays every candidate on a Work row: the choice is a
deliberate per-Work act or it does not happen.
