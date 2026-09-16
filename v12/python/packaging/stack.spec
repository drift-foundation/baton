# PyInstaller ONE-FOLDER spec for the deployed v12 stack. W183883.
#
# OWNER-PYINSTALLER-20260916.md: the application, the Python interpreter, the
# dependency libraries and the package resources ship together, so a running
# deployment reads nothing from the development checkout.
#
# WHAT HAS TO BE SAID EXPLICITLY, because PyInstaller finds imports by reading
# code and this distribution resolves several of them at RUN time:
#
#   the operations factories are named as `module:attribute` STRINGS in a
#     deployment document and imported by `importlib`, so nothing static points
#     at them and they are hidden imports here;
#   `jsonschema` selects its validator and its format checkers dynamically;
#   `rpds` is a NATIVE extension with no pure-Python fallback, so its compiled
#     library travels as a binary rather than as source;
#   the frozen JSON Schema assets are package DATA -- they are read from disk at
#     validation time and a bundle without them imports cleanly and then refuses
#     every document it is given.
#
# The build is HOST-SPECIFIC. A one-folder bundle is built for the platform it
# is built on; `baton-v12-stack identity` records what that was rather than
# claiming portability.
import os

HERE = os.path.abspath(os.path.join(SPECPATH, ".."))

# The frozen schema assets, at the same package-relative place the code reads.
SCHEMA = os.path.join(HERE, "src", "baton_v12", "contracts", "schema")

# THE BUILD STAMP IS CAPTURED HERE, once, while the source is in front of us.
# OWNER-VERSION-STAMP-20260916.md: the commit and the dirty flag are observed at
# PACKAGING time and embedded, so an installed build's reported identity cannot
# be changed by later edits and `--version` needs no checkout and no repository
# tool. The reads are `rev-parse` and `status --porcelain`; nothing is written
# to the repository.
import sys as _sys

_sys.path.insert(0, HERE)
from tools import build_stamp as _stamp                      # noqa: E402

STAMP = os.path.join(SPECPATH, _stamp.FILENAME)
_stamp.write(STAMP, _stamp.capture())

hidden = [
    # Resolved from deployment documents by `module:attribute`, never imported
    # by a statement PyInstaller could see.
    "tools.stage_execution", "tools.single_worker", "tools.integration_worker",
    "tools.integration_placement", "tools.integration_bundle",
    "tools.dogfood_operator", "tools.job_manager", "tools.job_viewer",
    "tools.stack", "tools.bootstrap", "tools.instance", "tools.user_credentials",
    "tools.worker_image",
    # The validator's own dynamic selection.
    "jsonschema", "jsonschema_specifications", "referencing", "rpds",
]

analysis = Analysis(
    [os.path.join(HERE, "tools", "stack_command.py")],
    pathex=[HERE, os.path.join(HERE, "src")],
    binaries=[],
    datas=[(SCHEMA, os.path.join("baton_v12", "contracts", "schema")),
           # Beside the bundle's own resources, which is where
           # `build_stamp.stamped()` reads it when frozen.
           (STAMP, ".")],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "unittest.mock"],
    noarchive=False,
)
pure = PYZ(analysis.pure)

executable = EXE(
    pure, analysis.scripts, [],
    exclude_binaries=True,          # ONE-FOLDER: the libraries stay beside it.
    name="baton-v12-stack",
    debug=False, strip=False, upx=False, console=True,
)
COLLECT(executable, analysis.binaries, analysis.datas,
        strip=False, upx=False, name="distro")
