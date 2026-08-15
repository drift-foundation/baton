# Setting up this Baton coordination home

`baton init` wrote two strict-JSON files for you to edit:

1. `baton.json` — the generation-one authority configuration. It is
   deliberately INCOMPLETE: add your teams (participants, roles,
   routes, kinds) and, if you use repository dossiers, the portable
   `roots` catalog. Do not add comments; the file must stay strict
   JSON.
2. `roots.json` — the machine-local resolver mapping root ids to THIS
   machine's absolute checkout paths. It never becomes authority
   state; other machines keep their own copy.

When the configuration is complete, activate the authority:

    baton activate . --participant team.member

Activation runs the one authoritative validation and creates the
unique SQLite database only if the document passes; a refusal leaves
nothing behind, so edit and retry freely. After activation, members
open the instance with `--config baton.json --participant team.member`.
