"""The Baton v12 trusted host.

Two products ship in this one distribution and remain separate in every way
that matters: the assignment AUTHORITY (`baton_v12.authority`) and, later, the
Worker MANAGER.  They keep separate modules, separate SQLite files, separate
connections, separate schemas and separate transactions.  Packaging them
together does not grant the manager authority ownership.
"""

__all__ = []
