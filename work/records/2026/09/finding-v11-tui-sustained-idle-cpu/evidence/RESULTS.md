# Idle TUI attribution evidence

## Reproduction identity

On 2026-09-06, `src/baton_work/tui/app.py` and the copy stored at
`baton_work/tui/app.py` inside the deployed
`/home/sl/opt/baton/v11/0650c61/bin/baton` archive both had SHA-256:

```text
ce569775e0b94d9e8556cf342aa4bd970e3908ed48cf9dd18a31425b1b581c69
```

`idle_probe.py` drives that source through a real 110x32 pseudo-terminal
against the deployed v11 configuration. It measures the first render
separately, starts the idle interval after that render, and stops the interval
when the parent sends the first exit-input byte.

## Normal idle loop

Representative command:

```text
python3 work/records/2026/09/finding-v11-tui-sustained-idle-cpu/evidence/idle_probe.py normal jobs
```

Representative 7.762-second measured idle interval:

```text
read calls                         4
expired reads                      3
time blocked in reads              6.003 seconds
timer ticks                        3
renders                            3
tree projection calls              3
idle CPU                           1.759 seconds (22.7% of one core)
render CPU                         1.759 seconds
tree projection CPU                1.702 seconds
tree rows                          140
```

The event loop therefore does not spin: it blocks for the requested deadline
and wakes once per timer interval. Each wake calls `Console.tick()`, which
unconditionally makes `refresh_due` true; the following render clears the
whole cache and executes `projection.tree()` again.

The first idle tree projection's `cProfile` sample took 0.571 seconds. Its
dominant cumulative entries were:

```text
projection.tree                    0.571 seconds
projection._claimed_ats            0.454 seconds
140 projection._row_view calls     0.106 seconds
3043 sqlite Connection.execute     0.096 seconds
140 projection.new_count calls     0.067 seconds
346 projection._unseen_set calls   0.061 seconds
140 projection._message_count      0.035 seconds
```

The same experiment with `inbox` and `teams` as the initial tab still made
three tree calls and spent respectively 1.690 and 1.698 CPU seconds in the
tree. The shared header's Jobs actionable count calls `Console._window()` on
every top-level tab, so page selection does not avoid the cost. Terminal
painting outside the tree accounted for only about 0.057 seconds across three
normal renders; geometry is not the dominant variable. The projection's 140
row views, 3043 SQL executions, message/unseen queries, and correlated event
scan establish that ledger/window size and history are the material cost
inputs.

## Unchanged-generation model

`poll-only` is an evidence-only monkeypatch: at each ordinary two-second
deadline it calls the existing `Authority.last_seq()`, does not invalidate the
cache, and still calls the unchanged production render path. Its purpose is to
isolate the cost of the proposed freshness probe plus cached presentation.

Representative 7.656-second interval:

```text
read calls                         4
expired reads                      3
time blocked in reads              7.654 seconds
timer ticks                        3
renders                            3
tree projection calls              0
poll CPU                           0.000123 seconds
render CPU                         0.001578 seconds
idle CPU                           0.001868 seconds (0.02% of one core)
```

This comparison attributes the sustained CPU to unconditional canonical tree
reprojection, not timeout wake frequency or curses repainting.

## Implemented correction validation

After the bounded source correction, the same `normal jobs` probe retained
three timer ticks and three renders over a representative 7.706-second idle
interval, but made no idle tree projection:

```text
read calls                         4
expired reads                      3
time blocked in reads              7.705 seconds
timer ticks                        3
renders                            3
tree projection calls              0
idle CPU                           0.001714 seconds (0.02% of one core)
render CPU                         0.001486 seconds
```

This is the production `Console.tick()` path, not the evidence-only
`poll-only` monkeypatch. The focused automatic-refresh and blink suites passed
20 tests, including the real-PTY external-change and continuous-input cases.
`just test-v11` then passed 3,337 parallel Python tests, 54 serial/PTY Python
tests, and 129 bridge tests.

## Instrumentation limitation

Attaching `strace` to the operator's existing PID was refused by the managed
environment (`PTRACE_TRACEME` and `PTRACE_SEIZE`: operation not permitted), and
that PID's `/proc` and `/dev/pts` entries were outside the sandbox namespace.
No escalation was requested. The controlled child PTY and in-process counters
provided the missing attribution without modifying the existing process.
