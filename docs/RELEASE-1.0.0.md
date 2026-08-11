# Baton 1.0.0 is available

Baton 1.0.0 is the first public release of the standalone coordination tool
for humans and AI agents. It runs fully offline, needs no daemon or Internet
service, and lets trusted participants coordinate as peers through a shared
SQLite mailbox.

The release provides directed handoffs with claims and terminal dispositions,
team-scoped and global notices, concise subjects and one-line messages, typed
multipart content, repository references, multi-recipient delivery, a shared
core API, and a human terminal inbox. Both `baton` and `baton-tui` report
`1.0.0 (protocol 10)`.

## Joining the channel

Your local deployment supplies the absolute executable and config paths plus
your participant address. Add the role-to-participant mapping to your project
policy; do not copy the mailbox into your repository or infer it from the
working directory.

Read [Using Baton effectively](EFFECTIVE-BATON.md) for the working routine and
[AGENTS-MAILBOX-PROTO.md](AGENTS-MAILBOX-PROTO.md) for the exact protocol and
mailbox conventions. The [README](../README.md) is the complete CLI and
storage reference.

The essential loop is simple:

1. Keep one read-only `wait` active for your participant.
2. Claim the exact message id it reports, or use `see` for a notice.
3. Process every claim immediately and finish it with `reply` or `close`.
4. Re-arm `wait`.

For engineering work, preserve decisions and restart context in a
`work/finding-*` folder and carry the exact paths in the handoff's references
part. Baton messages coordinate the work; findings, plans, progress journals,
tests, and review journals make the result reproducible after a crash or model
change.

The canonical released zipapps and live authority remain stable while future
work is developed in separate candidate distributions and development
authorities. Normal users should not be interrupted by feature development.

