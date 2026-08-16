# Finding: v11 `init` prints an invalid `activate` command order

## Observed

The first real Gate B trial ran the installed v11 executable:

    /home/sl/opt/baton/v11/6d1b944/bin/baton-work init .

The successful JSON result printed:

    baton activate . --participant team.member

The public parser defines `--participant` as a global option and the shipped
setup documentation uses the valid order:

    baton --participant team.member activate .

## Confirmed boundary

The authority scaffold itself is healthy; `roots.json`, `BATON-SETUP.md` and
`baton.json` were created and no database exists before activation. This is a
current-facing command-generation defect in `src/baton_work/project.py`, not a
reason to discard or rerun initialization.

The trial proceeds using the public parser's valid order. That temporary
operator correction does not close this finding. The generated `next` value
must be fixed and covered before the next v11 distribution.

## Clarification after key-value grammar — 2026-08-16

The original correction above predates the confirmed strict `key=value`
grammar. The production `825e97d` initialization still emits the obsolete
text:

    baton activate . --participant team.member

The current valid hint is:

    baton --participant team.member activate directory=.

This explicitly supersedes the earlier proposed
`baton --participant team.member activate .` form: global option placement
remains required, and the directory operand must now use the one public
`key=value` grammar. The correction must cover both properties without
changing successful initialization or authority contents.
