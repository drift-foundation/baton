# Owner direction — complete standalone deployment

Work W183883, 2026-09-16. Recorded by baton.prompt.

## Explicit direction

Asked how to finish the still-open Work, owner selected:
"Finish the agreed two-argument bootstrap: it creates the bundled distro,
databases and independent repositories."

Owner then clarified:
"once deployed, we shouldn't have to require more than the destination for
stop/start/status" and "once deployed, we should make it standalone, so just
should have justfile in the destination, then right?"

## Selected public interface

From the development checkout:

```text
cd v12
just bootstrap inputs.json /absolute/destination
```

Bootstrap prepares the PyInstaller one-folder distribution with bundled Python
and dependencies, databases, independent repositories at the explicitly selected
base, instance.json and a **destination-local justfile**. Building/selecting the
distribution must be handled by the two-argument operation; no third required
DISTRO operand. A separate build recipe may remain a development convenience.

The owner then operates the installed instance:

```text
cd /absolute/destination
just start
just status
just monitor
just stop
```

Alternatively `just --justfile /absolute/destination/justfile status` should
select the same deployment from another working directory. Resolve installed
paths relative to the deployed justfile, not the caller's cwd. Source-side
wrappers, if retained, require at most DESTINATION and dispatch to that deployed
interface. No repeated JSON argument, manual environment export, shell activation,
checkout helper or build-venv dependency in normal deployed operation.

The internal instance.json remains the single instance description. The public
interface locates it automatically inside the destination. Preserve explicit
instance/command ownership checks beneath the simpler interface.

## Explicit supersessions

- Supersedes the public lifecycle JSON operand selected in
  OWNER-INSTANCE-DESTINATION-20260916.md and repeated in
  OWNER-PYINSTALLER-20260916.md. The internal JSON selection/identity remains.
- Supersedes OPERATOR-INDEPENDENT-REPOSITORY.md's manual repository-clone
  prerequisite as the delivered workflow. The owner-run bootstrap performs those
  operations in the correct order. This does not authorize an agent to mutate
  Git; the owner invokes the finished operation.
- Supersedes the latest owner-handoff-only PLAN state and the third required
  distribution operand. Earlier accepted code/evidence is retained and reused.

The destination is outside the source checkout. Its repository objects and
working repositories do not borrow mutable source objects, linked worktrees or
paths. PyInstaller remains the selected packager. Host Git, just, container engine
and explicit credential references remain dependencies; this is isolation from
the development checkout/Python environment, not a claim to bundle the OS.

Implementation is authorized within the existing Work. Keep the change bounded
to completing this flow, with actual installed-entry verification and retained
artifacts. Do not close W183883 on a fragmentary configuration packet or create
another planning-only approval round. Production source/base/input choices must
be supplied explicitly; missing choices do not prevent building and testing the
generic owner-run command. No live Job/provider execution selected.
