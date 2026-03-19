import { useCallback } from 'react'
import { useCockpitStore } from '../store/index.js'
import { createTask, updateTask } from '../lib/cockpitClient'
import type { TaskStatus } from '../lib/cockpitClient'
import { emptyTaskEditor } from '../lib/formatters.js'

/**
 * Task CRUD: create, save, and status move.
 */
export function useTaskActions({
  refreshProjectSummary,
}: {
  refreshProjectSummary: () => Promise<unknown>
}) {
  const projectId = useCockpitStore((s) => s.projectId)
  const taskEditor = useCockpitStore((s) => s.taskEditor)
  const selectedTaskId = useCockpitStore((s) => s.selectedTaskId)
  const isSavingTask = useCockpitStore((s) => s.isSavingTask)

  const setApiError = useCockpitStore((s) => s.setApiError)
  const setUiNotice = useCockpitStore((s) => s.setUiNotice)
  const setTasks = useCockpitStore((s) => s.setTasks)
  const setSelectedTaskId = useCockpitStore((s) => s.setSelectedTaskId)
  const setTaskEditor = useCockpitStore((s) => s.setTaskEditor)
  const setIsSavingTask = useCockpitStore((s) => s.setIsSavingTask)

  const handleCreateTask = useCallback(async () => {
    if (!taskEditor.title.trim() || isSavingTask) {
      return
    }
    setIsSavingTask(true)
    setApiError(null)
    try {
      const created = await createTask(projectId, {
        title: taskEditor.title.trim(),
        owner: taskEditor.owner.trim() || 'clems',
        phase: taskEditor.phase.trim() || 'Implement',
        status: taskEditor.status,
        source: 'manual',
        objective: taskEditor.objective.trim(),
        done_definition: taskEditor.done_definition.trim(),
      })
      setTasks((previous) => [created, ...previous])
      setSelectedTaskId(created.task_id)
      setTaskEditor(emptyTaskEditor())
      await refreshProjectSummary()
      setUiNotice(`task created: ${created.task_id}`)
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsSavingTask(false)
    }
  }, [
    isSavingTask,
    projectId,
    refreshProjectSummary,
    taskEditor,
    setApiError,
    setIsSavingTask,
    setSelectedTaskId,
    setTaskEditor,
    setTasks,
    setUiNotice,
  ])

  const handleSaveTask = useCallback(async () => {
    if (!selectedTaskId || isSavingTask) {
      return
    }
    setIsSavingTask(true)
    setApiError(null)
    try {
      const updated = await updateTask(projectId, selectedTaskId, taskEditor)
      setTasks((previous) =>
        previous.map((task) => (task.task_id === updated.task_id ? updated : task)),
      )
      await refreshProjectSummary()
      setUiNotice(`task updated: ${updated.task_id}`)
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsSavingTask(false)
    }
  }, [
    isSavingTask,
    projectId,
    refreshProjectSummary,
    selectedTaskId,
    taskEditor,
    setApiError,
    setIsSavingTask,
    setTasks,
    setUiNotice,
  ])

  const handleTaskStatusMove = useCallback(
    async (taskId: string, status: TaskStatus) => {
      setApiError(null)
      try {
        const updated = await updateTask(projectId, taskId, { status })
        setTasks((previous) =>
          previous.map((task) => (task.task_id === updated.task_id ? updated : task)),
        )
        await refreshProjectSummary()
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      }
    },
    [projectId, refreshProjectSummary, setApiError, setTasks],
  )

  return {
    handleCreateTask,
    handleSaveTask,
    handleTaskStatusMove,
  }
}
