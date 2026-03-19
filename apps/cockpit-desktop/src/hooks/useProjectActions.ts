import { useCallback } from 'react'
import { useCockpitStore } from '../store/index.js'
import {
  createProject,
  createTask,
  liveTurn,
  putLlmProfile,
  putProjectSettings,
  putRoadmap,
  startTakeover,
} from '../lib/cockpitClient'
import { roomLeadAgentIdsFromRecords } from '../lib/formatters.js'
import { pickProjectFolder } from '../lib/tauriOps'

/**
 * Project-level actions: takeover, apply tasks/roadmap, launch plan,
 * save LLM profile, save project link, create project, folder picking.
 */
export function useProjectActions({
  refreshApprovals,
  refreshProjectSettings,
  refreshProjectSummary,
  refreshRoadmap,
  refreshTasks,
  roomStickToBottomRef,
}: {
  refreshApprovals: () => Promise<void>
  refreshProjectSettings: () => Promise<unknown>
  refreshProjectSummary: () => Promise<unknown>
  refreshRoadmap: () => Promise<unknown>
  refreshTasks: () => Promise<void>
  roomStickToBottomRef: React.RefObject<boolean>
}) {
  const projectId = useCockpitStore((s) => s.projectId)
  const linkedRepoDraft = useCockpitStore((s) => s.linkedRepoDraft)
  const profileDraft = useCockpitStore((s) => s.profileDraft)
  const isSavingProfile = useCockpitStore((s) => s.isSavingProfile)
  const projectSettings = useCockpitStore((s) => s.projectSettings)
  const agentRecords = useCockpitStore((s) => s.agentRecords)
  const takeoverResult = useCockpitStore((s) => s.takeoverResult)
  const isApplyingTakeover = useCockpitStore((s) => s.isApplyingTakeover)
  const isSendingChat = useCockpitStore((s) => s.isSendingChat)
  const isCreatingProject = useCockpitStore((s) => s.isCreatingProject)
  const newProjectIdDraft = useCockpitStore((s) => s.newProjectIdDraft)
  const newProjectNameDraft = useCockpitStore((s) => s.newProjectNameDraft)
  const newProjectRepoDraft = useCockpitStore((s) => s.newProjectRepoDraft)

  const setApiError = useCockpitStore((s) => s.setApiError)
  const setUiNotice = useCockpitStore((s) => s.setUiNotice)
  const setActiveTab = useCockpitStore((s) => s.setActiveTab)
  const setLlmProfile = useCockpitStore((s) => s.setLlmProfile)
  const setProfileDraft = useCockpitStore((s) => s.setProfileDraft)
  const setIsSavingProfile = useCockpitStore((s) => s.setIsSavingProfile)
  const setTakeoverResult = useCockpitStore((s) => s.setTakeoverResult)
  const setIsRunningTakeover = useCockpitStore((s) => s.setIsRunningTakeover)
  const setIsApplyingTakeover = useCockpitStore((s) => s.setIsApplyingTakeover)
  const setProjectRoadmap = useCockpitStore((s) => s.setProjectRoadmap)
  const setRoomParticipantMode = useCockpitStore((s) => s.setRoomParticipantMode)
  const setIsSendingChat = useCockpitStore((s) => s.setIsSendingChat)
  const mergeChatMessages = useCockpitStore((s) => s.mergeChatMessages)
  const setProjectId = useCockpitStore((s) => s.setProjectId)
  const setProjectActionMode = useCockpitStore((s) => s.setProjectActionMode)
  const setSelectedProjectDocId = useCockpitStore((s) => s.setSelectedProjectDocId)
  const setIsCreatingProject = useCockpitStore((s) => s.setIsCreatingProject)
  const setIsChoosingFolder = useCockpitStore((s) => s.setIsChoosingFolder)
  const setLinkedRepoDraft = useCockpitStore((s) => s.setLinkedRepoDraft)
  const setNewProjectIdDraft = useCockpitStore((s) => s.setNewProjectIdDraft)
  const setNewProjectNameDraft = useCockpitStore((s) => s.setNewProjectNameDraft)
  const setNewProjectRepoDraft = useCockpitStore((s) => s.setNewProjectRepoDraft)

  const handleSaveLlmProfile = useCallback(async () => {
    if (!profileDraft || isSavingProfile) {
      return
    }
    setIsSavingProfile(true)
    setApiError(null)
    try {
      const saved = await putLlmProfile(projectId, profileDraft)
      setLlmProfile(saved)
      setProfileDraft(saved)
      setUiNotice('model routing saved')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsSavingProfile(false)
    }
  }, [isSavingProfile, profileDraft, projectId, setApiError, setIsSavingProfile, setLlmProfile, setProfileDraft, setUiNotice])

  const handleSaveProjectLink = useCallback(async () => {
    setApiError(null)
    try {
      await putProjectSettings(projectId, {
        linked_repo_path: linkedRepoDraft.trim() || '',
      })
      await refreshProjectSettings()
      await refreshProjectSummary()
      setUiNotice('linked repo path saved')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    }
  }, [linkedRepoDraft, projectId, refreshProjectSettings, refreshProjectSummary, setApiError, setUiNotice])

  const handleRunTakeover = useCallback(async () => {
    setIsRunningTakeover(true)
    setApiError(null)
    setUiNotice(null)
    try {
      setRoomParticipantMode('all_active')
      const kickoffParticipants = roomLeadAgentIdsFromRecords(agentRecords)
      const response = await startTakeover(projectId, {
        linked_repo_path: linkedRepoDraft.trim() || undefined,
      })
      setTakeoverResult(response)
      if (response.linked_repo_path && response.linked_repo_path !== (projectSettings?.linked_repo_path ?? '')) {
        await putProjectSettings(projectId, {
          linked_repo_path: response.linked_repo_path,
        })
        await refreshProjectSettings()
      }
      await refreshProjectSummary()
      setActiveTab('concierge_room')
      roomStickToBottomRef.current = true
      const takeoverRoomContext = {
        room_participant_mode: 'all_active',
        room_participants: kickoffParticipants,
        room_participant_count: kickoffParticipants.length,
        coordinator: 'clems',
        takeover_run_id: response.run_id,
      }
      const kickoffPrompt = [
        `Takeover package ready for project ${projectId}.`,
        `Linked repo: ${response.linked_repo_path || 'not linked'}`,
        '',
        `Human summary: ${response.summary_human}`,
        '',
        'Top tech findings:',
        ...response.summary_tech.map((item) => `- ${item}`),
        '',
        'Suggested next actions:',
        ...response.suggested_tasks.map((task) => `- ${task.title} -> @${task.owner}`),
        '',
        'Clems, run the board from this takeover package. Clarify key unknowns, then propose execution order.',
      ].join('\n')

      const kickoff = await liveTurn(projectId, {
        text: kickoffPrompt,
        chat_mode: 'conceal_room',
        execution_mode: 'chat',
        mentions: ['clems'],
        context_ref: takeoverRoomContext,
      })
      mergeChatMessages(kickoff.messages)
      if (kickoff.approval_requests.length > 0) {
        void refreshApprovals()
      }
      setUiNotice('takeover draft ready in Le Conseil')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsRunningTakeover(false)
    }
  }, [
    agentRecords,
    linkedRepoDraft,
    mergeChatMessages,
    projectId,
    projectSettings?.linked_repo_path,
    refreshApprovals,
    refreshProjectSettings,
    refreshProjectSummary,
    roomStickToBottomRef,
    setActiveTab,
    setApiError,
    setIsRunningTakeover,
    setRoomParticipantMode,
    setTakeoverResult,
    setUiNotice,
  ])

  const handleApplyTakeoverTasks = useCallback(async () => {
    if (!takeoverResult || takeoverResult.suggested_tasks.length === 0 || isApplyingTakeover) {
      return
    }
    setIsApplyingTakeover(true)
    setApiError(null)
    try {
      for (const task of takeoverResult.suggested_tasks) {
        await createTask(projectId, {
          title: task.title,
          owner: task.owner,
          phase: 'Implement',
          status: 'todo',
          source: 'takeover',
          objective: task.objective,
          done_definition: task.done_definition,
        })
      }
      await refreshTasks()
      await refreshProjectSummary()
      setUiNotice('takeover tasks added to To Do')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsApplyingTakeover(false)
    }
  }, [isApplyingTakeover, projectId, refreshProjectSummary, refreshTasks, setApiError, setIsApplyingTakeover, setUiNotice, takeoverResult])

  const handleApplyTakeoverRoadmap = useCallback(async () => {
    if (!takeoverResult || isApplyingTakeover) {
      return
    }
    setIsApplyingTakeover(true)
    setApiError(null)
    try {
      const roadmap = await putRoadmap(projectId, takeoverResult.roadmap_sections)
      setProjectRoadmap(roadmap)
      await refreshRoadmap()
      await refreshProjectSummary()
      setUiNotice('takeover roadmap applied')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsApplyingTakeover(false)
    }
  }, [isApplyingTakeover, projectId, refreshProjectSummary, refreshRoadmap, setApiError, setIsApplyingTakeover, setProjectRoadmap, setUiNotice, takeoverResult])

  const handleLaunchTakeoverPlan = useCallback(async () => {
    if (!takeoverResult || isSendingChat) {
      return
    }

    const kickoff = [
      'Lets go.',
      `Run the takeover plan for project ${projectId}.`,
      `Linked repo: ${takeoverResult.linked_repo_path || 'not linked'}`,
      '',
      'Start from these tasks:',
      ...takeoverResult.suggested_tasks.slice(0, 10).map((task) => `- ${task.title} -> @${task.owner}`),
      '',
      'Clems, coordinate the room, choose the execution order, and report Now / Next / Blockers.',
    ].join('\n')

    setActiveTab('concierge_room')
    setRoomParticipantMode('all_active')
    setApiError(null)
    setUiNotice(null)
    setIsSendingChat(true)
    try {
      const kickoffParticipants = roomLeadAgentIdsFromRecords(agentRecords)
      const roomContext = {
        room_participant_mode: 'all_active',
        room_participants: kickoffParticipants,
        room_participant_count: kickoffParticipants.length,
        coordinator: 'clems',
      }
      const response = await liveTurn(projectId, {
        text: kickoff,
        chat_mode: 'conceal_room',
        execution_mode: 'chat',
        mentions: ['clems'],
        context_ref: roomContext,
      })
      mergeChatMessages(response.messages)
      if (response.approval_requests.length > 0) {
        void refreshApprovals()
      }
      setUiNotice('takeover execution started in Le Conseil')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsSendingChat(false)
    }
  }, [
    agentRecords,
    isSendingChat,
    mergeChatMessages,
    projectId,
    refreshApprovals,
    setActiveTab,
    setApiError,
    setIsSendingChat,
    setRoomParticipantMode,
    setUiNotice,
    takeoverResult,
  ])

  const handleChooseRepoFolder = useCallback(async (target: 'takeover' | 'create') => {
    const currentValue = target === 'create' ? newProjectRepoDraft : linkedRepoDraft
    const applyValue = target === 'create' ? setNewProjectRepoDraft : setLinkedRepoDraft
    const promptLabel = target === 'create' ? 'new project' : 'takeover'
    setIsChoosingFolder(true)
    setApiError(null)
    try {
      const chosen = await pickProjectFolder()
      if (chosen) {
        applyValue(chosen)
        setUiNotice(`folder selected: ${chosen}`)
      } else {
        const fallback = window.prompt(`Paste an absolute repo path for ${promptLabel}.`, currentValue)
        if (fallback && fallback.trim()) {
          applyValue(fallback.trim())
          setUiNotice(`folder path pasted: ${fallback.trim()}`)
        } else {
          setUiNotice('folder picker cancelled')
        }
      }
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
      const fallback = window.prompt('Native folder picker unavailable. Paste an absolute repo path.', currentValue)
      if (fallback && fallback.trim()) {
        applyValue(fallback.trim())
        setUiNotice(`folder path pasted: ${fallback.trim()}`)
      } else {
        setUiNotice('native folder picker unavailable. manual path still works.')
      }
    } finally {
      setIsChoosingFolder(false)
    }
  }, [linkedRepoDraft, newProjectRepoDraft, setApiError, setIsChoosingFolder, setLinkedRepoDraft, setNewProjectRepoDraft, setUiNotice])

  const handleCreateProject = useCallback(async () => {
    if (isCreatingProject) {
      return
    }
    const nextProjectId = newProjectIdDraft.trim().toLowerCase()
    if (!nextProjectId) {
      setApiError('project id is required')
      return
    }

    setIsCreatingProject(true)
    setApiError(null)
    setUiNotice(null)
    try {
      const created = await createProject({
        project_id: nextProjectId,
        project_name: newProjectNameDraft.trim() || nextProjectId,
        linked_repo_path: newProjectRepoDraft.trim() || null,
      })
      setTakeoverResult(null)
      setProjectActionMode(null)
      setSelectedProjectDocId(created.project_id)
      setProjectId(created.project_id)
      setNewProjectIdDraft('')
      setNewProjectNameDraft('')
      setNewProjectRepoDraft('')
      setUiNotice(`project created: ${created.project_id}`)
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsCreatingProject(false)
    }
  }, [
    isCreatingProject,
    newProjectIdDraft,
    newProjectNameDraft,
    newProjectRepoDraft,
    setApiError,
    setIsCreatingProject,
    setNewProjectIdDraft,
    setNewProjectNameDraft,
    setNewProjectRepoDraft,
    setProjectActionMode,
    setProjectId,
    setSelectedProjectDocId,
    setTakeoverResult,
    setUiNotice,
  ])

  return {
    handleRunTakeover,
    handleApplyTakeoverTasks,
    handleApplyTakeoverRoadmap,
    handleLaunchTakeoverPlan,
    handleSaveLlmProfile,
    handleSaveProjectLink,
    handleChooseRepoFolder,
    handleCreateProject,
  }
}
