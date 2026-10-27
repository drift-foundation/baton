import json
from pathlib import Path
from unittest import mock
from tests.tools.test_connected_creation import ConnectedCreationCase
from tools import instance

def probe(kind):
    c=ConnectedCreationCase(); c.setUp()
    try:
        target=Path(c.state)/'install-inputs.json'
        external=Path(c.root)/'foreign.json'
        if kind=='existing': target.write_text('FOREIGN')
        if kind=='temp-symlink':
            external.write_text('FOREIGN')
            Path(str(target)+'.tmp').symlink_to(external)
        if kind=='failed-selector':
            with mock.patch.object(instance,'create',side_effect=instance.InstanceRefusal('injected selector failure')):
                try:c.installed()
                except AssertionError:pass
        else:
            try:c.installed()
            except AssertionError:pass
        return {'kind':kind,'input_exists':target.exists(),'input_symlink':target.is_symlink(),
                'foreign_preserved':external.read_text()=='FOREIGN' if external.exists() else (target.read_text()=='FOREIGN' if target.exists() else None),
                'selector_exists':(Path(c.state)/'instance.json').exists()}
    finally:c.doCleanups()
for kind in ['existing','temp-symlink','failed-selector']:
    print(json.dumps(probe(kind)))
