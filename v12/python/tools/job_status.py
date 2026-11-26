"""Instance configuration adapter for the shared durable status API."""
import datetime
import json
from pathlib import Path

from baton_v12.job_manager import read_status
from tools import stage_execution


def read(settings):
    """Read the current configuration and stores; never a cached export."""
    document = json.loads(Path(settings['BATON_V12_STAGE_EXECUTION_CONFIG']).read_text())
    return read_status(settings['BATON_V12_JOB_STORE'],
        authority_uuid=settings['BATON_V12_AUTHORITY_UUID'], incarnation='v12-status-reader',
        clock=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
        control_store=settings['BATON_V12_CONTROL_STORE'],
        observation_factory=lambda jobs, control: stage_execution.observation_from(document, jobs, control))


def source(settings):
    """The bounded viewers accept serialized documents from any read source."""
    return lambda: json.dumps(read(settings)).encode('utf-8')
