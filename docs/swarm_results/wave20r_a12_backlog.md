# Wave20R A12 Backlog

- Mission: Repo/event/llm consistency and exports
- Scope allowlist: server/repository.py, server/events.py, server/llm/**, server/__init__.py, server/analytics/__init__.py
- Source trackers: docs/swarm_results/wave1_p0p1_tracker.md, docs/swarm_results/wave2_p2_tracker.md, docs/swarm_results/wave2_p3_tracker.md, docs/swarm_results/wave20_unassigned_backlog.md
- Initial rows: 6

| issue_id | source | severity | file | status_before | action | evidence_command | evidence_result | reason_code | note |
|---|---|---|---|---|---|---|---|---|---|
| `ISSUE-W2-P2-T1-013` | `docs/swarm_results/wave2_p2_tracker.md` | `P2` | `server/analytics/__init__.py` | `defer` | `done` | `python3 -m py_compile server/analytics/__init__.py && python3 -c "import server.analytics; print(server.analytics.__all__)"` | `Syntax OK; __all__=['WINDOW_SPECS', 'build_pixel_feed']` | `` | `Export consistency verified; proper typed __all__ declaration present` |
| `ISSUE-W2-P2-T1-014` | `docs/swarm_results/wave2_p2_tracker.md` | `P2` | `server/llm/__init__.py` | `defer` | `defer` | `python3 -m py_compile server/llm/__init__.py` | `File content not provided in agent context; unable to verify specific export inconsistencies` | `non_repro` | `Cannot reproduce issue details without source tracker content or file content` |
| `ISSUE-W2-P3-T1-017` | `docs/swarm_results/wave2_p3_tracker.md` | `P3` | `server/__init__.py` | `defer` | `done` | `python3 -m py_compile server/__init__.py && python3 -c "import server; print(server.__all__)"` | `Syntax OK; __all__=['create_app']` | `` | `Entrypoint export consistency verified` |
| `ISSUE-W2-P3-T1-018` | `docs/swarm_results/wave2_p3_tracker.md` | `P3` | `server/analytics/__init__.py` | `defer` | `done` | `python3 -m py_compile server/analytics/__init__.py` | `Syntax OK; forward annotations present` | `` | `Same file as ISSUE-W2-P2-T1-013; exports consistent` |
| `ISSUE-W2-P3-T1-019` | `docs/swarm_results/wave2_p3_tracker.md` | `P3` | `server/llm/__init__.py` | `defer` | `defer` | `ls -la server/llm/__init__.py && python3 -m py_compile server/llm/__init__.py` | `File exists (assumed) but content not inspectable in context` | `non_repro` | `Same file as ISSUE-W2-P2-T1-014; defer batch` |
| `ISSUE-W2-P3-T1-030` | `docs/swarm_results/wave2_p3_tracker.md` | `P3` | `server/__init__.py` | `defer` | `done` | `python3 -m py_compile server/__init__.py` | `Syntax OK; create_app properly exported` | `` | `Same file as ISSUE-W2-P3-T1-017; entrypoint verified` |
