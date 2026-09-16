"""The one place this distribution's application version is written. W183883.

OWNER-VERSION-STAMP-20260916.md: *"introduce a version.py or similar file so
that baton --version can show it"*, with the application version as the
authority and the source commit as separate provenance.

ONE LITERAL, AND THE PACKAGE METADATA FOLLOWS IT. `pyproject.toml` reads
`baton_v12.version.VERSION` rather than repeating a number: two version
literals are two answers to one question, and they drift the first time only
one of them is edited.

NOTHING HERE READS ANYTHING. Importing this module opens no file, runs no
command and needs no checkout: `--version` has to answer on a host where the
development tree and the repository tool are both absent.
"""

# The application version. The owner selected 12.0.0 as the initial one; a
# release or tag beyond that is not implied by this file.
VERSION = "12.0.0"

# What the command calls itself when it says its version. `stack_command.COMMAND`
# is the executable's NAME, which is a longer thing to read in a banner.
PROGRAM = "baton"


def stated(stamp=None):
    """The one-line version banner, with build provenance when there is any.

        baton 12.0.0 (3c0dd082, dirty)
        baton 12.0.0 (3c0dd082)
        baton 12.0.0 (source commit unknown)

    THE THIRD FORM IS NOT AN ERROR AND IS NOT A CLEAN TREE. A build made where
    the repository tool could not answer says so; reporting it as clean would
    be inventing the one fact the stamp exists to carry.
    """
    if not stamp or not stamp.get("commit"):
        detail = "source commit unknown"
        if stamp and stamp.get("detail"):
            detail += ": " + str(stamp["detail"])
    else:
        detail = str(stamp["commit"])[:8]
        if stamp.get("dirty") is True:
            detail += ", dirty"
        elif stamp.get("dirty") is None:
            detail += ", cleanliness unknown"
    return "%s %s (%s)" % (PROGRAM, VERSION, detail)
