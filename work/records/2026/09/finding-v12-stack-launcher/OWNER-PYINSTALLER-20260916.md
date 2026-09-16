# Owner decision — bundled Python distribution and independent repository

Recorded by baton.prompt, 2026-09-16, Work W183883.

## Confirmed outcome and supersession

Owner: "it should literally produce a self contained distro/db/repo so we can
continue work in the repo while running jobs". Owner then asked which packager
would include Python itself. Prompt recommended PyInstaller one-folder mode;
owner confirmed: "I think this is better - it ensures we are contained".

Select **PyInstaller one-folder** for the deployed command: application, Python
interpreter, dependency libraries and required package resources ship together.
This explicitly supersedes the preceding zipapp proposal and any runtime option
in OWNER-INSTANCE-DESTINATION-20260916.md that depends on the prepared/shared
venv or system Python. That file's external destination and same-instance-JSON
command contract remain in force. `just setup` remains the development/build
environment preparation; it is not a dependency of the already installed stack.

The intended external instance layout contains:

```text
destination/
  distro/          bundled executable, Python, dependencies and resources
  instance.json    the one lifecycle selector
  db/              separate authority/Job/control/integration stores
  repo/            independent Job repository/target at the selected base
  logs/            logs and published observation
```

Exact internal filenames can follow existing reviewed conventions. Keep process
records, snapshots, workspaces and other mutable execution data instance-local
as well. The deployment includes a real independent repository prepared from the
explicitly selected immutable base, not a Git worktree, symlink, editable source
mount or object alternates pointing into the development checkout. Source edits
and normal development in /home/sl/src/baton must not change the running distro
or Job repository. Do not embed private credential contents or v11 authority
state. Provider credentials, container engine, Git and target OS libraries remain
explicit host prerequisites; bundled Python is not an OS/container sandbox.

Bootstrap prepares the destination and emits instance.json. Start/status/monitor/
stop consume that SAME file and reach the installed executable, deriving the
correct process/log/database paths. Manual exports and the global stack-root
default are superseded as the normal instance selection interface. A deployed
command must also be runnable without the source checkout present; repository
just recipes are convenient dispatchers, not required runtime modules.

Repeated bootstrap and starts must not silently overwrite a running version or
reset state. Bundle identity/provenance stays attached to the instance. Two
independent destinations must not control the same supervisor or mutable stores.
No general upgrade/migration framework is selected; safe refusal is sufficient.

## Bounded implementation guidance

Finish the current small recipe review and preserve its accepted evidence, then
implement this named remaining deployment slice. Pin precise packaging/entry/
bootstrap/recipe/doc/test paths in PLAN before changes. Use a pinned build-tool
dependency in the build environment; avoid adding it to runtime requirements.
Reuse accepted runtime behavior; no scheduler/provider redesign, live-model
qualification or v11 service mutation.

Known packaging boundaries to validate, not assume:

- `rpds-py` in requirements.lock supplies a native extension; include its native
  library and the locked dependency/resource set.
- Existing children use `sys.executable -m tools...`. In a frozen command,
  sys.executable is the application, so provide explicit bundled subcommands
  and verify scheduler/publisher/viewer child dispatch.
- Dynamic factory imports and schema/assets must be available from the bundle;
  avoid checkout-relative file discovery and mutable PYTHONPATH inheritance.
- Capture the exact built platform/artifact identity. This is a host-specific
  distribution, not a claim of universal cross-platform portability.

Focused acceptance: execute the real built command from an unrelated working
directory with source imports and build-venv paths unavailable; prepare an
external fixture instance, start/read/stop empty scheduling through its JSON;
confirm all children use bundled code and two instance selectors cannot cross-
control. Check separate repository/base independence under the operator's Git
ownership boundary. Reuse earlier unchanged behavior evidence; verify actual
packaged composition rather than only mocking the packaging invocation.

No implicit live Jobs. Agent Git restrictions remain; concrete external
installation/repository initialization commands are prepared for the owner
where installed execution authority does not permit them. Do not launch a new
planning or approval campaign for ordinary implementation decisions within this
confirmed scope. Genuine missing source/base or deployment choices are reported
precisely, without substituting proof fixtures as production.

References: Python zipapp docs explain the external-interpreter/native-extension
limits (https://docs.python.org/3/library/zipapp.html). PyInstaller operating mode
docs explain one-folder bundling and platform limits
(https://pyinstaller.org/en/stable/operating-mode.html).

## Later owner interface ruling — 2026-09-16

OWNER-STANDALONE-INTERFACE-20260916.md supersedes public lifecycle JSON arguments
and manual pre-clone steps as the normal user workflow: bootstrap INPUTS
DESTINATION creates the complete deployment, including repositories and its
own justfile; deployed just start/status/monitor/stop resolve local instance.json.
Git mutation remains owner-only through the finished operator-run command.
Earlier technical isolation requirements and evidence remain applicable.
