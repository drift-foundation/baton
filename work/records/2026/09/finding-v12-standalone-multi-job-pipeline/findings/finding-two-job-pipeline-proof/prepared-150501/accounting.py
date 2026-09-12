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
from baton_v12.worker_manager import launch, exchange


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


class BoundJudges:
    def __init__(self, config, *, incarnation, authority, clock, workspace_group=None):
        self.workspace_group = workspace_group
        self.config, self.incarnation, self.authority, self.clock = config, incarnation, authority, clock

    def read(self, status, claims):
        config = self.config
        exclusions, observations, failure = {}, [], None
        if not status:
            return exclusions, observations, failure
        if status.get('schema') != 'baton.v12.job-status/4' or status.get('canonical') is not True or status.get('incarnation') != self.incarnation:
            raise AccountingError('foreign or noncanonical status for accounting')
        rows = intervals(claims, instant(self.clock()))
        stages = {stage['job_id']: stage for job in status['jobs'] for stage in job['stages'] if stage['kind'] == 'integration'}
        root = Path(config['state_root']) / 'result-judgments'
        if not root.exists():
            return exclusions, observations, failure
        if root.is_symlink() or not root.is_dir():
            raise AccountingError('invalid result subject directory')
        # This proof has one derived B result and no retries. A new cardinality is a refusal.
        homes = list(root.iterdir())
        if len(homes) > 1:
            raise AccountingError('unexpected multiple derived results in this proof')
        for home in homes:
            place = home / 'subject.json'
            if not place.exists():
                continue  # Before dispatch, no exclusion.
            subject, _ = document(place)
            if home.name != digest(subject['result_id'])[7:]:
                raise AccountingError('subject locator does not bind its result')
            with IntegrationStore.open_readonly(config['integration_store'], incarnation=self.incarnation, clock=self.clock) as owner:
                held = reconciliation.result_of(owner, subject['result_id'])
            if held['state'] not in ('published', 'authorized', 'imported'):
                raise AccountingError('dispatched subject is not a published result')
            if subject != subject_of(held, self.authority.policy_generation()):
                raise AccountingError('derived subject/result/policy disagree')
            stage = stages.get(held['job_id'])
            bindings = [one for one in config['job_bindings'] if one['job_id'] == held['job_id']]
            if len(bindings) != 1 or stage is None:
                raise AccountingError('result has no exact configured Job')
            binding = bindings[0]
            fixed = held['integration_assignment']
            if (held['authority_uuid'] != config['authority_uuid'] or held['integration_attempt_id'] != stage['attempt_id']
                    or stage['work_id'] != binding['job_work_id'] or held['work_id'] != binding['job_work_id']
                    or held['canonical_target_id'] != binding['canonical_target_id']
                    or held['source_base'] != binding['line_declared_base']
                    or fixed['work_ref'] != {'authority_uuid': config['authority_uuid'], 'work_id': stage['work_id']}
                    or fixed['participant'] != 'baton.proof-integrator'
                    or len([one for one in rows if one['assignment'] == fixed]) != 1):
                raise AccountingError('derived result/Job/stage/assignment binding mismatch')
            configured = config['result_judgment_workers'][held['job_id']]
            if set(configured) != {'verification', 'review', 'approval'}:
                raise AccountingError('all three independent judges are required')
            exclusions[key(fixed)] = []
            for kind, one in configured.items():
                given = one['deployment']
                candidates = [row for row in rows if row['name'] == kind]
                if not candidates:
                    continue
                if len(candidates) != 1:
                    raise AccountingError('unexpected judge claim generation/retry')
                row = candidates[0]
                assignment = row['assignment']
                if (assignment['generation'] != 1 or assignment['participant'] != given['participant'] or assignment['work_ref'] != given['input_manifest']['work_ref']
                        or assignment['work_ref']['authority_uuid'] != config['authority_uuid']):
                    raise AccountingError('judge assignment differs from configured Work/participant')
                judged = dict(subject, kind=kind)
                attempt = 'judgment-' + digest({'subject': judged, 'worker_id': one['worker_id'],
                    'participant': given['participant'], 'input': given['input_manifest']['manifest_digest'],
                    'policy': given['policy_digest'], 'profile': given['profile_digest']})[7:]
                observation = {'kind': kind, 'attempt_id': attempt, 'assignment': assignment, 'result_id': held['result_id'], 'exchange': None, 'verdict': None}
                sealed_path = Path(given['workspace_storage']) / attempt / 'custody' / attempt / 'sealed.json'
                if sealed_path.exists():
                    sealed, _ = document(sealed_path)
                    check_manifest_structure(sealed, 'resultManifest')
                    if sealed['assignment_ref'] != assignment or sealed['result_id'] != 'result-' + attempt:
                        raise AccountingError('sealed judge result belongs to another assignment/attempt')
                    findings = next(one for one in sealed['outputs'] if one['name'] == 'findings')
                    report, raw = document(sealed_path.parent / 'findings/report.json')
                    entries = [entry for entry in findings['content_manifest']['entries'] if entry['path'] == 'report.json']
                    claim = findings['result_metadata']['baton.checkpoint-review/1']
                    if (len(entries) != 1 or entries[0]['bytes'] != len(raw) or entries[0]['content_digest'] != digest_of_bytes(raw)
                            or claim['base'] != subject['source_base'] or claim['head'] != subject['candidate'] or claim['tree'] != subject['tree']
                            or report['schema'] != 'baton.review-report/1' or report['verdict'] != claim['verdict']):
                        raise AccountingError('frozen judgment report/subject mismatch')
                    observation['verdict'] = report['verdict']
                    if sealed['disposition'] != 'completed' or report['verdict'] != 'accepted':
                        failure = failure or dict(observation, ending='answered', disposition='plan-rejected', fault_code=None)
                else:
                    if self.workspace_group is None:
                        raise AccountingError('missing product contract: public read-only worker-manager workspace-group acquisition for derived-judge exchange observation')
                    delivered = launch.adopt(given['launch_home'], attempt_id=attempt,
                        session='session-' + digest(attempt)[7:31], contract=given['launch_contract'], role=given['launch_role'],
                        transport=exchange.EXCHANGE_TRANSPORT, workspace_group=self.workspace_group)
                    if delivered is not None:
                        view = exchange.observation(delivered.exchange)
                        observation['exchange'] = view
                        terminal = view.get('terminal') or {}
                        if view.get('foreign') or view.get('unreadable'):
                            raise AccountingError('required judge exchange is unreadable/foreign')
                        ending = terminal.get('ending')
                        if view.get('receipt') and (ending in ('lost', 'faulted') or ending == 'answered' and terminal.get('disposition') in ('unable', 'cancelled', 'plan-rejected')):
                            failure = failure or dict(observation, ending=ending, disposition=terminal.get('disposition'), fault_code=terminal.get('fault_code'))
                    elif not row['active']:
                        raise AccountingError('ended judge lacks both exchange and frozen report')
                exclusions[key(fixed)].append(assignment)
                observations.append(observation)
        return exclusions, observations, failure


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
