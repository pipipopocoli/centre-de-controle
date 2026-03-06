from __future__ import annotations

import json
from pathlib import Path
import urllib.error
import urllib.request

BASE_URL = 'http://127.0.0.1:8787'
PROJECT_ID = 'cockpit'


def _request(path: str, *, method: str = 'GET', payload: dict | None = None) -> tuple[int, dict]:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode('utf-8')
        headers['content-type'] = 'application/json'
    request = urllib.request.Request(f'{BASE_URL}{path}', data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode('utf-8')
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode('utf-8')
        return error.code, json.loads(raw) if raw else {}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    status, initial = _request(f'/v1/projects/{PROJECT_ID}/tasks')
    _assert(status == 200, f'list tasks returned {status}: {initial}')
    before_count = len(initial.get('tasks') or [])
    task_path: Path | None = None

    try:
        status, created = _request(
            f'/v1/projects/{PROJECT_ID}/tasks',
            method='POST',
            payload={
                'title': 'Runtime task smoke',
                'owner': 'clems',
                'phase': 'Test',
                'status': 'todo',
                'source': 'manual',
                'objective': 'Verify live task CRUD.',
                'done_definition': 'Task can be created and moved to done.',
            },
        )
        _assert(status == 201, f'create task returned {status}: {created}')
        created_task = created.get('task') if isinstance(created.get('task'), dict) else {}
        task_id = str(created_task.get('task_id') or '')
        raw_path = str(created_task.get('path') or '')
        task_path = Path(raw_path) if raw_path else None
        _assert(task_id.startswith('ISSUE-CP-'), f'unexpected task id: {created}')

        status, updated = _request(
            f'/v1/projects/{PROJECT_ID}/tasks/{task_id}',
            method='PATCH',
            payload={
                'status': 'done',
                'done_definition': 'Verified by smoke test.',
            },
        )
        _assert(status == 200, f'patch task returned {status}: {updated}')
        updated_task = updated.get('task') if isinstance(updated.get('task'), dict) else {}
        _assert(updated_task.get('status') == 'done', f'task not moved to done: {updated}')

        status, final = _request(f'/v1/projects/{PROJECT_ID}/tasks')
        _assert(status == 200, f'final task list returned {status}: {final}')
        tasks = final.get('tasks') or []
        _assert(len(tasks) >= before_count + 1, 'task list did not grow after create')
        _assert(any(str(task.get('task_id')) == task_id for task in tasks if isinstance(task, dict)), 'created task missing from list')
    finally:
        if task_path and task_path.exists():
            task_path.unlink()

    print('OK: cockpit next task runtime verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
