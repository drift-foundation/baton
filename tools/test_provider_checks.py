"""Fake CLI checks only: never contacts a provider or reads real auth files."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('provider_checks', ROOT / 'tools/provider_checks.py')
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)
FAKE = r'''
import argparse,json,os,sys,time,signal
from pathlib import Path
provider=Path(sys.argv[0]).name
home=os.environ.get('CODEX_HOME' if provider=='codex' else 'CLAUDE_CONFIG_DIR')
mode=Path(home).name
phase='usage' if sys.argv[1]=='app-server' else 'login' if sys.argv[1] in ('login','auth') else 'live'
# Model the documented optional positional prompt and greedy <configs...>.
# argparse owns the parsing: the fake does not just look for a sentinel flag.
if provider=='claude' and phase=='live':
 parser=argparse.ArgumentParser()
 parser.add_argument('--print',action='store_true')
 parser.add_argument('--verbose',action='store_true')
 parser.add_argument('--output-format')
 parser.add_argument('--no-session-persistence',action='store_true')
 parser.add_argument('--tools',nargs='+')
 parser.add_argument('--disable-slash-commands',action='store_true')
 parser.add_argument('--setting-sources')
 parser.add_argument('--settings')
 parser.add_argument('--strict-mcp-config',action='store_true')
 parser.add_argument('--mcp-config',nargs='+')
 parser.add_argument('prompt',nargs='?')
 parsed=parser.parse_args(sys.argv[1:])
 try:
  for value in parsed.mcp_config:
   if json.loads(value)!={'mcpServers':{}}:raise ValueError()
 except (ValueError,TypeError):
  print('Error: Invalid MCP configuration: private-path DO-NOT-PRINT',file=sys.stderr)
  sys.exit(1)
 if not parsed.prompt:
  print('error: missing required argument prompt',file=sys.stderr);sys.exit(1)
with open(os.environ['CHECK_RECORD'],'a') as f:
 f.write(json.dumps({'provider':provider,'home':home,'phase':phase,'argv':sys.argv[1:],
 'overrides':{k:os.environ[k] for k in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','CLAUDE_CODE_OAUTH_TOKEN','OPENAI_BASE_URL') if k in os.environ},'cwd':os.getcwd()})+'\n')
if mode in ('hang','interrupt'):
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 pid=os.fork()
 if pid==0:
  while True: time.sleep(1)
 Path(os.environ['CHILD_PID']).write_text(str(pid))
 while True: time.sleep(1)
if phase=='usage':
 assert sys.argv[1:]==['app-server','--listen','stdio://']
 first=json.loads(sys.stdin.readline())
 assert first['id']==1 and first['method']=='initialize'
 assert first['params']['clientInfo']['name']=='baton_provider_checks'
 print(json.dumps({'method':'account/rateLimits/updated','params':{'DO-NOT-PRINT':True}}),flush=True)
 print(json.dumps({'id':99,'result':{}}),flush=True)
 print(json.dumps({'id':1,'result':{}}),flush=True)
 assert json.loads(sys.stdin.readline())['method']=='initialized'
 assert json.loads(sys.stdin.readline())=={'id':2,'method':'account/rateLimits/read'}
 if mode=='rpc-error':print(json.dumps({'id':2,'error':{'message':'DO-NOT-PRINT'}}),flush=True)
 elif mode=='rpc-malformed':print('DO-NOT-PRINT',flush=True)
 elif mode=='rpc-overflow':print('x'*1100000,flush=True)
 elif mode=='rpc-exit':sys.exit(0)
 elif mode=='rpc-timeout':
  signal.signal(signal.SIGTERM,signal.SIG_IGN)
  pid=os.fork()
  if pid==0:
   while True:time.sleep(1)
  Path(os.environ['CHILD_PID']).write_text(str(pid))
 else:
  print(json.dumps({'id':2,'result':{'rateLimitsByLimitId':{'codex':{
   'primary':{'usedPercent':20,'windowDurationMins':10080,'resetsAt':2000000000},
   'secondary':{'usedPercent':75.5,'windowDurationMins':300,'resetsAt':2000000000},
   'credits':{'balance':'DO-NOT-PRINT'}}}}}),flush=True)
 while True:time.sleep(1)
if phase=='login':
 if provider=='codex':
  print('Not logged in' if mode=='auth' else 'Logged in using ChatGPT',file=sys.stderr)
  sys.exit(1 if mode=='auth' else 0)
 print(json.dumps({'loggedIn':mode!='auth','secret':'DO-NOT-PRINT'}));sys.exit(0)
if mode=='quota':
 print(json.dumps({'type':'error','message':'usage limit reached DO-NOT-PRINT'}));sys.exit(1)
if mode=='auth':
 print('authentication failed DO-NOT-PRINT',file=sys.stderr);sys.exit(1)
if mode=='malformed':print('DO-NOT-PRINT');sys.exit(0)
if mode=='overflow':print('x'*1100000);sys.exit(0)
if provider=='claude':
 assert parsed.output_format=='stream-json' and parsed.verbose
 print(json.dumps({'type':'system','subtype':'init','session_id':mode}))
 if mode=='quota-stream':
  print(json.dumps({'type':'rate_limit_event','session_id':mode,'rate_limit_info':{'rateLimitType':'five_hour','utilization':.13,'resetsAt':2000000000,'status':'allowed'}}))
 print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':'Pong! Ready.','session_id':mode}))
else:
 print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Pong! Ready.'}}))
 print(json.dumps({'type':'turn.completed','usage':{}}))
'''


class ProviderChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='provider-check-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for provider in ('codex', 'claude'):
            p = self.bin / provider
            p.write_text('#!' + sys.executable + '\n' + FAKE)
            p.chmod(0o700)
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                        HOME=str(self.root), XDG_CONFIG_HOME=str(self.root / 'configuration'), XDG_RUNTIME_DIR=str(self.root),
                        CHECK_RECORD=str(self.root / 'calls'), CHILD_PID=str(self.root / 'child'),
                        CODEX_HOME='/must-not-inherit', CLAUDE_CONFIG_DIR='/must-not-inherit',
                        OPENAI_API_KEY='DO-NOT-PRINT', ANTHROPIC_API_KEY='DO-NOT-PRINT',
                        CLAUDE_CODE_OAUTH_TOKEN='DO-NOT-PRINT', OPENAI_BASE_URL='https://wrong.invalid')
        self.env.pop('PROVIDER_CHECKS_CONFIG', None)

    def config(self, entries):
        accounts=[]
        for provider, mode in entries:
            home=self.root / 'homes with spaces' / mode
            home.mkdir(parents=True,exist_ok=True)
            accounts.append({'provider':provider,'label':provider+' '+mode,'home':str(home)})
        path=self.root / 'config with spaces $(false).json'
        path.write_text(json.dumps({'accounts':accounts}))
        return path

    def invoke(self, path=None, timeout='2', command=None):
        argv=command or [sys.executable,'-B',str(ROOT/'tools/provider_checks.py'),'--timeout',timeout]
        if path:argv += ['--config',str(path)]
        return subprocess.run(argv,env=self.env,cwd=ROOT,capture_output=True,text=True,timeout=10)

    def calls(self):
        return [json.loads(line) for line in (self.root/'calls').read_text().splitlines()]

    def test_aggregate_just_entrypoint_spaces_and_environment(self):
        path=self.config([('codex','good'),('claude','good')])
        just=shutil.which('just')
        self.assertIsNotNone(just, 'just is required to verify the real recipe')
        result=self.invoke(command=[just,'provider-checks',str(path)])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('4 checks, 0 failed',result.stdout)
        calls=self.calls();self.assertEqual(len(calls),5)
        for call in calls:
            self.assertIn('homes with spaces',call['home'])
            self.assertEqual(call['overrides'],{})
            self.assertNotEqual(call['cwd'],str(ROOT))
        self.assertIn('--ignore-user-config',calls[1]['argv'])
        self.assertIn('--no-session-persistence',calls[4]['argv'])
        self.assertNotIn('DO-NOT-PRINT',result.stdout+result.stderr)

    def test_mixed_outcomes_continue_and_do_not_expose_diagnostics(self):
        p=self.config([('codex','quota'),('claude','auth'),('codex','malformed'),('claude','good')])
        result=self.invoke(p)
        self.assertEqual(result.returncode,1)
        for word in ('usage-limited','not-logged-in','authentication-error','inconclusive','[claude/claude good]\n  login: ok; live: ok'):
            self.assertIn(word,result.stdout)
        self.assertEqual(len(self.calls()),10)
        self.assertNotIn('DO-NOT-PRINT',result.stdout+result.stderr)

    def test_default_locator_and_default_homes_ignore_inherited_homes(self):
        for name in ('.codex','.claude'):(self.root/name).mkdir()
        p=Path(self.env['XDG_CONFIG_HOME'])/'baton/provider-checks.json'
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'accounts':[{'provider':v,'label':v} for v in ('codex','claude')]}))
        self.assertEqual(self.invoke().returncode,0)
        self.assertEqual({c['home'] for c in self.calls()},{str(self.root/'.codex'),str(self.root/'.claude')})
        with patch.dict(os.environ,self.env,clear=True):
            before=dict(os.environ);checks.child_environment('codex','/selected');self.assertEqual(dict(os.environ),before)

    def test_missing_and_invalid_config_fail_before_any_cli(self):
        self.assertEqual(self.invoke().returncode,2)
        p=self.root/'bad.json'
        for doc in ({'accounts':[]},{'accounts':[{'provider':'other','label':'bad'}]}, {'accounts':[{'provider':'codex','label':'ok','home':'relative'}]}):
            p.write_text(json.dumps(doc));self.assertEqual(self.invoke(p).returncode,2)
        self.assertFalse((self.root/'calls').exists())

    def test_missing_cli_and_home_continue(self):
        p=self.config([('codex','good'),('claude','good')])
        self.env['PATH']=str(self.bin)
        (self.bin/'codex').unlink()
        result=self.invoke(p)
        self.assertEqual(result.returncode,1)
        self.assertIn('missing-cli',result.stdout)
        self.assertIn('[claude/claude good]\n  login: ok; live: ok',result.stdout)
        doc=json.loads(p.read_text());doc['accounts'][0]['home']=str(self.root/'absent');p.write_text(json.dumps(doc))
        self.assertIn('missing-home',self.invoke(p).stdout)

    def child_stopped(self):
        pid=int((self.root/'child').read_text())
        for _ in range(50):
            status=Path(f'/proc/{pid}/stat')
            if not status.exists() or status.read_text().split()[2]=='Z':return
            time.sleep(.02)
        self.fail('fake descendant survived check cleanup')

    def test_timeout_cleans_process_group_and_continues(self):
        result=self.invoke(self.config([('codex','hang'),('claude','good')]),timeout='.2')
        self.assertEqual(result.returncode,1)
        self.assertIn('timeout',result.stdout)
        self.assertIn('[claude/claude good]\n  login: ok; live: ok',result.stdout)
        self.child_stopped()

    def test_sigterm_cleans_process_group(self):
        p=self.config([('codex','interrupt')])
        proc=subprocess.Popen([sys.executable,'-B',str(ROOT/'tools/provider_checks.py'),'--config',str(p)],env=self.env,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            deadline=time.monotonic()+3
            while not (self.root/'child').exists() and time.monotonic()<deadline:time.sleep(.02)
            self.assertTrue((self.root/'child').exists())
            proc.send_signal(signal.SIGTERM)
            out,err=proc.communicate(timeout=3)
            self.assertEqual(proc.returncode,130,err)
            self.child_stopped()
        finally:
            if proc.poll() is None:proc.kill();proc.wait()
            proc.stdout.close();proc.stderr.close()

    def test_claude_variadic_parser_rejects_old_vector_accepts_delimited_prompt(self):
        path = self.config([('claude', 'good')])
        home = json.loads(path.read_text())['accounts'][0]['home']
        with patch.dict(os.environ, self.env, clear=True):
            env = checks.child_environment('claude', home)
        corrected = checks.commands('claude')[1]
        old = corrected.copy()
        old.remove('--')
        rejected = checks.run(old, env, str(self.root), 2)
        self.assertEqual(rejected[0], 1)
        self.assertIn('Invalid MCP configuration', rejected[2])
        self.assertTrue(checks.classify('claude', 'live', rejected).startswith('invocation-error (MCP config;'))
        accepted = checks.run(corrected, env, str(self.root), 2)
        self.assertEqual(checks.classify('claude', 'live', accepted), 'ok')
        call = self.calls()[-1]
        self.assertEqual(call['argv'][-2:], ['--', checks.PROMPT])

    def test_safe_local_invocation_diagnostics_and_unknown_exit(self):
        cases = [
            ('Error: Invalid MCP configuration: DO-NOT-PRINT', 'MCP config'),
            ('--mcp-config validation failed: DO-NOT-PRINT', 'MCP config'),
            ('Error: Invalid JSON provided to --settings DO-NOT-PRINT', 'settings'),
            ("error: unknown option 'DO-NOT-PRINT'", 'CLI options'),
        ]
        for diagnostic, category in cases:
            with self.subTest(category=category):
                verdict = checks.classify('claude', 'live', (1, '', diagnostic, None))
                self.assertIn('invocation-error (' + category, verdict)
                self.assertIn('docs/PROVIDER-CHECKS.md', verdict)
                self.assertNotIn('DO-NOT-PRINT', verdict)
        result = checks.classify('claude', 'live', (7, '', 'DO-NOT-PRINT unknown failure', None))
        self.assertIn('exit=7', result)
        self.assertNotIn('DO-NOT-PRINT', result)
        # A successful model response quoting an error is not a parser failure.
        out = json.dumps({'type':'result','subtype':'success','is_error':False,
                          'result':'unknown option: this is only text'})
        self.assertEqual(checks.classify('claude', 'live', (0, out, '', None)), 'ok')

    def test_usage_rpc_and_missing_claude_windows(self):
        result = self.invoke(self.config([('codex', 'good'), ('claude', 'good')]))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Session: 24.5% remaining; resets 2033-05-18 03:33:20 UTC', result.stdout)
        self.assertIn('Weekly: 80% remaining', result.stdout)
        self.assertRegex(result.stdout, r'Report completed: \d{4}-\d\d-\d\d \d\d:\d\d:\d\d UTC')
        self.assertNotIn('unavailable', result.stdout)
        self.assertNotIn('credits', result.stdout)
        self.assertEqual(result.stdout.count('Report completed:'), 1)
        self.assertTrue(result.stdout.splitlines()[-1].startswith('Report completed:'))
        self.assertNotIn('Observed:', result.stdout)
        for field in ('remaining=', 'window_minutes=', 'source=', 'status=', 'unknown'):
            self.assertNotIn(field, result.stdout)
        self.assertEqual([c['phase'] for c in self.calls()], ['login', 'live', 'usage', 'login', 'live'])
        self.assertNotIn('DO-NOT-PRINT', result.stdout + result.stderr)

    def test_usage_failures_are_unknown_not_login_failures(self):
        for mode, status in [('rpc-error', 'provider rejected the usage query'), ('rpc-malformed', 'invalid or interrupted provider response'),
                             ('rpc-exit', 'provider returned no usage response'), ('rpc-overflow', 'provider response exceeded the size limit'),
                             ('rpc-timeout', 'provider query timed out')]:
            with self.subTest(mode=mode):
                result = self.invoke(self.config([('codex', mode)]), timeout='.3')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn('Usage unavailable:', result.stdout)
                self.assertNotIn(status, result.stdout)
                self.assertNotIn('Session:', result.stdout)
                self.assertNotIn('Weekly:', result.stdout)
                self.assertIn('2 checks, 0 failed', result.stdout)
                self.assertNotIn('DO-NOT-PRINT', result.stdout + result.stderr)
        self.child_stopped()

    def test_claude_collects_from_existing_live_process_only(self):
        result = self.invoke(self.config([('claude', 'quota-stream'), ('claude', 'good')]))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Session: 87% remaining; resets 2033-05-18 03:33:20 UTC', result.stdout)
        self.assertNotIn('Weekly:', result.stdout)
        self.assertIn('[claude/claude good]\n  login: ok; live: ok\n2 accounts', result.stdout)
        self.assertEqual([c['phase'] for c in self.calls()], ['login', 'live', 'login', 'live'])
        self.assertTrue(all(c['overrides'] == {} for c in self.calls()))

    def test_an_unsuccessful_stream_without_a_terminal_result_is_still_classified(self):
        """R1: a recognized diagnostic on stdout must not be lost.

        `claude_events` answers no unique terminal result for an error-only
        stream AND for conflicting results. Both stay unsuccessful; what this
        case adds is that the provider's own diagnostic is still categorized,
        and that an unknown one stays unclassified without disclosure.
        """
        def live(code, out, err=''):
            return checks.classify('claude', 'live', (code, out, err, None))

        def error(message):
            return json.dumps({'type': 'error', 'message': message})

        self.assertEqual(live(1, error('usage limit reached')), 'usage-limited')
        self.assertEqual(live(1, error('authentication failed')),
                         'authentication-error')
        self.assertEqual(live(1, '', 'authentication failed'),
                         'authentication-error')
        # AN UNKNOWN DIAGNOSTIC STAYS UNCLASSIFIED AND STAYS PRIVATE.
        unknown = live(1, error('DO-NOT-PRINT strange trouble'))
        self.assertTrue(unknown.startswith('failed (unclassified; exit=1'),
                        unknown)
        for secret in ('DO-NOT-PRINT', 'strange', 'trouble'):
            self.assertNotIn(secret, unknown)
        # QUOTA NEVER MANUFACTURES SUCCESS: a zero exit with no unique terminal
        # result is inconclusive, whatever the stream says.
        self.assertEqual(live(0, error('usage limit reached')), 'inconclusive')
        self.assertEqual(live(0, ''), 'inconclusive')
        # CONFLICTING TERMINAL RESULTS: unsuccessful, and still classified.
        terminal = {'type': 'result', 'subtype': 'success', 'is_error': False,
                    'result': 'pong', 'session_id': 'one'}
        both = '\n'.join(json.dumps(one) for one in (terminal, terminal))
        self.assertEqual(live(0, both), 'inconclusive')
        self.assertEqual(live(1, both + '\n' + error('usage limit reached')),
                         'usage-limited')

    def test_a_claude_quota_stream_is_classified_through_the_fake_cli(self):
        """The same correction end to end, through the existing fake mode.

        The fake's `quota` mode writes the structured stdout error and exits 1,
        which is exactly the shape R1 reproduced; the mixed-outcome case above
        only ever drove that mode for Codex.
        """
        result = self.invoke(self.config([('claude', 'quota')]))
        self.assertEqual(result.returncode, 1)
        self.assertIn('usage-limited', result.stdout)
        self.assertIn('login: ok', result.stdout)
        self.assertNotIn('DO-NOT-PRINT', result.stdout + result.stderr)

    def test_claude_sparse_stream_validation_and_attribution(self):
        terminal = {'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'pong', 'session_id': 'one'}
        def event(kind='five_hour', used=.13, reset=200, session='one'):
            return {'type': 'rate_limit_event', 'session_id': session,
                    'rate_limit_info': {'rateLimitType': kind, 'utilization': used, 'resetsAt': reset, 'status': 'allowed'}}
        def sample(events, end=terminal, code=0, status=None):
            return (code, '\n'.join(json.dumps(e) for e in events + ([end] if end is not None else [])), '', status)
        def quota(events, **kw):
            return checks.claude_allowance(sample(events, **kw), 100)
        self.assertAlmostEqual(quota([event(), event('seven_day', .58)])['weekly']['remaining'], 42)
        for used, expected in [(0, 100), (1, 0), (.5, 50)]:
            self.assertEqual(quota([event(used=used)])['session']['remaining'], expected)
        for used in [None, True, '0.13', -.1, 1.1, float('nan'), float('inf'), 10**400]:
            self.assertIsNone(quota([event(used=used)])['session']['remaining'])
        for reset in [None, True, '200', -1, float('inf')]:
            self.assertIsNone(quota([event(reset=reset)])['session']['reset'])
        self.assertIsNone(quota([event(reset=100)])['session']['remaining'])
        for kind in ['seven_day_opus', 'seven_day_sonnet', 'overage', 'other', None, []]:
            self.assertTrue(all(w['remaining'] is None for w in quota([event(kind)]).values()))
        for events, end in [([event(session='other')], terminal), ([event(session=None)], terminal),
                            ([event()], dict(terminal, session_id='')), ([event()], None),
                            ([event(), terminal], terminal),
                            ([event(), {'type':'system','subtype':'init','session_id':'other'}], terminal)]:
            self.assertTrue(all(w['remaining'] is None for w in quota(events, end=end).values()))
        self.assertEqual(quota([event(), event()])['session']['remaining'], 87)
        self.assertIsNone(quota([event(), event(used=.5)])['session']['remaining'])
        self.assertEqual(quota([event(), event(used=.5), event('seven_day', .5)])['weekly']['remaining'], 50)
        for status in ['timeout', 'output-limit']:
            self.assertIsNone(quota([event()], status=status)['session']['remaining'])
        for raw in ['bad', '[]', '{"type":"result"}\nbad']:
            self.assertIsNone(checks.claude_allowance((0, raw, '', None), 100)['session']['remaining'])
        # Missing/malformed quota cannot corrupt a valid terminal verdict.
        self.assertEqual(checks.classify('claude', 'live', sample([event(used='bad')])), 'ok')
        self.assertEqual(checks.classify('claude', 'live', sample([event()], end=None)), 'inconclusive')
        self.assertEqual(checks.classify('claude', 'live', sample([event(), terminal])), 'inconclusive')
        self.assertNotEqual(checks.classify('claude', 'live', sample([event()], code=1)), 'ok')
        failed = dict(terminal, subtype='error_during_execution', is_error=True, result='authentication failed')
        self.assertEqual(checks.classify('claude', 'live', sample([event()], end=failed)), 'authentication-error')
        missing = {'type':'rate_limit_event','session_id':'one','rate_limit_info':{'unifiedWindows':{'five_hour':{'utilization':.1}}}}
        self.assertIsNone(quota([missing])['session']['remaining'])

    def test_compact_partial_missing_and_stale_usage_rendering(self):
        result = {'rateLimits': {'secondary': {'usedPercent': 52, 'windowDurationMins': 10080, 'resetsAt': 2000000000}}}
        lines = checks.render_usage(checks.allowance(result, 100), 100)
        self.assertEqual(lines, ['Weekly: 48% remaining; resets 2033-05-18 03:33:20 UTC'])
        self.assertEqual(checks.render_usage(checks.allowance({}, 100), 100),
                         [])
        stale = checks.render_usage(checks.allowance(result, 2000000001), 2000000001)
        self.assertEqual(stale, [])
        result['rateLimits']['secondary']['usedPercent'] = None
        self.assertEqual(checks.render_usage(checks.allowance(result, 100), 100), [])
        result['rateLimits']['secondary']['usedPercent'] = 52
        result['rateLimits']['secondary']['resetsAt'] = None
        self.assertIn('Weekly: 48% remaining; reset not reported', checks.render_usage(checks.allowance(result, 100), 100))

    def test_usage_window_validation_and_bucket_selection(self):
        def read(primary, secondary=None, **extra):
            return checks.allowance({'rateLimits': {'primary': primary, 'secondary': secondary}, **extra}, 100)
        def window(used=25, minutes=300, reset=200):
            return {'usedPercent': used, 'windowDurationMins': minutes, 'resetsAt': reset}
        for used, expected in [(0, 100), (100, 0), (25.5, 74.5)]:
            self.assertEqual(read(window(used))['session']['remaining'], expected)
        for used in [None, True, '20', -1, 101, float('nan'), float('inf'), 10**400]:
            self.assertIsNone(read(window(used))['session']['remaining'])
        for minutes in [None, True, '300', 0, -1, 1440, 10079]:
            result = read(window(minutes=minutes))
            self.assertTrue(all(v['remaining'] is None for v in result.values()))
        for reset in [None, True, '200', -1, float('nan'), float('inf'), 10**400]:
            result = read(window(reset=reset))['session']
            self.assertIsNone(result['reset'])
            self.assertEqual(result['remaining'], 75)
        for reset in [0, 99, 100]:
            result = read(window(reset=reset))['session']
            self.assertIsNone(result['remaining'])
            self.assertEqual(result['reason'], 'stale-reset')
        result = read(window(), window(minutes=60))['session']
        self.assertIsNone(result['remaining'])
        self.assertEqual(result['reason'], 'ambiguous-windows')
        self.assertEqual(read(window(minutes=10080), window())['weekly']['remaining'], 75)
        for buckets in [{}, [], {'other': {'primary': window()}}]:
            self.assertIsNone(read(window(), rateLimitsByLimitId=buckets)['session']['remaining'])
        self.assertEqual(read(window(), rateLimitsByLimitId=None)['session']['remaining'], 75)
        for doc in [None, {}, {'rateLimits': {'credits': {'balance': 500}}},
                    {'rateLimits': {'limitId': 'other', 'primary': window()}}]:
            self.assertTrue(all(v['remaining'] is None for v in checks.allowance(doc, 100).values()))

    def test_output_limit_and_ambiguous_zero_exit(self):
        result=self.invoke(self.config([('claude','overflow')]))
        self.assertEqual(result.returncode,1)
        self.assertIn('output-limit',result.stdout)
        self.assertEqual(checks.classify('codex','live',(0,'{"type":"turn.completed"}','',None)),'inconclusive')
        self.assertEqual(checks.classify('claude','live',(0,'{"type":"result","subtype":"success","is_error":false,"result":""}','',None)),'inconclusive')


if __name__=='__main__':unittest.main()
