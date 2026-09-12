"""Provide a real temporary source directory for offline document validation.

Only the configured RUN path is substituted. No schema, owner or source-nomination
validator is stubbed. This empty fixture is not a Git baseline or host posture.
"""
from unittest import mock

import deployment


def documents_in_fixture(destination, images, facts):
    root = destination.parent / 'offline-run'
    (root / 'source').mkdir(parents=True, exist_ok=True)
    (root / 'OFFLINE-ONLY.txt').write_text('Temporary source nomination only; not actual run8 inputs, Git baseline or host validation.\n')
    with mock.patch.object(deployment, 'RUN', root):
        return deployment.documents(destination, images, facts)
