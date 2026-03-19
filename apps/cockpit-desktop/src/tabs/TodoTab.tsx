import { useCockpitStore } from '../store/index.js'
import type { TaskStatus } from '../lib/cockpitClient'
import { compareTasksByFreshness } from '../lib/formatters.js'
import { STATUS_ORDER, STATUS_LABELS } from '../lib/appConstants.js'

export interface TodoTabProps {
  handleCreateTask: () => Promise<void>
  handleSaveTask: () => Promise<void>
  handleTaskStatusMove: (taskId: string, status: TaskStatus) => Promise<void>
}

export function TodoTab({
  handleCreateTask,
  handleSaveTask,
  handleTaskStatusMove,
}: TodoTabProps) {
  const tasks = useCockpitStore((state) => state.tasks)
  const taskEditor = useCockpitStore((state) => state.taskEditor)
  const setTaskEditor = useCockpitStore((state) => state.setTaskEditor)
  const selectedTaskId = useCockpitStore((state) => state.selectedTaskId)
  const setSelectedTaskId = useCockpitStore((state) => state.setSelectedTaskId)
  const isSavingTask = useCockpitStore((state) => state.isSavingTask)

  const selectedTask = tasks.find((task) => task.task_id === selectedTaskId) ?? null

  const tasksByStatus = STATUS_ORDER.map((status) => ({
    status,
    label: STATUS_LABELS[status],
    items: tasks.filter((task) => task.status === status),
  }))

  return (
    <section className="secondary-tab panel todo-tab">
      <div className="secondary-header">
        <h2>To Do</h2>
        <span className="hint">issue-backed board with operator + AI tasks</span>
      </div>
      <div className="todo-layout">
        <section className="todo-board">
          {tasksByStatus.map((column) => (
            <article key={column.status} className="todo-column">
              <header>
                <h3>{column.label}</h3>
                <span>{column.items.length}</span>
              </header>
              <div className="todo-column-body" tabIndex={0} aria-label={`${STATUS_LABELS[column.status]} tasks`}>
                {column.items.length === 0 ? (
                  <p className="terminal-empty">No items.</p>
                ) : (
                  [...column.items].sort(compareTasksByFreshness).map((task) => (
                    <button
                      key={task.task_id}
                      className={`todo-card ${selectedTaskId === task.task_id ? 'active' : ''}`}
                      onClick={() => setSelectedTaskId(task.task_id)}
                    >
                      <div className="todo-card-top">
                        <strong>{task.title}</strong>
                        <span className={`task-source ${task.source === 'ai_auto' ? 'ai' : 'manual'}`}>
                          {task.source}
                        </span>
                      </div>
                      <p>{task.task_id}</p>
                      <div className="todo-card-meta">
                        <span>@{task.owner}</span>
                        <span>{task.phase}</span>
                      </div>
                      <div className="todo-card-actions">
                        {STATUS_ORDER.filter((status) => status !== task.status).map((status) => (
                          <button
                            key={status}
                            className="small-btn"
                            onClick={(event) => {
                              event.stopPropagation()
                              void handleTaskStatusMove(task.task_id, status)
                            }}
                          >
                            {STATUS_LABELS[status]}
                          </button>
                        ))}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </article>
          ))}
        </section>
        <aside className="todo-editor">
          <section className="secondary-card">
            <h3>{selectedTask ? 'Task detail' : 'Create task'}</h3>
            <div className="form-grid">
              <label>
                <span>Title</span>
                <input
                  value={taskEditor.title}
                  onChange={(event) => setTaskEditor((previous) => ({ ...previous, title: event.target.value }))}
                  placeholder="Task title"
                />
              </label>
              <label>
                <span>Owner</span>
                <input
                  value={taskEditor.owner}
                  onChange={(event) => setTaskEditor((previous) => ({ ...previous, owner: event.target.value }))}
                  placeholder="@clems"
                />
              </label>
              <label>
                <span>Phase</span>
                <input
                  value={taskEditor.phase}
                  onChange={(event) => setTaskEditor((previous) => ({ ...previous, phase: event.target.value }))}
                  placeholder="Implement"
                />
              </label>
              <label>
                <span>Status</span>
                <select
                  value={taskEditor.status}
                  onChange={(event) =>
                    setTaskEditor((previous) => ({ ...previous, status: event.target.value as TaskStatus }))
                  }
                >
                  {STATUS_ORDER.map((status) => (
                    <option key={status} value={status}>
                      {STATUS_LABELS[status]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="wide">
                <span>Objective</span>
                <textarea
                  value={taskEditor.objective}
                  onChange={(event) =>
                    setTaskEditor((previous) => ({ ...previous, objective: event.target.value }))
                  }
                  placeholder="What should be delivered?"
                />
              </label>
              <label className="wide">
                <span>Done definition</span>
                <textarea
                  value={taskEditor.done_definition}
                  onChange={(event) =>
                    setTaskEditor((previous) => ({ ...previous, done_definition: event.target.value }))
                  }
                  placeholder="Verifiable definition of done"
                />
              </label>
            </div>
            <div className="todo-editor-actions">
              <button className="send-btn" onClick={() => void handleCreateTask()} disabled={isSavingTask}>
                {isSavingTask && !selectedTask ? 'Creating...' : 'Create task'}
              </button>
              <button
                className="send-btn alt"
                onClick={() => void handleSaveTask()}
                disabled={isSavingTask || !selectedTask}
              >
                {isSavingTask && selectedTask ? 'Saving...' : 'Save selected'}
              </button>
            </div>
            {selectedTask ? (
              <div className="todo-detail-meta">
                <p><strong>Path:</strong> {selectedTask.path}</p>
                <p><strong>Updated:</strong> {new Date(selectedTask.updated_at).toLocaleString()}</p>
                <p><strong>Source:</strong> {selectedTask.source}</p>
              </div>
            ) : (
              <p className="small-copy">
                AI-created task lists from @clems and L1 agents land here automatically with source <code>ai_auto</code>.
              </p>
            )}
          </section>
        </aside>
      </div>
    </section>
  )
}
