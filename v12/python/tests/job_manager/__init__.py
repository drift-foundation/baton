"""W71875 — the persistent Job manager's own regressions.

Self-contained on purpose. These cases build their own strict authority
session and their own Job submissions rather than importing another leaf's
fixtures: the manager suite carries live edits from other Work, and a gate
that fails because somebody else's fixture moved is a gate nobody trusts.
"""
