"""Selected-source identity replay only; does not certify current operational readiness."""
from pathlib import Path
import sys
from unittest.mock import patch
p=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(p))
import prove
import prepare
selected=prepare.capacity.SOURCE_COMMIT
identity={'root':str(prepare.capacity.REPOSITORY),'commit':selected,'selected':selected,'at_selected_commit':True}
with patch.object(prepare.capacity,'source_identity',return_value=identity):
    prove.main()
