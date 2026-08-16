# Setting up this Baton coordination home

`baton init` wrote one strict-JSON configuration for you to edit:

`baton.json` — the generation-one authority configuration. It is
deliberately INCOMPLETE: add your teams (participants, roles, routes,
kinds) and, if you use repository dossiers, the `roots` catalog. Each
root declares its explicit absolute `base` path right here — baton.json
is the single root config; there is no separate machine-local resolver
file and no filesystem inference. Do not add comments; the file must
stay strict JSON.

When the configuration is complete, activate the authority:

    baton activate . --participant team.member

Activation runs the one authoritative validation and creates the
unique SQLite database only if the document passes; a refusal leaves
nothing behind, so edit and retry freely. After activation, members
open the instance with `--config baton.json --participant team.member`.
