"""Owner150498: proof-only clocks and public read-only judge observations.

No serving factory, control-store connection, SQL, credential read, or transition.
The retained subject locates a result; only its public owner can bind that result.
"""
from datetime import datetime
import math
import os
from pathlib import Path
import stat
import json

from baton_v12.contracts import digest, digest_of_bytes
from baton_v12.contracts.manifest import check_manifest_structure
from baton_v12.integration import IntegrationStore, reconciliation
from baton_v12.worker_manager import (ControlStore, launch, exchange, attempt_runtime_of,
    assignment_of, frozen_output_of, attempt_preparation_failure_of, attempt_start_failure_of)
from baton_v12.worker_manager.workspaces import configured_workspace_group
from baton_v12.worker_manager.intake import intake_receipt_of
from baton_v12.worker_manager.manifests import load_manifest
from urllib.parse import urlsplit, unquote


class AccountingError(RuntimeError):
    pass


class BudgetExpired(TimeoutError):
    def __init__(self, clock):
        self.clock = clock
        super().__init__('approved deadline reached: ' + clock['kind'])


class BudgetWake(Exception):
    """Re-observe a potentially ended/paused clock; never call this a failure."""


def instant(text):
    answer = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if answer.tzinfo is None:
        raise AccountingError('an accounting timestamp has no timezone')
    return answer.timestamp()


def key(assignment):
    return json.dumps(assignment, sort_keys=True, separators=(',', ':'))


def intervals(claims, now):
    answer = []
    for name, history in claims.items():
        events = history['events']
        seen = set()
        for index, event in enumerate(events):
            if event['cause'] != 'claimed':
                continue
            assignment = event['assignment_ref']
            identity = key(assignment)
            if identity in seen:
                raise AccountingError('duplicate claim identity')
            seen.add(identity)
            ending = next((later for later in events[index + 1:] if later['assignment_ref'] == assignment), None)
            start = instant(event['at'])
            end = instant(ending['at']) if ending else now
            if end < start or end > now or start > now:
                raise AccountingError('inconsistent claim timestamps')
            if ending is None and history['current'] != assignment:
                raise AccountingError('unended claim is not the current assignment')
            answer.append({'name': name, 'assignment': assignment, 'start': start, 'end': end,
                           'active': ending is None, 'ending': ending['cause'] if ending else None})
        if history['current'] is not None and key(history['current']) not in seen:
            raise AccountingError('public owner supplied no matching claim timestamp')
    return answer


def union_seconds(ranges):
    total, end = 0.0, None
    for lo, hi in sorted(ranges):
        if hi < lo:
            raise AccountingError('reversed exclusion')
        total += max(0, hi - max(lo, end if end is not None else lo))
        end = hi if end is None else max(end, hi)
    return total


def evaluate(claims, exclusions, *, now, elapsed, limits):
    """Exclusions come only from BoundJudges.read; completed claims use same math."""
    whole = {'kind': 'whole-run', 'limit': 1200, 'charged': elapsed,
             'excluded': 0, 'remaining': 1200 - elapsed, 'assignment': None}
    if elapsed < 0 or not math.isfinite(elapsed):
        raise AccountingError('invalid whole-run duration')
    if whole['remaining'] <= 0:
        raise BudgetExpired(whole)
    rows = intervals(claims, now)
    by_assignment = {key(row['assignment']): row for row in rows}
    clocks = [whole]
    for row in rows:
        identity = key(row['assignment'])
        ranges, paused = [], False
        for judge in exclusions.get(identity, []):
            fixed = by_assignment.get(key(judge))
            if fixed is None or fixed['name'] not in ('verification', 'review', 'approval'):
                raise AccountingError('exclusion has no exact derived judge claim')
            lo, hi = max(row['start'], fixed['start']), min(row['end'], fixed['end'])
            if hi >= lo:
                ranges.append((lo, hi))
            paused = paused or row['active'] and fixed['active']
        excluded = union_seconds(ranges)
        charged = row['end'] - row['start'] - excluded
        limit = limits[row['assignment']['participant']]
        if excluded and limit != 120:
            raise AccountingError('only integration can exclude judge time')
        remaining = limit - charged
        clock = dict(row, kind='integration' if limit == 120 else 'attempt', limit=limit,
                     charged=charged, excluded=excluded, paused=paused,
                     remaining=remaining, exclusions=ranges)
        # Completed exactly-at-limit claims are legal; active exactly-at-limit are not.
        if remaining < 0 or row['active'] and remaining <= 0:
            raise BudgetExpired(clock)
        if row['active']:
            clocks.append(dict(clock, alarm_remaining=None if paused else remaining))
    if whole['remaining'] <= 0:
        raise BudgetExpired(whole)
    winner = min((one for one in clocks if one.get('alarm_remaining', one['remaining']) is not None), key=lambda one: one.get('alarm_remaining', one['remaining']))
    return {'winner': winner, 'remaining': winner.get('alarm_remaining', winner['remaining']), 'clocks': clocks}


def final_timeout(elapsed):
    left = 1200 - elapsed
    if left <= 0:
        raise BudgetExpired({'kind': 'whole-run', 'limit': 1200, 'charged': elapsed, 'remaining': left})
    return min(30, left)


def document(path):
    """Bounded regular file and no symlinks at any path component."""
    path = Path(path)
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        child = os.open(path.name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=fd)
        try:
            if not stat.S_ISREG(os.fstat(child).st_mode):
                raise AccountingError('accounting evidence is not a regular file')
            with os.fdopen(child, 'rb', closefd=False) as stream:
                raw = stream.read(65537)
            if len(raw) > 65536:
                raise AccountingError('accounting evidence exceeds64KiB')
        finally:
            os.close(child)
    finally:
        os.close(fd)
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise AccountingError('duplicate accounting document member')
            result[name] = value
        return result
    def invalid(_):
        raise AccountingError('nonfinite accounting document value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid), raw


def subject_of(held, policy):
    names = ('result_id', 'job_id', 'canonical_target_id', 'derived_proposal_id', 'derived_result_id',
             'derived_result_digest', 'content_digest', 'target_revision', 'source_proposal_id',
             'source_base', 'source_candidate', 'causal_observations', 'observed_by')
    return dict({name: held[name] for name in names}, candidate=held['prepared']['head'],
                tree=held['prepared']['tree'], policy_generation=policy)


def read_claims(authority, works):
    """Bracket public reads with the append-only owner history; no private snapshot."""
    result = {}
    for name, work_id in works.items():
        before = authority.assignment_events(work_id)
        current = authority.assignment_of(work_id)
        after = authority.assignment_events(work_id)
        if before != after:
            raise BudgetWake()
        result[name] = {'current': current, 'events': after}
    return result


class BoundJudges:
    def __init__(self, config, *, incarnation, authority, clock, control_path):
        self.config, self.incarnation, self.authority, self.clock = config, incarnation, authority, clock
        self.control_path = str(control_path)

    def read(self, status, claims):
        config = self.config
        if not status:
            return {}, [], None
        if status.get('schema') != 'baton.v12.job-status/4' or status.get('canonical') is not True or status.get('incarnation') != self.incarnation:
            raise AccountingError('foreign or noncanonical status for accounting')
        root = Path(config['state_root']) / 'result-judgments'
        if not root.exists():
            return {}, [], None
        if root.is_symlink() or not root.is_dir():
            raise AccountingError('invalid result subject directory')
        homes = list(root.iterdir())
        if len(homes) > 1:
            raise AccountingError('unexpected multiple derived results in this proof')
        exclusions, observations = {}, []
        for home in homes:
            place = home / 'subject.json'
            if not place.exists():
                continue
            subject, _ = document(place)
            if home.name != digest(subject['result_id'])[7:]:
                raise AccountingError('subject locator does not bind its result')
            policy = self.authority.policy_generation()
            held = self.result(subject['result_id'])
            if self.authority.policy_generation() != policy:
                raise BudgetWake()
            fixed, configured = self.bind_result(status, claims, subject, held, policy)
            with ControlStore.open_readonly(self.control_path, incarnation=self.incarnation, clock=self.clock) as manager:
                with manager.snapshot():
                    group = configured_workspace_group(manager)
                    rows = intervals(claims, instant(self.clock()))
                    exclusions[key(fixed)] = []
                    for kind, one in configured.items():
                        candidates = [row for row in rows if row['name'] == kind]
                        if not candidates:
                            continue
                        if len(candidates) != 1:
                            raise AccountingError('unexpected judge claim generation/retry')
                        row = candidates[0]
                        observed = self.judge(manager, group, subject, kind, one, row)
                        if observed is None:
                            continue  # Claimed but not activated: no exclusion until the owner binds it.
                        observations.append(observed)
                        if observed.get('failure'):
                            return exclusions, observations, observed
                        exclusions[key(fixed)].append(row['assignment'])
            # A serving import can advance policy or custody while these owners
            # are read. Discard every dependent fact; do not decide from a mix.
            if self.result(subject['result_id']) != held or self.authority.policy_generation() != policy:
                raise BudgetWake()
        return exclusions, observations, None

    def result(self, result_id):
        with IntegrationStore.open_readonly(self.config['integration_store'], incarnation=self.incarnation, clock=self.clock) as owner:
            return reconciliation.result_of(owner, result_id)

    def bind_result(self, status, claims, subject, held, observed_policy):
        config = self.config
        rows = intervals(claims, instant(self.clock()))
        stages = {stage['job_id']: stage for job in status['jobs'] for stage in job['stages'] if stage['kind'] == 'integration'}
        # Import releases the lease and can advance current policy. The public
        # result reader proves its committed evidence/import chain; terminal
        # observation binds that retained approval generation, not a new grant.
        policy = held['policy_generation'] if held['state'] == 'imported' else observed_policy
        if held['state'] not in ('published', 'authorized', 'imported') or subject != subject_of(held, policy):
            raise AccountingError('derived subject/result/policy disagree')
        stage = stages.get(held['job_id'])
        bindings = [one for one in config['job_bindings'] if one['job_id'] == held['job_id']]
        integrators = [one for one in config['workers'] if one['role'] == 'integration']
        if len(bindings) != 1 or len(integrators) != 1 or stage is None:
            raise AccountingError('result has no exact configured Job/integrator')
        binding = bindings[0]
        fixed = held['integration_assignment']
        if (held['authority_uuid'] != config['authority_uuid'] or held['integration_attempt_id'] != stage['attempt_id']
                or stage['work_id'] != binding['job_work_id'] or held['work_id'] != binding['job_work_id']
                or stage['stage_id'] != held['job_id'] + '/integration' or stage['episode'] != 1
                or stage['offer_id'] != 'offer-' + stage['attempt_id'].removeprefix('attempt-')
                or held['canonical_target_id'] != binding['canonical_target_id']
                or held['source_base'] != binding['line_declared_base']
                or fixed['work_ref'] != {'authority_uuid': config['authority_uuid'], 'work_id': stage['work_id']}
                or fixed['participant'] != integrators[0]['deployment']['participant']
                or len([one for one in rows if one['assignment'] == fixed]) != 1):
            raise AccountingError('derived result/Job/stage/assignment binding mismatch')
        configured = config['result_judgment_workers'][held['job_id']]
        if set(configured) != {'verification', 'review', 'approval'}:
            raise AccountingError('all three independent judges are required')
        if len({one['deployment']['participant'] for one in configured.values()}) != 3 or len({one['deployment']['principal'] for one in configured.values()}) != 3:
            raise AccountingError('derived judges must be independent configured participants/principals')
        return fixed, configured

    def judge(self, manager, group, subject, kind, one, row):
        given, assignment = one['deployment'], row['assignment']
        if (assignment['generation'] != 1 or assignment['participant'] != given['participant']
                or assignment['work_ref'] != given['input_manifest']['work_ref']
                or assignment['work_ref']['authority_uuid'] != self.config['authority_uuid']):
            raise AccountingError('judge assignment differs from configured Work/participant')
        judged = dict(subject, kind=kind)
        attempt = 'judgment-' + digest({'subject': judged, 'worker_id': one['worker_id'], 'participant': given['participant'],
            'input': given['input_manifest']['manifest_digest'], 'policy': given['policy_digest'], 'profile': given['profile_digest']})[7:]
        runtime = attempt_runtime_of(manager, attempt)
        if runtime is None or runtime['assignment'] is None:
            if row['active']:
                return None
            raise AccountingError('ended judge has no activated owner assignment')
        fixed = assignment_of(manager, attempt)
        if runtime['assignment'] != assignment or fixed['principal'] != given['principal']:
            raise AccountingError('judge runtime/Authority/principal binding mismatch')
        observation = {'kind': kind, 'job_id': subject['job_id'], 'attempt_id': attempt, 'assignment': assignment,
                       'result_id': subject['result_id'], 'runtime_id': runtime['runtime_id'], 'exchange': None,
                       'verdict': None, 'failure': False, 'artifacts': []}
        for kind_of_failure, reader in (('preparation', attempt_preparation_failure_of), ('start', attempt_start_failure_of)):
            if reader(manager, attempt) is not None:
                return dict(observation, failure=True, ending=kind_of_failure, disposition=None, fault_code=None)
        frozen = frozen_output_of(manager, attempt)
        receipt = intake_receipt_of(manager, attempt)
        if receipt is not None and receipt['custody'] != 'accepted':
            return dict(observation, failure=True, ending='intake', disposition=receipt['custody'], fault_code=None)
        if frozen is not None and receipt is not None:
            if frozen['disposition'] != 'completed':
                return dict(observation, failure=True, ending='frozen', disposition=frozen['disposition'], fault_code=None)
            result = load_manifest(manager, frozen['manifest_digest'], 'resultManifest')
            if (result is None or result['assignment_ref'] != assignment or result['result_id'] != frozen['result_id']
                    or receipt['assignment'] != assignment or receipt['result_id'] != frozen['result_id']
                    or receipt['manifest_digest'] != frozen['manifest_digest']
                    or result['input_manifest_digest'] != given['input_manifest']['manifest_digest']):
                raise AccountingError('frozen judge result/intake/assignment mismatch')
            outputs = {output['name']: output for output in result['outputs']}
            for name in ('findings', 'logs'):
                output = outputs.get(name)
                if output is None or output['status'] != 'present' or output['artifact'] is None or output['content_manifest'] is None:
                    raise AccountingError('judge did not freeze findings and logs')
                artifacts = [artifact for artifact in receipt['artifacts'] if artifact['artifact_id'] == output['artifact']['artifact_id']]
                if len(artifacts) != 1 or artifacts[0]['content_digest'] != output['content_manifest']['tree_digest']:
                    raise AccountingError('judge output differs from accepted custody')
            findings = outputs['findings']
            artifact = next(artifact for artifact in receipt['artifacts'] if artifact['artifact_id'] == findings['artifact']['artifact_id'])
            locator = urlsplit(artifact['custody_locator'])
            if locator.scheme != 'file' or locator.netloc or locator.query or locator.fragment:
                raise AccountingError('judge report needs exact local accepted custody')
            report, raw = document(Path(unquote(locator.path)) / 'report.json')
            entries = [entry for entry in findings['content_manifest']['entries'] if entry['path'] == 'report.json']
            claim = (findings.get('result_metadata') or {}).get('baton.checkpoint-review/1')
            if (type(claim) is not dict or set(claim) != {'base', 'head', 'tree', 'verdict'}
                    or claim['base'] != subject['source_base'] or claim['head'] != subject['candidate'] or claim['tree'] != subject['tree']
                    or len(entries) != 1 or entries[0]['bytes'] != len(raw) or entries[0]['content_digest'] != digest_of_bytes(raw)
                    or set(report) != {'schema', 'verdict', 'findings'} or report['schema'] != 'baton.review-report/1'
                    or report['verdict'] != claim['verdict'] or report['verdict'] not in ('accepted', 'rejected', 'changes-requested')
                    or type(report['findings']) is not str):
                raise AccountingError('frozen judgment report/subject mismatch')
            if any('baton.checkpoint-review/1' in (output.get('result_metadata') or {}) for name, output in outputs.items() if name != 'findings'):
                raise AccountingError('competing judgment report claims')
            return dict(observation, verdict=report['verdict'], failure=report['verdict'] != 'accepted',
                        ending='frozen', disposition=report['verdict'], fault_code=None,
                        manifest_digest=frozen['manifest_digest'], receipt_digest=receipt['receipt_digest'])
        delivered = launch.adopt(given['launch_home'], attempt_id=attempt, session='session-' + digest(attempt)[7:31],
            contract=given['launch_contract'], role=given['launch_role'], transport=exchange.EXCHANGE_TRANSPORT, workspace_group=group)
        if delivered is None:
            if row['active'] and runtime['runtime_id'] is None:
                return observation
            # Snapshot may precede cleanup while launch removal follows it. Retry
            # fresh owners; if custody never appears the active judge clock still expires.
            raise BudgetWake()
        view = exchange.observation(delivered.exchange)
        if view.get('foreign') or view.get('unreadable'):
            raise AccountingError('required judge exchange is unreadable/foreign')
        terminal = view.get('terminal') or {}
        ending, disposition, fault = terminal.get('ending'), terminal.get('disposition'), terminal.get('fault_code')
        failed = bool(view.get('receipt')) and (ending == 'lost' or ending == 'faulted' and fault in exchange.FAULT_CODES or
            ending == 'answered' and disposition in ('unable', 'cancelled', 'plan-rejected'))
        return dict(observation, exchange=view, failure=failed, ending=ending, disposition=disposition, fault_code=fault,
                    sequence_id=view.get('sequence_id'), manifest_digest=terminal.get('manifest_digest'))


class Alarm:
    """A stale attempt alarm asks for fresh owners; only whole expiry is final here."""
    def __init__(self, *, started, monotonic, set_timer, record, persist):
        self.started, self.monotonic, self.set_timer = started, monotonic, set_timer
        self.record, self.persist = record, persist

    def whole(self):
        elapsed = self.monotonic() - self.started
        final_timeout(elapsed)
        self.arm({'winner': {'kind': 'whole-run', 'limit': 1200, 'charged': elapsed,
                            'remaining': 1200 - elapsed}, 'remaining': 1200 - elapsed})

    def arm(self, chosen):
        self.record['budget_clock'] = chosen
        self.persist(chosen)  # Evidence is retained before the chosen alarm is armed.
        self.set_timer(max(0.001, chosen['remaining']))

    def __call__(self, _signum, _frame):
        elapsed = self.monotonic() - self.started
        if elapsed >= 1200:
            raise BudgetExpired({'kind': 'whole-run', 'limit': 1200, 'charged': elapsed, 'remaining': 1200 - elapsed})
        # The timer may describe a claim that just ended or began judging. Never
        # turn that stale sampling hint into a definitive failure. Re-arm whole
        # before unwinding a bounded read; the loop obtains fresh owner facts.
        self.set_timer(1200 - elapsed)
        raise BudgetWake()
