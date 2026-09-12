"""Offline image custody checks; no engine/container/provider is executed."""
import io
import json
from pathlib import Path
import tarfile
import unittest

import build_images as images

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'prepared-141676'


def archive_bytes(payload=b'candidate', *, kind=tarfile.REGTYPE, mode=0o644, link=''):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w') as archive:
        member = tarfile.TarInfo('file')
        member.type = kind
        member.mode = mode
        member.linkname = link
        member.size = len(payload) if kind == tarfile.REGTYPE else 0
        archive.addfile(member, io.BytesIO(payload) if kind == tarfile.REGTYPE else None)
    return out.getvalue()


class ImagePreparationTests(unittest.TestCase):
    def test_complete_accepted_context_changes_only_reviewed_adapter(self):
        manifest = json.loads((HERE / 'image-context-manifest.json').read_text())
        old = json.loads((PRIOR / 'image-context-manifest.json').read_text())
        self.assertEqual(set(old), set(manifest))
        for name, expected in manifest.items():
            payload = (HERE / 'image-context' / name).read_bytes()
            self.assertEqual(expected, {'sha256': images.sha(payload), 'bytes': len(payload)})
            if name != 'worker/claude_agent.py':
                self.assertEqual(old[name], expected)
                self.assertEqual((PRIOR / 'image-context' / name).read_bytes(), payload)
        self.assertEqual('sha256:489399897c3f0ae94f06be9da47adde3f05210fa0ecfd7faad295daf6accfe2a', manifest['worker/claude_agent.py']['sha256'])
        self.assertEqual((PRIOR / 'image-context/Dockerfile.provider').read_bytes(), (HERE / 'image-context/Dockerfile.provider').read_bytes())
        for name in ('Dockerfile.provider', 'worker/Dockerfile.integration'):
            lines = (HERE / 'image-context' / name).read_text().splitlines()
            self.assertFalse(any(line.startswith(('RUN ', 'ADD ')) for line in lines))

    def test_static_member_requires_exact_regular_type_size_mode_and_bytes(self):
        expected = {'sha256': images.sha(b'candidate'), 'bytes': 9, 'mode': 0o644}
        self.assertEqual(expected, images.checked_file(archive_bytes(), expected))
        for data in (archive_bytes(b'different'), archive_bytes(b''), archive_bytes(mode=0o755), archive_bytes(kind=tarfile.SYMTYPE, link='secret'), archive_bytes(kind=tarfile.LNKTYPE, link='secret'), archive_bytes(kind=tarfile.DIRTYPE)):
            with self.assertRaises(RuntimeError): images.checked_file(data, expected)
        with self.assertRaises(tarfile.ReadError): images.checked_file(b'not a tar', expected)

    def test_launcher_is_only_verified_metadata_declared_native_executable(self):
        target = '../lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe'
        self.assertEqual('/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe', images.checked_launcher(archive_bytes(kind=tarfile.SYMTYPE, link=target))['target'])
        for data in (archive_bytes(), archive_bytes(kind=tarfile.SYMTYPE, link='/secret'), archive_bytes(kind=tarfile.LNKTYPE, link=target)):
            with self.assertRaises(RuntimeError): images.checked_launcher(data)

    def test_exact_provider_installation_and_independent_helper_bindings(self):
        provenance = json.loads((HERE / 'provider-installation.json').read_text())
        self.assertEqual('2.1.247', provenance['version'])
        self.assertEqual(images.BASE, provenance['immutable_base'])
        self.assertEqual(4, len(provenance['files']))
        native = provenance['files']['/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe']
        self.assertEqual('sha256:5fb321bf417ffc5cd4e3f36e7c9c7e029bf47aaa36d5621db979fcc5e6eabe15', native['sha256'])
        self.assertEqual((250162696, 0o755), (native['bytes'], native['mode']))
        hashes = json.loads((HERE / 'runner-helpers.json').read_text())
        self.assertEqual({'run.py', 'deployment.py', 'target_posture.py', 'failure_observation.py'}, set(hashes))
        for name, expected in hashes.items(): self.assertEqual(expected, images.sha((HERE / name).read_bytes()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
