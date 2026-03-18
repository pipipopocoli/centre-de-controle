import { useCallback, useEffect, useMemo, useRef } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import { EditorState } from './office/editor/editorState.js'
import { OfficeState } from './office/engine/officeState.js'
import { OfficeCanvas } from './office/components/OfficeCanvas.js'
import { ToolOverlay } from './office/components/ToolOverlay.js'
import { loadDonargTheme } from './office/themes/donargTheme.js'
import { loadPixelReferenceTheme } from './office/themes/pixelReferenceTheme.js'
import {
  approveApproval,
  createTask,
  createAgent,
  createProject,
  deleteAgent,
  getApiUrl,
  getAgents,
  getApprovals,
  getChat,
  getHealth,
  getLayout,
  getLlmProfile,
  getPixelFeed,
  getProjects,
  getProjectSummary,
  getProjectSettings,
  getRoadmap,
  getSkillsLibrary,
  getTasks,
  liveTurn,
  openTerminal,
  putLlmProfile,
  putLayout,
  putProjectSettings,
  putRoadmap,
  resetChat,
  restartTerminal,
  startTakeover,
  connectEvents,
  rejectApproval,
  transcribeVoice,
  updateTask,
} from './lib/cockpitClient'
import type {
  ChatMessage,
  ChatMode,
  PixelFeedResponse,
  ProjectCatalogEntry,
  TaskRecord,
  TaskStatus,
  VoiceTranscribeResponse,
} from './lib/cockpitClient'
import { openOsTerminal, pickProjectFolder } from './lib/tauriOps'
import {
  useCockpitStore,
  selectDirectChatMessages,
  selectConciergeChatMessages,
  selectInternalConciergeMessages,
  selectActiveChatMode,
} from './store/index.js'
import type { ComposerStatus, DirectTargetMode, RosterAgentView, WorkbenchPanel } from './types.js'
import type { ToolActivity } from './office/types.js'
import {
  parseSkillsInput,
  formatSkillChip,
  agentInitials,
  formatHeartbeat,
  formatAgentState,
  formatCurrencyCad,
  projectLabel,
  modelLabel,
  isUnavailableModel,
  messageKindLabel,
  messageChatMode,
  isSyntheticDirectReply,
  roomLeadAgentIdsFromRecords,
  preferredVoiceRecorder,
  blobToBase64,
  emptyTaskEditor,
  compareTasksByFreshness,
} from './lib/formatters.js'
import {
  STATUS_ORDER,
  STATUS_LABELS,
  CLEMS_MODEL_OPTIONS,
  L1_MODEL_OPTIONS,
  L2_MODEL_OPTIONS,
  QUICK_AGENT_PRESETS,
  VOICE_STT_OPTIONS,
} from './lib/appConstants.js'


function App() {
  const store = useCockpitStore()
  const {
    projectId, setProjectId,
    apiError, setApiError,
    loading, setLoading,
    feed, setFeed,
    agentRecords, setAgentRecords,
    setChatMessages,
    directChatInput, setDirectChatInput,
    roomChatInput, setRoomChatInput,
    executionMode, setExecutionMode,
    wsConnected, setWsConnected,
    composerStatus, setComposerStatus,
    selectedAgentId, setSelectedAgentId,
    directTarget, setDirectTarget,
    eventLog, setEventLog,
    createAgentId, setCreateAgentId,
    createAgentName, setCreateAgentName,
    createAgentSkills, setCreateAgentSkills,
    isSubmitting, setIsSubmitting,
    isSendingChat, setIsSendingChat,
    showRoomAddMenu, setShowRoomAddMenu,
    refreshTick, setRefreshTick,
    agentTools, setAgentTools,
    overlayViewport, setOverlayViewport,
    activeTab, setActiveTab,
    workspaceTab, setWorkspaceTab,
    approvals, setApprovals,
    approvalBusy, setApprovalBusy,
    uiNotice, setUiNotice,
    fallbackDiagnostics, setFallbackDiagnostics,
    directSendPhase, setDirectSendPhase,
    zoom, setZoom,
    workbenchCollapsed, setWorkbenchCollapsed,
    workbenchPanel, setWorkbenchPanel,
    backendHealth, setBackendHealth,
    llmProfile, setLlmProfile,
    profileDraft, setProfileDraft,
    tasks, setTasks,
    taskEditor, setTaskEditor,
    selectedTaskId, setSelectedTaskId,
    isSavingTask, setIsSavingTask,
    isSavingProfile, setIsSavingProfile,
    clockNow, setClockNow,
    lastEventAt, setLastEventAt,
    lastSyncAt,
    docsPanel, setDocsPanel,
    skillsLibrary, setSkillsLibrary,
    skillsLibraryLoading, setSkillsLibraryLoading,
    projectSummary, setProjectSummary,
    projectSettings, setProjectSettings,
    projectCatalog, setProjectCatalog,
    projectCatalogLoading, setProjectCatalogLoading,
    selectedProjectDocId, setSelectedProjectDocId,
    linkedRepoDraft, setLinkedRepoDraft,
    projectActionMode, setProjectActionMode,
    newProjectIdDraft, setNewProjectIdDraft,
    newProjectNameDraft, setNewProjectNameDraft,
    newProjectRepoDraft, setNewProjectRepoDraft,
    projectRoadmap, setProjectRoadmap,
    takeoverResult, setTakeoverResult,
    isRunningTakeover, setIsRunningTakeover,
    isApplyingTakeover, setIsApplyingTakeover,
    isChoosingFolder, setIsChoosingFolder,
    isCreatingProject, setIsCreatingProject,
    isRecordingVoice, setIsRecordingVoice,
    isTranscribingVoice, setIsTranscribingVoice,
    directVisibleCount, setDirectVisibleCount,
    roomVisibleCount, setRoomVisibleCount,
    roomParticipantMode, setRoomParticipantMode,
    roomCustomParticipants, setRoomCustomParticipants,
    assetsStatus, setAssetsStatus,
    mergeChatMessages,
    markSynced,
  } = store
  const directChatMessages = useCockpitStore(selectDirectChatMessages)
  const conciergeChatMessages = useCockpitStore(selectConciergeChatMessages)
  const internalConciergeMessages = useCockpitStore(selectInternalConciergeMessages)
  const activeChatMode = useCockpitStore(selectActiveChatMode)

  const officeState = useMemo(() => new OfficeState(), [])
  const editorState = useMemo(() => new EditorState(), [])
  const panRef = useRef({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)
  const createAgentIdInputRef = useRef<HTMLInputElement>(null)
  const wsConnectedRef = useRef(false)
  const fallbackPollingRef = useRef(false)
  const fallbackPollTimerRef = useRef<number | null>(null)
  const fallbackStopTimerRef = useRef<number | null>(null)
  const directRetryTimerRef = useRef<number | null>(null)

  const idToNumericRef = useRef(new Map<string, number>())
  const numericToIdRef = useRef(new Map<number, string>())
  const nextNumericRef = useRef(1)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const voiceChunksRef = useRef<Blob[]>([])
  const voiceFormatRef = useRef('ogg')
  const directChatLogRef = useRef<HTMLDivElement>(null)
  const roomChatLogRef = useRef<HTMLDivElement>(null)
  const directStickToBottomRef = useRef(true)
  const roomStickToBottomRef = useRef(true)

  const toNumericId = useCallback((agentId: string) => {
    const existing = idToNumericRef.current.get(agentId)
    if (existing !== undefined) {
      return existing
    }
    const value = nextNumericRef.current++
    idToNumericRef.current.set(agentId, value)
    numericToIdRef.current.set(value, agentId)
    return value
  }, [])

  const styleForAgent = useCallback((agentId: string): { palette: number; hueShift: number } => {
    const canonical: Record<string, number> = {
      clems: 0,
      victor: 1,
      leo: 2,
      nova: 3,
      vulgarisation: 4,
    }
    const normalized = agentId.trim().toLowerCase()
    const fixed = canonical[normalized]
    if (fixed !== undefined) {
      return { palette: fixed, hueShift: 0 }
    }

    let hash = 0
    for (let i = 0; i < normalized.length; i++) {
      hash = (hash * 31 + normalized.charCodeAt(i)) | 0
    }
    const unsignedHash = Math.abs(hash)
    return {
      palette: unsignedHash % 6,
      hueShift: ((unsignedHash % 9) + 1) * 20,
    }
  }, [])

  const stopFallbackPolling = useCallback(
    (nextStatus?: ComposerStatus) => {
      fallbackPollingRef.current = false
      if (fallbackPollTimerRef.current !== null) {
        window.clearInterval(fallbackPollTimerRef.current)
        fallbackPollTimerRef.current = null
      }
      if (fallbackStopTimerRef.current !== null) {
        window.clearTimeout(fallbackStopTimerRef.current)
        fallbackStopTimerRef.current = null
      }
      if (nextStatus) {
        setComposerStatus(nextStatus)
      }
    },
    [],
  )

  // markSynced is now provided by the Zustand store

  const refreshApprovals = useCallback(async () => {
    try {
      const response = await getApprovals(projectId, 'pending')
      setApprovals(response.approvals)
      markSynced()
    } catch {
      // keep silent to avoid noisy UI while reconnecting
    }
  }, [markSynced, projectId])

  const startFallbackPolling = useCallback(() => {
    if (fallbackPollingRef.current) {
      return
    }

    fallbackPollingRef.current = true
    setComposerStatus('http_fallback')

    const poll = async () => {
      try {
        const history = await getChat(projectId, 300, 'operator')
        mergeChatMessages(history.messages)
      } catch {
        // no-op: keep trying during fallback window
      }

      if (wsConnectedRef.current) {
        stopFallbackPolling('live')
        void refreshApprovals()
      }
    }

    void poll()

    fallbackPollTimerRef.current = window.setInterval(() => {
      void poll()
    }, 1500)

    fallbackStopTimerRef.current = window.setTimeout(() => {
      if (wsConnectedRef.current) {
        stopFallbackPolling('live')
      } else {
        stopFallbackPolling('reconnecting')
      }
    }, 20_000)
  }, [mergeChatMessages, projectId, refreshApprovals, stopFallbackPolling])

  const syncOfficeAgents = useCallback(
    (nextFeed: PixelFeedResponse | null) => {
      if (!nextFeed) {
        return
      }

      const ids = new Set(nextFeed.agents.map((agent) => agent.agent_id))

      for (const [agentId, numericId] of idToNumericRef.current.entries()) {
        if (!ids.has(agentId)) {
          officeState.removeAgent(numericId)
          idToNumericRef.current.delete(agentId)
          numericToIdRef.current.delete(numericId)
        }
      }

      const tools: Record<number, ToolActivity[]> = {}

      for (const agent of nextFeed.agents) {
        const numericId = toNumericId(agent.agent_id)
        const exists = officeState.characters.has(numericId)
        if (!exists) {
          const style = styleForAgent(agent.agent_id)
          officeState.addAgent(
            numericId,
            style.palette,
            style.hueShift,
            undefined,
            true,
            agent.name,
          )
        }

        const isActive = agent.terminal_state === 'running'
        officeState.setAgentActive(numericId, isActive)
        officeState.setAgentTool(numericId, isActive ? 'terminal' : null)

        tools[numericId] = [
          {
            toolId: `terminal-${agent.agent_id}`,
            status: isActive ? 'Terminal live' : 'Idle',
            done: !isActive,
          },
        ]
      }

      const currentSelected = useCockpitStore.getState().selectedAgentId
      if (!currentSelected || !ids.has(currentSelected)) {
        setSelectedAgentId(ids.has('clems') ? 'clems' : nextFeed.agents[0]?.agent_id ?? null)
      }

      setAgentTools(tools)
      setRefreshTick((value) => value + 1)
    },
    [officeState, styleForAgent, toNumericId],
  )

  const refreshPixelFeed = useCallback(async () => {
    const nextFeed = await getPixelFeed(projectId)
    setFeed(nextFeed)
    syncOfficeAgents(nextFeed)
    markSynced()
  }, [markSynced, projectId, syncOfficeAgents])

  const refreshAgentWorkspace = useCallback(async () => {
    const [nextFeed, nextAgents] = await Promise.all([getPixelFeed(projectId), getAgents(projectId)])
    setFeed(nextFeed)
    setAgentRecords(nextAgents)
    syncOfficeAgents(nextFeed)
    markSynced()
    return { nextFeed, nextAgents }
  }, [markSynced, projectId, syncOfficeAgents])

  const refreshSkillsLibrary = useCallback(async () => {
    setSkillsLibraryLoading(true)

    try {
      const response = await getSkillsLibrary(projectId)
      setSkillsLibrary(response.skills)
      markSynced()
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setSkillsLibraryLoading(false)
    }
  }, [markSynced, projectId])

  const refreshProjectSettings = useCallback(async () => {
    const settings = await getProjectSettings(projectId)
    setProjectSettings(settings)
    setLinkedRepoDraft(settings.linked_repo_path ?? '')
    markSynced()
    return settings
  }, [markSynced, projectId])

  const refreshProjectSummary = useCallback(async () => {
    const summary = await getProjectSummary(projectId)
    setProjectSummary(summary)
    markSynced()
    return summary
  }, [markSynced, projectId])

  const refreshProjectCatalog = useCallback(async () => {
    setProjectCatalogLoading(true)
    try {
      const projects = await getProjects()
      setProjectCatalog(projects)
      markSynced()
      return projects
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
      return []
    } finally {
      setProjectCatalogLoading(false)
    }
  }, [markSynced])

  const refreshRoadmap = useCallback(async () => {
    const roadmap = await getRoadmap(projectId)
    setProjectRoadmap(roadmap)
    markSynced()
    return roadmap
  }, [markSynced, projectId])

  const ensureClemsAgent = useCallback(async () => {
    let nextAgents = await getAgents(projectId)
    if (!nextAgents.some((agent) => agent.agent_id === 'clems')) {
      await createAgent(projectId, { agent_id: 'clems' })
      nextAgents = await getAgents(projectId)
    }
    setAgentRecords(nextAgents)
    return nextAgents
  }, [projectId])

  const refreshTasks = useCallback(async () => {
    const response = await getTasks(projectId)
    setTasks(response.tasks)
    setSelectedTaskId((previous) => previous ?? response.tasks[0]?.task_id ?? null)
    markSynced()
  }, [markSynced, projectId])

  const bootstrap = useCallback(async () => {
    setLoading(true)
    setApiError(null)

    try {
      const [themeLoaded, pixelRefLoaded] = await Promise.all([loadDonargTheme(), loadPixelReferenceTheme()])

      await ensureClemsAgent()

      const [layout, pixel, chat, pendingApprovals, health, profile, taskPayload, settings, roadmap, summary, projects] = await Promise.all([
        getLayout(projectId),
        getPixelFeed(projectId),
        getChat(projectId, 300, 'all'),
        getApprovals(projectId, 'pending'),
        getHealth(),
        getLlmProfile(projectId),
        getTasks(projectId),
        getProjectSettings(projectId),
        getRoadmap(projectId),
        getProjectSummary(projectId),
        getProjects(),
      ])

      const presetKey = `cockpit.video_preset_applied.${projectId}`
      let activeLayout = layout
      if (!window.localStorage.getItem(presetKey)) {
        try {
          const presetResponse = await fetch('/local-assets/presets/video-scene.layout.json')
          if (presetResponse.ok) {
            const presetLayout = (await presetResponse.json()) as Record<string, unknown>
            await putLayout(projectId, presetLayout)
            activeLayout = presetLayout
            window.localStorage.setItem(presetKey, '1')
            setUiNotice('video preset auto-applied')
          }
        } catch {
          // ignore and keep project layout
        }
      }

      officeState.rebuildFromLayout(activeLayout as never)
      setFeed(pixel)
      mergeChatMessages(chat.messages)
      setApprovals(pendingApprovals.approvals)
      setBackendHealth(health)
      setLlmProfile(profile)
      setProfileDraft(profile)
      setTasks(taskPayload.tasks)
      setProjectSettings(settings)
      setProjectCatalog(projects)
      setLinkedRepoDraft(settings.linked_repo_path ?? '')
      setProjectRoadmap(roadmap)
      setProjectSummary(summary)
      setSelectedTaskId((previous) => previous ?? taskPayload.tasks[0]?.task_id ?? null)
      setAssetsStatus({
        donarg: themeLoaded,
        pixelRef: pixelRefLoaded,
      })
      setLastEventAt(health.time ?? null)
      setActiveTab('pixel_home')
      setWorkspaceTab('agent')
      setWorkbenchPanel('chat')
      setSelectedAgentId('clems')
      setDirectTarget('clems')
      markSynced()
      syncOfficeAgents(pixel)

      if (health.status === 'ok') {
        try {
          await openTerminal(projectId, 'clems')
          await refreshPixelFeed()
        } catch {
          setUiNotice('clems terminal did not auto-open. open it from the terminal panel.')
        }
      }

      if (!themeLoaded) {
        setUiNotice('donarg assets not loaded. run import_office_tileset.sh if needed.')
      } else if (!pixelRefLoaded) {
        setUiNotice('pixel reference character assets missing. run import_pixel_reference_assets.sh.')
      }
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setLoading(false)
    }
  }, [ensureClemsAgent, markSynced, mergeChatMessages, officeState, projectId, refreshPixelFeed, syncOfficeAgents])

  const selectedTask = useMemo(
    () => tasks.find((task) => task.task_id === selectedTaskId) ?? null,
    [selectedTaskId, tasks],
  )

  useEffect(() => {
    const timer = window.setInterval(() => setClockNow(new Date()), 1000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    return () => {
      mediaRecorderRef.current?.stop()
      if (mediaStreamRef.current) {
        for (const track of mediaStreamRef.current.getTracks()) {
          track.stop()
        }
      }
    }
  }, [])

  useEffect(() => {
    if (!selectedTask) {
      setTaskEditor(emptyTaskEditor())
      return
    }
    setTaskEditor({
      title: selectedTask.title,
      owner: selectedTask.owner,
      phase: selectedTask.phase,
      status: selectedTask.status,
      objective: selectedTask.objective,
      done_definition: selectedTask.done_definition,
    })
  }, [selectedTask])

  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  useEffect(() => {
    const disconnect = connectEvents(
      projectId,
      (event) => {
        setEventLog((previous) => [event, ...previous].slice(0, 160))
        setLastEventAt(event.timestamp)

        if (event.type === 'chat.message.created') {
          const message = event.payload.message as ChatMessage | undefined
          if (message?.message_id) {
            mergeChatMessages([message])
          }
          return
        }

        if (event.type === 'chat.reset.completed') {
          setChatMessages([])
          setApprovals([])
          setUiNotice('chat reset complete')
          return
        }

        if (event.type === 'approval.requested' || event.type === 'approval.updated') {
          void refreshApprovals()
          return
        }

        if (event.type === 'task.created' || event.type === 'task.updated') {
          void refreshTasks()
          void refreshProjectSummary()
          return
        }

        if (event.type === 'agent.terminal.status') {
          const state = String(event.payload.state ?? '')
          if (state !== 'output') {
            void refreshPixelFeed()
          }
          return
        }

        if (
          event.type === 'agent.created' ||
          event.type === 'agent.updated'
        ) {
          void refreshAgentWorkspace()
          return
        }

        if (
          event.type === 'pixel.updated' ||
          event.type === 'layout.updated' ||
          event.type === 'agent.spawn.completed'
        ) {
          void refreshPixelFeed()
        }

        if (event.type === 'project.settings.updated' || event.type === 'roadmap.updated') {
          void refreshProjectSummary()
        }
      },
      (connected) => {
        wsConnectedRef.current = connected
        setWsConnected(connected)
        if (connected) {
          setComposerStatus('live')
          stopFallbackPolling('live')
          void refreshApprovals()
        } else if (!fallbackPollingRef.current) {
          setComposerStatus('reconnecting')
        }
      },
    )

    return () => {
      disconnect()
      stopFallbackPolling()
    }
  }, [
    projectId,
    mergeChatMessages,
    refreshAgentWorkspace,
    refreshApprovals,
    refreshPixelFeed,
    refreshProjectSummary,
    refreshTasks,
    stopFallbackPolling,
  ])

  useEffect(() => {
    if (activeTab === 'docs' && docsPanel === 'skills_library') {
      void refreshSkillsLibrary()
    }
  }, [activeTab, docsPanel, refreshSkillsLibrary])

  useEffect(() => {
    if (activeTab === 'overview' || (activeTab === 'docs' && docsPanel === 'project')) {
      void refreshProjectSummary()
    }
  }, [activeTab, docsPanel, refreshProjectSummary])

  useEffect(() => {
    if (activeTab === 'overview' || (activeTab === 'docs' && docsPanel === 'project')) {
      void refreshProjectCatalog()
    }
  }, [activeTab, docsPanel, refreshProjectCatalog])

  useEffect(() => {
    const listener = (rawEvent: Event) => {
      const event = rawEvent as CustomEvent<{ type: string }>
      if (!event.detail?.type) {
        return
      }
      if (event.detail.type === 'saveAgentSeats') {
        return
      }
    }

    window.addEventListener('cockpit-office-message', listener)
    return () => {
      window.removeEventListener('cockpit-office-message', listener)
    }
  }, [])

  useEffect(() => {
    let rafId = 0

    const sampleViewport = () => {
      const container = containerRef.current
      if (container) {
        const dpr = window.devicePixelRatio || 1
        const rect = container.getBoundingClientRect()
        const next = {
          viewportWidth: Math.round(rect.width * dpr),
          viewportHeight: Math.round(rect.height * dpr),
          panX: panRef.current.x,
          panY: panRef.current.y,
          dpr,
        }

        setOverlayViewport((previous) => {
          const sameSize =
            previous.viewportWidth === next.viewportWidth &&
            previous.viewportHeight === next.viewportHeight &&
            previous.dpr === next.dpr
          const samePan =
            Math.abs(previous.panX - next.panX) < 0.5 &&
            Math.abs(previous.panY - next.panY) < 0.5
          if (sameSize && samePan) {
            return previous
          }
          return next
        })
      }

      rafId = window.requestAnimationFrame(sampleViewport)
    }

    rafId = window.requestAnimationFrame(sampleViewport)
    return () => {
      window.cancelAnimationFrame(rafId)
    }
  }, [])

  const ensureAgentTerminal = useCallback(
    async (agentId: string) => {
      setSelectedAgentId(agentId)
      setApiError(null)
      try {
        await openTerminal(projectId, agentId)
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      }
    },
    [projectId],
  )

  const handleSelectAgent = useCallback((agentId: string) => {
    setSelectedAgentId(agentId)
    setDirectTarget(agentId === 'clems' ? 'clems' : 'selected_agent')
  }, [])

  const handleCreateAgent = useCallback(
    async (event: FormEvent) => {
      event.preventDefault()
      if (isSubmitting) {
        return
      }

      setIsSubmitting(true)
      setApiError(null)
      try {
        const payload = {
          agent_id: createAgentId.trim() || undefined,
          name: createAgentName.trim() || undefined,
          skills: parseSkillsInput(createAgentSkills),
        }
        const created = await createAgent(projectId, payload)
        setCreateAgentId('')
        setCreateAgentName('')
        setCreateAgentSkills('')
        setSelectedAgentId(created.agent.agent_id)
        await refreshAgentWorkspace()
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      } finally {
        setIsSubmitting(false)
      }
    },
    [createAgentId, createAgentName, createAgentSkills, isSubmitting, projectId, refreshAgentWorkspace],
  )

  const handleDeleteAgent = useCallback(
    async (agentId: string) => {
      setApiError(null)
      try {
        await deleteAgent(projectId, agentId)
        await refreshAgentWorkspace()
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      }
    },
    [projectId, refreshAgentWorkspace],
  )

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
  }, [isSavingTask, projectId, refreshProjectSummary, taskEditor])

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
  }, [isSavingTask, projectId, refreshProjectSummary, selectedTaskId, taskEditor])

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
    [projectId, refreshProjectSummary],
  )

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
  }, [isSavingProfile, profileDraft, projectId])

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
  }, [linkedRepoDraft, projectId, refreshProjectSettings, refreshProjectSummary])

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
    linkedRepoDraft,
    mergeChatMessages,
    projectId,
    projectSettings?.linked_repo_path,
    refreshApprovals,
    refreshProjectSettings,
    refreshProjectSummary,
    agentRecords,
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
  }, [isApplyingTakeover, projectId, refreshProjectSummary, refreshTasks, takeoverResult])

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
  }, [isApplyingTakeover, projectId, refreshProjectSummary, refreshRoadmap, takeoverResult])

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
    isSendingChat,
    mergeChatMessages,
    projectId,
    refreshApprovals,
    takeoverResult,
    agentRecords,
  ])

  const handleToggleVoiceRecording = useCallback(async () => {
    if (isTranscribingVoice) {
      return
    }

    if (isRecordingVoice) {
      mediaRecorderRef.current?.stop()
      setIsRecordingVoice(false)
      return
    }

    const preferred = preferredVoiceRecorder()
    if (!preferred) {
      setApiError('voice capture unsupported in this webview')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream
      voiceChunksRef.current = []
      voiceFormatRef.current = preferred.format

      const recorder = new MediaRecorder(stream, { mimeType: preferred.mimeType })
      mediaRecorderRef.current = recorder
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          voiceChunksRef.current.push(event.data)
        }
      }
      recorder.onstop = () => {
        const chunks = [...voiceChunksRef.current]
        voiceChunksRef.current = []
        mediaRecorderRef.current = null
        if (mediaStreamRef.current) {
          for (const track of mediaStreamRef.current.getTracks()) {
            track.stop()
          }
          mediaStreamRef.current = null
        }

        if (chunks.length === 0) {
          return
        }

        void (async () => {
          setIsTranscribingVoice(true)
          setApiError(null)
          try {
            const blob = new Blob(chunks, { type: preferred.mimeType })
            const audioBase64 = await blobToBase64(blob)
            const response: VoiceTranscribeResponse = await transcribeVoice(projectId, {
              audio_base64: audioBase64,
              format: voiceFormatRef.current,
            })
            if (response.status !== 'ok') {
              throw new Error(response.error || 'voice transcription failed')
            }
            const appendTranscript = activeTab === 'concierge_room' ? setRoomChatInput : setDirectChatInput
            appendTranscript((previous) => {
              const prefix = previous.trim()
              if (!prefix) {
                return response.text
              }
              return `${prefix}\n${response.text}`
            })
            setUiNotice(`voice transcribed via ${response.model}`)
          } catch (error) {
            setApiError(error instanceof Error ? error.message : String(error))
          } finally {
            setIsTranscribingVoice(false)
          }
        })()
      }
      recorder.start()
      setIsRecordingVoice(true)
      setUiNotice('recording voice message')
    } catch (error) {
      if (mediaStreamRef.current) {
        for (const track of mediaStreamRef.current.getTracks()) {
          track.stop()
        }
        mediaStreamRef.current = null
      }
      setApiError(error instanceof Error ? error.message : String(error))
    }
  }, [activeTab, isRecordingVoice, isTranscribingVoice, projectId])

  const handleOfficeClick = useCallback(
    async (numericId: number) => {
      const agentId = numericToIdRef.current.get(numericId)
      if (!agentId) {
        return
      }

      setSelectedAgentId(agentId)
      setActiveTab('pixel_home')
      setWorkspaceTab('agent')
      setWorkbenchPanel('chat')
      setDirectTarget(agentId === 'clems' ? 'clems' : 'selected_agent')
    },
    [],
  )

  const handleOfficeClose = useCallback(
    (numericId: number) => {
      const agentId = numericToIdRef.current.get(numericId)
      if (!agentId) {
        return
      }
      void handleDeleteAgent(agentId)
    },
    [handleDeleteAgent],
  )

  const activeTasksByOwner = useMemo(() => {
    const next = new Map<string, TaskRecord>()
    for (const task of [...tasks].sort(compareTasksByFreshness)) {
      if (task.status === 'done') {
        continue
      }
      if (!next.has(task.owner)) {
        next.set(task.owner, task)
      }
    }
    return next
  }, [tasks])

  const rosterAgents = useMemo<RosterAgentView[]>(() => {
    const recordsByAgentId = new Map(agentRecords.map((agent) => [agent.agent_id, agent]))
    const feedByAgentId = new Map((feed?.agents ?? []).map((agent) => [agent.agent_id, agent]))
    const preferredOrder = ['clems', 'victor', 'leo', 'nova', 'vulgarisation']
    const mergedIds = [...new Set([...preferredOrder, ...Array.from(recordsByAgentId.keys()), ...Array.from(feedByAgentId.keys())])]

    return mergedIds
      .map((agentId) => {
        const record = recordsByAgentId.get(agentId)
        const feedAgent = feedByAgentId.get(agentId)
        if (!record && !feedAgent) {
          return null
        }
        return {
          agent_id: agentId,
          name: feedAgent?.name ?? record?.name ?? agentId,
          engine: record?.engine ?? 'openrouter',
          platform: record?.platform ?? 'openrouter',
          level: feedAgent?.level ?? record?.level ?? 2,
          lead_id: feedAgent?.lead_id ?? record?.lead_id ?? null,
          role: feedAgent?.role ?? record?.role ?? 'specialist',
          chat_targetable: feedAgent?.chat_targetable ?? agentId === 'clems',
          terminal_state: feedAgent?.terminal_state ?? 'offline',
          terminal_session_id: feedAgent?.terminal_session_id ?? null,
          skills: record?.skills ?? [],
          phase: record?.phase ?? null,
          status: record?.status ?? null,
          current_task: record?.current_task ?? null,
          heartbeat: record?.heartbeat ?? null,
          scene_present: Boolean(feedAgent),
        }
      })
      .filter((agent): agent is RosterAgentView => agent !== null)
      .sort((left, right) => {
        const leftOrder = preferredOrder.indexOf(left.agent_id)
        const rightOrder = preferredOrder.indexOf(right.agent_id)
        if (leftOrder !== -1 || rightOrder !== -1) {
          return (leftOrder === -1 ? Number.MAX_SAFE_INTEGER : leftOrder) - (rightOrder === -1 ? Number.MAX_SAFE_INTEGER : rightOrder)
        }
        return left.agent_id.localeCompare(right.agent_id)
      })
  }, [agentRecords, feed])

  const selectedAgent = useMemo(
    () => rosterAgents.find((agent) => agent.agent_id === selectedAgentId) ?? null,
    [rosterAgents, selectedAgentId],
  )

  const selectedAgentChatReady = selectedAgent?.chat_targetable ?? false

  const resolvedModelForAgent = useCallback((agent: RosterAgentView): string => {
    if (!profileDraft) {
      return 'route loading'
    }
    if (agent.level === 0) {
      return modelLabel(profileDraft.clems_model)
    }
    if (agent.level === 1) {
      return modelLabel(profileDraft.l1_models[agent.agent_id] ?? 'moonshotai/kimi-k2.5')
    }
    return modelLabel(profileDraft.l2_default_model)
  }, [profileDraft])

  const visibleDirectMessages = useMemo(
    () => directChatMessages.slice(-directVisibleCount),
    [directChatMessages, directVisibleCount],
  )

  const visibleConciergeMessages = useMemo(
    () => conciergeChatMessages.slice(-roomVisibleCount),
    [conciergeChatMessages, roomVisibleCount],
  )

  const visibleInternalConciergeMessages = useMemo(
    () => internalConciergeMessages.slice(-10),
    [internalConciergeMessages],
  )

  const roomCandidateAgents = useMemo(
    () => rosterAgents.filter((agent) => agent.agent_id === 'clems' || (agent.level === 1 && agent.chat_targetable)),
    [rosterAgents],
  )

  const effectiveRoomParticipantIds = useMemo(() => {
    const allIds = roomCandidateAgents.map((agent) => agent.agent_id)
    const leadIds = roomCandidateAgents
      .filter((agent) => agent.agent_id === 'clems' || agent.level === 1)
      .map((agent) => agent.agent_id)

    if (roomParticipantMode === 'custom') {
      const custom = roomCustomParticipants.filter((agentId) => allIds.includes(agentId))
      return custom.length > 0 ? custom : ['clems']
    }
    if (roomParticipantMode === 'lead_only') {
      return leadIds
    }
    return allIds
  }, [roomCandidateAgents, roomCustomParticipants, roomParticipantMode])

  const roomParticipantLabel = useMemo(() => {
    if (effectiveRoomParticipantIds.length === 0) {
      return '@clems'
    }
    return effectiveRoomParticipantIds.map((agentId) => `@${agentId}`).join(', ')
  }, [effectiveRoomParticipantIds])

  const roomDispatchParticipantIds = useMemo(
    () => effectiveRoomParticipantIds.filter((agentId) => agentId !== 'clems'),
    [effectiveRoomParticipantIds],
  )

  const roomDispatchContext = useMemo(
    () => ({
      room_participant_mode: roomParticipantMode,
      room_participants: roomDispatchParticipantIds,
      room_participant_count: roomDispatchParticipantIds.length,
      coordinator: 'clems',
    }),
    [roomDispatchParticipantIds, roomParticipantMode],
  )

  useEffect(() => {
    if (rosterAgents.length === 0) {
      return
    }

    const selectedStillExists = selectedAgentId ? rosterAgents.some((agent) => agent.agent_id === selectedAgentId) : false
    if (selectedStillExists) {
      return
    }

    const fallbackAgent = rosterAgents.find((agent) => agent.agent_id === 'clems') ?? rosterAgents[0]
    if (!fallbackAgent) {
      return
    }

    setSelectedAgentId(fallbackAgent.agent_id)
    setDirectTarget(fallbackAgent.agent_id === 'clems' || !fallbackAgent.chat_targetable ? 'clems' : 'selected_agent')
  }, [rosterAgents, selectedAgentId])

  useEffect(() => {
    if (directTarget === 'selected_agent' && !selectedAgentChatReady) {
      setDirectTarget('clems')
    }
  }, [directTarget, selectedAgentChatReady])

  useEffect(() => {
    if (projectCatalog.length === 0) {
      if (selectedProjectDocId !== projectId) {
        setSelectedProjectDocId(projectId)
      }
      return
    }
    if (projectCatalog.some((project) => project.project_id === selectedProjectDocId)) {
      return
    }
    setSelectedProjectDocId(projectId)
  }, [projectCatalog, projectId, selectedProjectDocId])

  useEffect(() => {
    const valid = new Set(roomCandidateAgents.map((agent) => agent.agent_id))
    setRoomCustomParticipants((previous) => {
      const filtered = previous.filter((agentId) => valid.has(agentId))
      if (filtered.length > 0) {
        return filtered
      }
      return valid.has('clems') ? ['clems'] : filtered
    })
  }, [roomCandidateAgents])

  useEffect(() => {
    return () => {
      if (directRetryTimerRef.current !== null) {
        window.clearTimeout(directRetryTimerRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (!directChatLogRef.current || !directStickToBottomRef.current) {
      return
    }
    directChatLogRef.current.scrollTop = directChatLogRef.current.scrollHeight
  }, [visibleDirectMessages.length, workbenchPanel, activeTab, directSendPhase])

  useEffect(() => {
    if (!roomChatLogRef.current || !roomStickToBottomRef.current) {
      return
    }
    roomChatLogRef.current.scrollTop = roomChatLogRef.current.scrollHeight
  }, [visibleConciergeMessages.length, activeTab, takeoverResult?.run_id])

  const handleSendChat = useCallback(async ({
    targetMode = directTarget,
    chatMode = activeChatMode,
    contextRef = null,
  }: {
    targetMode?: DirectTargetMode
    chatMode?: ChatMode
    contextRef?: Record<string, unknown> | null
  } = {}) => {
    const activeInput = chatMode === 'conceal_room' ? roomChatInput : directChatInput
    const text = activeInput.trim()
    if (!text || isSendingChat) {
      return
    }

    if (chatMode === 'conceal_room') {
      roomStickToBottomRef.current = true
    } else {
      directStickToBottomRef.current = true
    }

    let resolvedTargetMode = targetMode
    let targetAgentId =
      chatMode === 'direct' && resolvedTargetMode === 'selected_agent'
        ? (selectedAgent?.chat_targetable ? selectedAgent.agent_id : null)
        : null

    if (chatMode === 'direct' && resolvedTargetMode === 'selected_agent' && !targetAgentId) {
      resolvedTargetMode = 'clems'
      targetAgentId = null
      setDirectTarget('clems')
      setUiNotice('selected agent not chat-ready. direct chat stays on @clems.')
    }

    if (chatMode === 'conceal_room') {
      setRoomChatInput('')
    } else {
      setDirectChatInput('')
      setDirectSendPhase('thinking')
      if (directRetryTimerRef.current !== null) {
        window.clearTimeout(directRetryTimerRef.current)
      }
      directRetryTimerRef.current = window.setTimeout(() => {
        setDirectSendPhase((previous) => (previous === 'thinking' ? 'retrying' : previous))
      }, 10000)
    }
    setApiError(null)
    setUiNotice(null)
    setIsSendingChat(true)
    if (chatMode === 'direct') {
      setDirectTarget(resolvedTargetMode)
    }

    let keepDirectDegradedState = false

    try {
      const response = await liveTurn(projectId, {
        text,
        chat_mode: chatMode,
        execution_mode: executionMode,
        target_agent_id: targetAgentId,
        mentions: chatMode === 'conceal_room' ? ['clems'] : undefined,
        context_ref: chatMode === 'conceal_room' ? (contextRef ?? roomDispatchContext) : contextRef,
      })

      mergeChatMessages(response.messages)
      if (response.approval_requests.length > 0) {
        void refreshApprovals()
      }

      if (response.error) {
        const hasVisibleReply = response.messages.some(
          (message) =>
            message.visibility !== 'internal' &&
            message.author !== 'operator' &&
            messageChatMode(message) === chatMode &&
            (chatMode !== 'direct' || !isSyntheticDirectReply(message)),
        )

        setFallbackDiagnostics((previous) => [
          {
            id: `${Date.now()}-${chatMode}`,
            timestamp: new Date().toISOString(),
            chatMode,
            error: response.error ?? 'unknown_chat_error',
          },
          ...previous,
        ].slice(0, 12))

        if (response.error === 'some_llm_calls_failed_using_fallback' && hasVisibleReply) {
          // Keep the main chat surface quiet when a visible reply already exists.
        } else if (chatMode === 'direct' && !hasVisibleReply) {
          setDirectChatInput(text)
          setDirectSendPhase('degraded')
          keepDirectDegradedState = true
          setUiNotice('OpenRouter degraded, direct reply unavailable. Retry or switch to Le Conseil.')
        } else {
          setUiNotice(`degraded mode: ${response.error}`)
        }
      }

      if (!wsConnectedRef.current || response.delivery_mode !== 'ws') {
        startFallbackPolling()
      } else {
        setComposerStatus('live')
      }
    } catch (error) {
      if (chatMode === 'conceal_room') {
        setRoomChatInput(text)
      } else {
        setDirectChatInput(text)
      }
      setApiError(error instanceof Error ? error.message : String(error))
      setUiNotice('send failed. draft restored.')
    } finally {
      if (directRetryTimerRef.current !== null) {
        window.clearTimeout(directRetryTimerRef.current)
        directRetryTimerRef.current = null
      }
      if (chatMode === 'direct' && !keepDirectDegradedState) {
        setDirectSendPhase(null)
      }
      setIsSendingChat(false)
    }
  }, [
    activeChatMode,
    directChatInput,
    directTarget,
    executionMode,
    isSendingChat,
    mergeChatMessages,
    projectId,
    refreshApprovals,
    roomChatInput,
    roomDispatchContext,
    selectedAgent,
    startFallbackPolling,
  ])

  const handleRestartTerminal = useCallback(async () => {
    if (!selectedAgentId) {
      return
    }

    setApiError(null)
    try {
      await restartTerminal(projectId, selectedAgentId)
      await refreshPixelFeed()
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    }
  }, [projectId, refreshPixelFeed, selectedAgentId])

  const handleOpenExternalTerminal = useCallback(async () => {
    if (!selectedAgentId) {
      return
    }

    setApiError(null)
    try {
      const session = await openTerminal(projectId, selectedAgentId)
      await openOsTerminal(selectedAgentId, session.cwd)
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    }
  }, [projectId, selectedAgentId])

  const handleOpenExternalTerminalForAgent = useCallback(
    async (agentId: string) => {
      setSelectedAgentId(agentId)
      setApiError(null)
      try {
        const session = await openTerminal(projectId, agentId)
        await openOsTerminal(agentId, session.cwd)
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      }
    },
    [projectId],
  )

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
  }, [linkedRepoDraft, newProjectRepoDraft])

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
  }, [isCreatingProject, newProjectIdDraft, newProjectNameDraft, newProjectRepoDraft])

  const handleQuickAgent = useCallback(
    async (agentId: string) => {
      setApiError(null)
      setActiveTab('pixel_home')
      setWorkspaceTab('agent')
      setWorkbenchPanel('chat')
      try {
        if (!agentRecords.some((agent) => agent.agent_id === agentId)) {
          await createAgent(projectId, { agent_id: agentId })
          await refreshAgentWorkspace()
        }

        setSelectedAgentId(agentId)
        if (agentId === 'clems') {
          setDirectTarget('clems')
          await ensureAgentTerminal('clems')
        } else {
          setDirectTarget('selected_agent')
        }
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      }
    },
    [agentRecords, ensureAgentTerminal, projectId, refreshAgentWorkspace],
  )

  const handleApproval = useCallback(
    async (requestId: string, decision: 'approve' | 'reject') => {
      setApprovalBusy((previous) => ({
        ...previous,
        [requestId]: true,
      }))

      setApiError(null)
      try {
        if (decision === 'approve') {
          await approveApproval(projectId, requestId, {
            decided_by: 'operator',
            note: 'approved from cockpit ui',
          })
        } else {
          await rejectApproval(projectId, requestId, {
            decided_by: 'operator',
            note: 'rejected from cockpit ui',
          })
        }
        await refreshApprovals()
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      } finally {
        setApprovalBusy((previous) => ({
          ...previous,
          [requestId]: false,
        }))
      }
    },
    [projectId, refreshApprovals],
  )

  const handleResetChat = useCallback(async () => {
    if (!window.confirm('Reset chat now? This clears global chat and approvals history.')) {
      return
    }

    setApiError(null)
    setUiNotice(null)
    try {
      await resetChat(projectId)
      setChatMessages([])
      setApprovals([])
      setUiNotice('chat reset complete')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    }
  }, [projectId])

  const handleApplyVideoPreset = useCallback(async () => {
    setApiError(null)
    setUiNotice(null)
    try {
      const response = await fetch('/local-assets/presets/video-scene.layout.json')
      if (!response.ok) {
        throw new Error('preset file missing: public/local-assets/presets/video-scene.layout.json')
      }
      const layout = (await response.json()) as Record<string, unknown>
      await putLayout(projectId, layout)
      window.localStorage.setItem(`cockpit.video_preset_applied.${projectId}`, '1')
      officeState.rebuildFromLayout(layout as never)
      setRefreshTick((value) => value + 1)
      await refreshPixelFeed()
      setUiNotice('video preset applied')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    }
  }, [officeState, projectId, refreshPixelFeed])

  const addMention = useCallback((mention: string, surface: 'direct' | 'room') => {
    const applyInput = surface === 'room' ? setRoomChatInput : setDirectChatInput
    applyInput((previous) => {
      if (previous.trim().length === 0) {
        return `@${mention} `
      }
      return `${previous} @${mention} `
    })
    if (surface === 'room') {
      setShowRoomAddMenu(false)
    }
  }, [])

  const agentNumericIds = useMemo(() => {
    if (rosterAgents.length === 0) {
      return []
    }
    return rosterAgents.map((agent) => toNumericId(agent.agent_id))
  }, [rosterAgents, toNumericId])

  const profileDirty = useMemo(() => {
    if (!llmProfile || !profileDraft) {
      return false
    }
    return JSON.stringify(llmProfile) !== JSON.stringify(profileDraft)
  }, [llmProfile, profileDraft])
  const l1Agents = useMemo(() => {
    const fromFeed = rosterAgents.filter((agent) => agent.level === 1).map((agent) => agent.agent_id)
    const fromProfile = profileDraft ? Object.keys(profileDraft.l1_models ?? {}) : []
    return [...new Set([...fromFeed, ...fromProfile])].sort()
  }, [profileDraft, rosterAgents])
  const directTargetLabel =
    directTarget === 'selected_agent'
      ? selectedAgent && selectedAgentChatReady
        ? `@${selectedAgent.agent_id}`
        : '@clems'
      : '@clems'
  const directTargetBadge =
    directTarget === 'selected_agent' && selectedAgent && selectedAgentChatReady
      ? `Selected agent ${directTargetLabel}`
      : 'Clems default'
  const directTargetNotice =
    directTarget === 'selected_agent'
      ? selectedAgent && selectedAgentChatReady
        ? `target @${selectedAgent.agent_id}`
        : selectedAgent
          ? `@${selectedAgent.agent_id} not chat-ready. fallback @clems.`
          : 'No agent selected. fallback @clems.'
      : ''

  const activeProjectCard = useMemo<ProjectCatalogEntry>(
    () =>
      projectCatalog.find((project) => project.project_id === projectId) ?? {
        project_id: projectId,
        project_name: projectSettings?.project_name ?? projectId,
        linked_repo_path: projectSettings?.linked_repo_path ?? null,
        phase: projectSummary?.phase ?? 'Implement',
        objective: projectSummary?.objective ?? 'No objective set yet.',
      },
    [
      projectCatalog,
      projectId,
      projectSettings?.linked_repo_path,
      projectSettings?.project_name,
      projectSummary?.objective,
      projectSummary?.phase,
    ],
  )
  const visibleProjectCards = useMemo(() => [activeProjectCard], [activeProjectCard])
  const selectedProjectCard =
    visibleProjectCards.find((project) => project.project_id === selectedProjectDocId) ?? activeProjectCard

  const topTabs = useMemo(
    () => [
      { id: 'pixel_home' as const, label: 'Pixel Home' },
      { id: 'concierge_room' as const, label: 'Le Conseil' },
      { id: 'overview' as const, label: 'Overview' },
      { id: 'pilotage' as const, label: 'Pilotage' },
      { id: 'docs' as const, label: 'Docs' },
      { id: 'todo' as const, label: 'To Do' },
      { id: 'model_routing' as const, label: 'Model Routing' },
    ],
    [],
  )

  const workspaceTabs = useMemo(
    () => [
      { id: 'agent' as const, label: 'Agents' },
      { id: 'layout' as const, label: 'Layout' },
      { id: 'settings' as const, label: 'Settings' },
    ],
    [],
  )

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-card">
          <h1>Cockpit</h1>
          <p>Loading Pixel Home...</p>
        </div>
      </div>
    )
  }

  const composerLabel =
    composerStatus === 'live'
      ? 'Live'
      : composerStatus === 'http_fallback'
        ? 'HTTP fallback'
        : 'Reconnecting'
  const openRouterHealth = backendHealth?.openrouter ?? null
  const openRouterLabel =
    openRouterHealth?.status === 'ready'
      ? 'OpenRouter ready'
      : openRouterHealth?.status === 'degraded'
        ? 'OpenRouter degraded'
        : openRouterHealth?.status === 'missing_key'
          ? 'OpenRouter missing key'
          : openRouterHealth?.status === 'missing_base_url'
            ? 'OpenRouter missing base url'
            : 'OpenRouter unknown'
  const openRouterPillTone =
    openRouterHealth?.status === 'ready' ? 'ok' : openRouterHealth?.status ? 'warn' : 'neutral'

  const workbenchTabs = [
    { id: 'chat' as const, label: 'Chat' },
    {
      id: 'terminal' as const,
      label: 'Terminal',
      count: selectedAgent?.terminal_state === 'running' ? 'live' : selectedAgentId ? 'offline' : 'none',
    },
    { id: 'approvals' as const, label: 'Approvals', count: approvals.length > 0 ? String(approvals.length) : undefined },
    { id: 'events' as const, label: 'Events', count: eventLog.length > 0 ? String(Math.min(eventLog.length, 99)) : undefined },
  ] satisfies Array<{ id: WorkbenchPanel; label: string; count?: string }>

  const renderWorkspaceLeftPanel = () => {
    if (workspaceTab === 'layout') {
      return (
        <section className="workspace-section">
          <div className="section-title-row">
            <h2>Layout</h2>
            <span className="hint">Donarg compatible</span>
          </div>
          <p className="small-copy">The scene is loaded from project layout and stays file-compatible.</p>
          <button
            className="small-btn"
            onClick={() => {
              void bootstrap()
            }}
          >
            Reload layout
          </button>
          <button
            className="small-btn"
            onClick={() => {
              void handleApplyVideoPreset()
            }}
          >
            Apply video preset
          </button>
          <button
            className="small-btn"
            onClick={() => {
              panRef.current = { x: 0, y: 0 }
              setZoom(2)
            }}
          >
            Reset camera
          </button>
        </section>
      )
    }

    if (workspaceTab === 'settings') {
      return (
        <section className="workspace-section">
          <div className="section-title-row">
            <h2>Settings</h2>
            <span className="hint">Runtime</span>
          </div>
          <ul className="settings-list">
            <li>chat mode: {activeChatMode}</li>
            <li>execution mode: {executionMode}</li>
            <li>ws: {wsConnected ? 'connected' : 'reconnecting'}</li>
            <li>api: {getApiUrl()}</li>
            <li>last sync: {lastSyncAt ? new Date(lastSyncAt).toLocaleTimeString() : 'none'}</li>
          </ul>
        </section>
      )
    }

    return (
      <section className="workspace-section workspace-section-agents">
        <div className="section-title-row compact">
          <h2>Agents</h2>
          <span className="hint">stable roster + quick launch</span>
        </div>

        <div className="agent-create-card">
          <div className="quick-agent-row">
            {QUICK_AGENT_PRESETS.map((preset) => {
              const isSelected = selectedAgentId === preset.agent_id
              const exists = agentRecords.some((agent) => agent.agent_id === preset.agent_id)
              return (
                <button
                  key={preset.agent_id}
                  className={`quick-agent-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => {
                    void handleQuickAgent(preset.agent_id)
                  }}
                  type="button"
                >
                  <span>{preset.label}</span>
                  <span className="quick-agent-meta">{exists ? 'ready' : 'create'}</span>
                </button>
              )
            })}
          </div>
          <form className="create-form compact" onSubmit={handleCreateAgent}>
            <input
              ref={createAgentIdInputRef}
              aria-label="Agent id optional"
              placeholder="agent id (optional)"
              value={createAgentId}
              onChange={(event) => setCreateAgentId(event.target.value)}
            />
            <input
              aria-label="Agent name optional"
              placeholder="name (optional)"
              value={createAgentName}
              onChange={(event) => setCreateAgentName(event.target.value)}
            />
            <input
              aria-label="Agent skills comma separated"
              placeholder="skills (comma separated)"
              value={createAgentSkills}
              onChange={(event) => setCreateAgentSkills(event.target.value)}
            />
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : '+ Agent'}
            </button>
          </form>
          <p className="small-copy">
            Clems is always live at startup. L1 leads are one click away. Add skills now or assign them later.
          </p>
        </div>

        {selectedAgent ? (
          <div className="selected-agent-banner">
            <div className="selected-agent-avatar">{agentInitials(selectedAgent.name, selectedAgent.agent_id)}</div>
            <div className="selected-agent-copy">
              <p className="selected-agent-label">Selected now</p>
              <strong>@{selectedAgent.agent_id}</strong>
              <span>{formatAgentState(selectedAgent.phase, selectedAgent.status)}</span>
              <span>
                {selectedAgent.current_task
                  ? `task ${selectedAgent.current_task}`
                  : activeTasksByOwner.get(selectedAgent.agent_id)
                    ? `task ${activeTasksByOwner.get(selectedAgent.agent_id)?.title}`
                    : 'no active task'}
              </span>
              <span>
                {selectedAgent.chat_targetable ? 'chat ready' : 'chat unavailable'} - terminal{' '}
                {selectedAgent.terminal_state === 'running' ? 'live' : 'offline'} - {formatHeartbeat(selectedAgent.heartbeat)}
              </span>
              <span>
                model {resolvedModelForAgent(selectedAgent)} - {selectedAgent.scene_present ? 'on scene' : 'off scene'}
              </span>
            </div>
          </div>
        ) : null}

        <div className="agent-cards" tabIndex={0} aria-label="Agent roster">
          {rosterAgents.map((agent) => (
            <article
              key={agent.agent_id}
              className={`agent-card level-${agent.level} ${selectedAgentId === agent.agent_id ? 'active' : ''}`}
            >
              <button className="agent-card-main" onClick={() => handleSelectAgent(agent.agent_id)}>
                <div className="agent-card-head">
                  <div className="agent-identity">
                    <div className="agent-avatar">{agentInitials(agent.name, agent.agent_id)}</div>
                    <div>
                      <p className="agent-name">{agent.name}</p>
                      <p className="agent-meta">@{agent.agent_id}</p>
                    </div>
                  </div>
                  <span className="agent-level-pill">L{agent.level}</span>
                </div>
                <div className="agent-card-copy">
                  <p className="agent-role">{agent.role}</p>
                  <p className="agent-lead">
                    {agent.lead_id ? `lead @${agent.lead_id}` : 'top-level operator lane'}
                  </p>
                  <p className="agent-runtime-line">
                    model {resolvedModelForAgent(agent)} - {agent.platform}
                  </p>
                  <p className="agent-runtime-line">
                    {agent.current_task
                      ? `task ${agent.current_task}`
                      : activeTasksByOwner.get(agent.agent_id)
                        ? `task ${activeTasksByOwner.get(agent.agent_id)?.title}`
                        : 'no open task assigned'}
                  </p>
                  <p className="agent-runtime-line">{formatAgentState(agent.phase, agent.status)}</p>
                  <p className="agent-runtime-line">{formatHeartbeat(agent.heartbeat)}</p>
                </div>
                {agent.skills.length > 0 ? (
                  <div className="agent-skill-row">
                    {agent.skills.slice(0, 3).map((skill) => (
                      <span key={skill} className="skill-chip" title={skill}>
                        {formatSkillChip(skill)}
                      </span>
                    ))}
                    {agent.skills.length > 3 ? <span className="skill-chip overflow">+{agent.skills.length - 3}</span> : null}
                  </div>
                ) : (
                  <p className="agent-skill-empty">No skills assigned yet.</p>
                )}
                <div className="agent-card-statuses">
                  <span className={`dot ${agent.chat_targetable ? 'green' : 'gray'}`}>
                    {agent.chat_targetable ? 'chat ready' : 'chat unavailable'}
                  </span>
                  <span className={`dot ${agent.terminal_state === 'running' ? 'green' : 'gray'}`}>
                    terminal {agent.terminal_state === 'running' ? 'live' : 'offline'}
                  </span>
                  <span className={`dot ${agent.scene_present ? 'green' : 'gray'}`}>
                    {agent.scene_present ? 'on scene' : 'off scene'}
                  </span>
                </div>
              </button>
              <div className="agent-card-footer">
                <button
                  className="agent-action"
                  onClick={() => {
                    void handleOpenExternalTerminalForAgent(agent.agent_id)
                  }}
                >
                  Open terminal
                </button>
                <button
                  className="agent-action"
                  onClick={() => {
                    setSelectedAgentId(agent.agent_id)
                    setActiveTab('pixel_home')
                    setWorkbenchPanel('chat')
                    setDirectTarget(agent.agent_id === 'clems' ? 'clems' : 'selected_agent')
                  }}
                >
                  Chat
                </button>
                {agent.agent_id !== 'clems' ? (
                  <button
                    className="agent-delete"
                    onClick={() => {
                      void handleDeleteAgent(agent.agent_id)
                    }}
                  >
                    Remove
                  </button>
                ) : (
                  <span className="agent-keeper">system</span>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
    )
  }

  const renderSecondaryTab = () => {
    const agentsTotal = feed?.agents.length ?? 0
    const runningTerminals = feed?.terminals_alive ?? 0
    const queueDepth = feed?.queue_depth ?? 0
    const chatReadyCount = rosterAgents.filter((agent) => agent.chat_targetable).length
    const leadsCount = rosterAgents.filter((agent) => agent.level === 1).length
    const latestDirect = directChatMessages.slice(-8).reverse()
    const latestRoom = conciergeChatMessages.slice(-8).reverse()
    const latestInternal = internalConciergeMessages.slice(-8).reverse()
    const latestEvents = eventLog.slice(0, 20)
    const recentTasks = [...tasks].sort(compareTasksByFreshness).slice(0, 5)
    const linkedRepoLabel = projectSummary?.linked_repo_path ?? projectSettings?.linked_repo_path ?? 'not linked'
    const currentProjectLabel = projectLabel(projectId, projectSettings?.project_name ?? projectId)
    const projectPhase = projectSummary?.phase ?? 'unknown'
    const projectObjective = projectSummary?.objective ?? 'No objective set yet.'
    const roadmapNow = projectSummary?.roadmap_now ?? projectRoadmap?.sections.now ?? []
    const roadmapNext = projectSummary?.roadmap_next ?? projectRoadmap?.sections.next ?? []
    const roadmapRisks = projectSummary?.roadmap_risks ?? projectRoadmap?.sections.risks ?? []
    const projectDecisions = projectSummary?.latest_decisions ?? []
    const projectTaskCounts = projectSummary?.open_task_counts
    const monthlyCostLabel = formatCurrencyCad(projectSummary?.monthly_cost_estimate_cad)
    const costEventsLabel = String(projectSummary?.cost_events_this_month ?? 0)
    const modelUsageSummary = projectSummary?.model_usage_summary ?? []
    const taskCounts = STATUS_ORDER.reduce<Record<TaskStatus, number>>(
      (accumulator, status) => ({
        ...accumulator,
        [status]: tasks.filter((task) => task.status === status).length,
      }),
      {
        todo: 0,
        in_progress: 0,
        blocked: 0,
        done: 0,
      },
    )

    const quickStatus = [
      { label: 'Backend', value: backendHealth?.status ?? 'unknown' },
      { label: 'OpenRouter', value: openRouterHealth?.status ?? 'unknown' },
      { label: 'WS', value: composerLabel },
      { label: 'Agents', value: String(agentsTotal) },
      { label: 'Terminals live', value: String(runningTerminals) },
      { label: 'Queue', value: String(queueDepth) },
      {
        label: 'Tasks open',
        value: String(
          projectTaskCounts
            ? projectTaskCounts.todo + projectTaskCounts.in_progress + projectTaskCounts.blocked
            : taskCounts.todo + taskCounts.in_progress + taskCounts.blocked,
        ),
      },
    ]

    if (activeTab === 'concierge_room') {
      return (
        <section className="secondary-tab panel concierge-tab">
          <div className="secondary-header">
            <h2>Le Conseil</h2>
            <span className="hint">multi-agent board room with Clems on coordination duty</span>
          </div>
          <div className="concierge-layout">
            <section className="secondary-card concierge-chat-card">
              <div className="chat-head-block room-head-block">
                <div className="section-title-row">
                  <div className="chat-title-block">
                    <h3>Board room</h3>
                    <p className="small-copy">Clems coordinates the visible room answer while leads execute in parallel.</p>
                  </div>
                  <div className="chat-actions">
                    <span className={`chat-status ${composerStatus}`}>{composerLabel}</span>
                    <span className="chat-target">visible answer via @clems</span>
                  </div>
                </div>
                <div className="chat-toolbar-card room-toolbar-card">
                  <div className="chat-toolbar-row">
                    <div className="direct-chat-toolbar-group">
                      <span className="mode-pill active">Le Conseil</span>
                      <span className="mode-pill">participants {effectiveRoomParticipantIds.length}</span>
                      <span className="mode-pill">active agents {agentsTotal}</span>
                    </div>
                    <div className="chat-actions">
                      {conciergeChatMessages.length > 8 ? (
                        <>
                          <span className="hint">latest {Math.min(roomVisibleCount, conciergeChatMessages.length)}</span>
                          <button
                            className="small-btn"
                            onClick={() => setRoomVisibleCount((value) => Math.min(conciergeChatMessages.length, value + 12))}
                            disabled={roomVisibleCount >= conciergeChatMessages.length}
                          >
                            Show older
                          </button>
                          <button
                            className="small-btn"
                            onClick={() => setRoomVisibleCount(8)}
                            disabled={roomVisibleCount <= 8}
                          >
                            Show latest
                          </button>
                        </>
                      ) : null}
                    </div>
                  </div>
                  <div className="chat-toolbar-row">
                    <span className="chat-target">participants {roomParticipantLabel}</span>
                    <div className="exec-toggle">
                      <button
                        className={executionMode === 'chat' ? 'active' : ''}
                        onClick={() => setExecutionMode('chat')}
                      >
                        chat
                      </button>
                      <button
                        className={executionMode === 'scene' ? 'active' : ''}
                        onClick={() => setExecutionMode('scene')}
                      >
                        scene
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div className="secondary-card project-actions-card">
                <div className="section-title-row compact">
                  <h3>Project actions</h3>
                  <span className="hint">{currentProjectLabel} - {linkedRepoLabel}</span>
                </div>
                <div className="project-actions-mode-row">
                  <button
                    className={`small-btn ${projectActionMode === 'create' ? 'active' : ''}`}
                    type="button"
                    aria-pressed={projectActionMode === 'create'}
                    onClick={() => setProjectActionMode((value) => (value === 'create' ? null : 'create'))}
                  >
                    Create new project
                  </button>
                  <button
                    className={`small-btn ${projectActionMode === 'takeover' ? 'active' : ''}`}
                    type="button"
                    aria-pressed={projectActionMode === 'takeover'}
                    onClick={() => setProjectActionMode((value) => (value === 'takeover' ? null : 'takeover'))}
                  >
                    Take over a project
                  </button>
                </div>
                {projectActionMode === 'create' ? (
                  <div className="project-action-form">
                    <div className="form-grid">
                      <label>
                        <span>Project id</span>
                        <input
                          value={newProjectIdDraft}
                          onChange={(event) => setNewProjectIdDraft(event.target.value)}
                          aria-label="New project id"
                          placeholder="new-project"
                        />
                      </label>
                      <label>
                        <span>Project name</span>
                        <input
                          value={newProjectNameDraft}
                          onChange={(event) => setNewProjectNameDraft(event.target.value)}
                          aria-label="New project name"
                          placeholder="Project name"
                        />
                      </label>
                      <label className="wide">
                        <span>Linked repo path (optional)</span>
                        <div className="inline-picker-row">
                          <input
                            value={newProjectRepoDraft}
                            onChange={(event) => setNewProjectRepoDraft(event.target.value)}
                            aria-label="Linked repository path optional"
                            placeholder="/absolute/path/to/repo"
                          />
                          <button className="small-btn" type="button" onClick={() => void handleChooseRepoFolder('create')} disabled={isChoosingFolder}>
                            {isChoosingFolder ? 'Choosing...' : 'Choose folder'}
                          </button>
                        </div>
                      </label>
                    </div>
                    <div className="todo-editor-actions">
                      <button className="send-btn" onClick={() => void handleCreateProject()} disabled={isCreatingProject}>
                        {isCreatingProject ? 'Creating...' : 'Create project'}
                      </button>
                    </div>
                  </div>
                ) : null}
                {projectActionMode === 'takeover' ? (
                  <div className="project-action-form">
                    <div className="form-grid">
                      <label className="wide">
                        <span>Linked repo path</span>
                        <div className="inline-picker-row">
                          <input
                            value={linkedRepoDraft}
                            onChange={(event) => setLinkedRepoDraft(event.target.value)}
                            aria-label="Linked repository path"
                            placeholder="/absolute/path/to/repo"
                          />
                          <button className="small-btn" type="button" onClick={() => void handleChooseRepoFolder('takeover')} disabled={isChoosingFolder}>
                            {isChoosingFolder ? 'Choosing...' : 'Choose folder'}
                          </button>
                        </div>
                      </label>
                    </div>
                    <div className="todo-editor-actions">
                      <button className="send-btn alt" onClick={() => void handleSaveProjectLink()}>
                        Save linked repo
                      </button>
                      <button className="send-btn" onClick={() => void handleRunTakeover()} disabled={isRunningTakeover}>
                        {isRunningTakeover ? 'Running takeover...' : 'Take over project'}
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
              {takeoverResult ? (
                <div className="takeover-wizard-card">
                  <div className="section-title-row compact">
                    <h3>Takeover wizard</h3>
                    <span className="hint">{takeoverResult.linked_repo_path || 'repo not linked'}</span>
                  </div>
                  <p className="takeover-summary">{takeoverResult.summary_human}</p>
                  <div className="takeover-columns">
                    <div>
                      <h4>Tech summary</h4>
                      <ul className="simple-list">
                        {takeoverResult.summary_tech.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4>Suggested tasks</h4>
                      <ul className="simple-list">
                        {takeoverResult.suggested_tasks.map((task) => (
                          <li key={`${task.owner}-${task.title}`}>
                            {task.title} - @{task.owner}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  <div className="todo-editor-actions">
                    <button
                      className="send-btn alt"
                      onClick={() => void handleApplyTakeoverRoadmap()}
                      disabled={isApplyingTakeover}
                    >
                      {isApplyingTakeover ? 'Applying...' : 'Apply roadmap draft'}
                    </button>
                    <button
                      className="send-btn"
                      onClick={() => void handleApplyTakeoverTasks()}
                      disabled={isApplyingTakeover || takeoverResult.suggested_tasks.length === 0}
                    >
                      {isApplyingTakeover ? 'Applying...' : 'Add suggested tasks to To Do'}
                    </button>
                    <button className="small-btn" onClick={() => void handleRunTakeover()} disabled={isRunningTakeover}>
                      {isRunningTakeover ? 'Running...' : 'Rerun takeover'}
                    </button>
                    <button className="small-btn" onClick={() => void handleLaunchTakeoverPlan()} disabled={isSendingChat}>
                      Lets go
                    </button>
                    <button className="small-btn" onClick={() => setActiveTab('overview')}>
                      Back to Overview
                    </button>
                  </div>
                </div>
              ) : null}
              <div
                ref={roomChatLogRef}
                className="chat-log concierge-log"
                tabIndex={0}
                aria-label="Le Conseil room transcript"
                onScroll={(event) => {
                  const node = event.currentTarget
                  roomStickToBottomRef.current = node.scrollHeight - node.scrollTop - node.clientHeight < 40
                }}
              >
                {visibleConciergeMessages.length === 0 ? (
                  <p className="chat-empty">No room traffic yet. Send a first operator instruction to @clems or widen the participant set.</p>
                ) : (
                  visibleConciergeMessages.map((message) => (
                    <article
                      key={message.message_id}
                      className={`chat-row ${message.author === 'operator' ? 'operator' : message.author === 'clems' ? 'clems' : 'agent'}`}
                    >
                      <header>
                        <div className="chat-row-meta">
                          <strong className="chat-author">@{message.author}</strong>
                          {messageKindLabel(message) ? <span className="chat-kind">{messageKindLabel(message)}</span> : null}
                        </div>
                        <time className="chat-time">{new Date(message.timestamp).toLocaleTimeString()}</time>
                      </header>
                      <p className="chat-body">{message.text}</p>
                    </article>
                  ))
                )}
              </div>
                <div className="composer-stack">
                <div className="composer-row composer-row-room">
                  <div className="plus-wrap">
                    <button
                      className="plus-btn"
                      type="button"
                      aria-label="Open mention shortcuts"
                      onClick={() => setShowRoomAddMenu((value) => !value)}
                    >
                      +
                    </button>
                    {showRoomAddMenu ? (
                      <div className="plus-menu">
                        <button type="button" onClick={() => addMention('clems', 'room')}>mention @clems</button>
                        <button type="button" onClick={() => addMention('victor', 'room')}>mention @victor</button>
                        <button type="button" onClick={() => addMention('leo', 'room')}>mention @leo</button>
                        <button type="button" onClick={() => addMention('nova', 'room')}>mention @nova</button>
                      </div>
                    ) : null}
                  </div>
                  <input
                    value={roomChatInput}
                    aria-label="Le Conseil message"
                    onChange={(event) => setRoomChatInput(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        event.preventDefault()
                        void handleSendChat({ chatMode: 'conceal_room', contextRef: roomDispatchContext })
                      }
                    }}
                    placeholder="Ask @clems to coordinate the board room."
                  />
                  <button
                    className={`small-btn voice-btn ${isRecordingVoice ? 'recording' : ''}`}
                    type="button"
                    aria-label={isRecordingVoice ? 'Stop voice recording' : 'Start voice recording'}
                    onClick={() => void handleToggleVoiceRecording()}
                    disabled={isTranscribingVoice}
                  >
                    {isTranscribingVoice ? 'Transcribing...' : isRecordingVoice ? 'Stop voice' : 'Voice'}
                  </button>
                  <button
                    className="send-btn"
                    type="button"
                    onClick={() => void handleSendChat({ chatMode: 'conceal_room', contextRef: roomDispatchContext })}
                    disabled={isSendingChat}
                  >
                    {isSendingChat ? 'Sending...' : 'Send to Le Conseil'}
                  </button>
                  {takeoverResult ? (
                    <button className="send-btn alt" onClick={() => void handleLaunchTakeoverPlan()} disabled={isSendingChat}>
                      Lets go
                    </button>
                  ) : null}
                </div>
              </div>
            </section>
            <div className="concierge-support-grid">
              <section className="secondary-card concierge-side-card participant-filter-card">
                <div className="section-title-row compact">
                  <h3>Participants</h3>
                  <span className="hint">Clems coordinates: {roomParticipantLabel}</span>
                </div>
                <div className="participant-mode-row">
                  <button
                    className={`small-btn ${roomParticipantMode === 'all_active' ? 'active' : ''}`}
                    type="button"
                    aria-pressed={roomParticipantMode === 'all_active'}
                    onClick={() => setRoomParticipantMode('all_active')}
                  >
                    All active
                  </button>
                  <button
                    className={`small-btn ${roomParticipantMode === 'lead_only' ? 'active' : ''}`}
                    type="button"
                    aria-pressed={roomParticipantMode === 'lead_only'}
                    onClick={() => setRoomParticipantMode('lead_only')}
                  >
                    Leads only
                  </button>
                  <button
                    className={`small-btn ${roomParticipantMode === 'custom' ? 'active' : ''}`}
                    type="button"
                    aria-pressed={roomParticipantMode === 'custom'}
                    onClick={() => setRoomParticipantMode('custom')}
                  >
                    Custom
                  </button>
                </div>
                {roomParticipantMode === 'custom' ? (
                  <div className="participant-chip-row">
                    {roomCandidateAgents.map((agent) => {
                      const active = roomCustomParticipants.includes(agent.agent_id)
                      return (
                        <button
                          key={agent.agent_id}
                          className={`participant-chip ${active ? 'active' : ''}`}
                          type="button"
                          aria-pressed={active}
                          onClick={() =>
                            setRoomCustomParticipants((previous) =>
                              previous.includes(agent.agent_id)
                                ? previous.filter((agentId) => agentId !== agent.agent_id)
                                : [...previous, agent.agent_id],
                            )
                          }
                        >
                          @{agent.agent_id}
                        </button>
                      )
                    })}
                  </div>
                ) : null}
              </section>
              <section className="secondary-card concierge-side-card">
                <h3>Room snapshot</h3>
                <div className="concierge-score-grid">
                  <article>
                    <span>Active agents</span>
                    <strong>{agentsTotal}</strong>
                  </article>
                  <article>
                    <span>Chat ready</span>
                    <strong>{chatReadyCount}</strong>
                  </article>
                  <article>
                    <span>Approvals</span>
                    <strong>{approvals.length}</strong>
                  </article>
                  <article>
                    <span>Open tasks</span>
                    <strong>{taskCounts.todo + taskCounts.in_progress + taskCounts.blocked}</strong>
                  </article>
                </div>
                <ul className="data-list">
                  <li>
                    <span>Room mode</span>
                    <strong>{roomParticipantMode === 'all_active' ? 'all active' : roomParticipantMode === 'lead_only' ? 'leads only' : 'custom'}</strong>
                  </li>
                  <li>
                    <span>Participants</span>
                    <strong>{roomParticipantLabel}</strong>
                  </li>
                  <li>
                    <span>Selected agent</span>
                    <strong>{selectedAgent ? `@${selectedAgent.agent_id}` : 'none'}</strong>
                  </li>
                  <li>
                    <span>Direct target</span>
                    <strong>{directTargetLabel}</strong>
                  </li>
                  <li>
                    <span>WS</span>
                    <strong>{composerLabel}</strong>
                  </li>
                  <li>
                    <span>Last event</span>
                    <strong>{lastEventAt ? new Date(lastEventAt).toLocaleTimeString() : 'none'}</strong>
                  </li>
                </ul>
              </section>
              <section className="secondary-card concierge-side-card">
                <h3>Active roster</h3>
                <div className="concierge-roster-list">
                  {roomCandidateAgents.map((agent) => (
                    <div key={agent.agent_id} className="concierge-roster-row">
                      <div>
                        <strong>@{agent.agent_id}</strong>
                        <p>{agent.role} - {resolvedModelForAgent(agent)}</p>
                      </div>
                      <span className={`dot ${agent.chat_targetable ? 'green' : 'gray'}`}>
                        {agent.chat_targetable ? 'chat ready' : 'chat unavailable'}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
              <section className="secondary-card concierge-side-card">
                <h3>Internal trace</h3>
                <div className="events-log">
                  {visibleInternalConciergeMessages.map((message) => (
                    <p key={message.message_id}>
                      <strong>@{message.author}</strong> {message.text}
                    </p>
                  ))}
                  {visibleInternalConciergeMessages.length === 0 ? <p>No internal room traces yet.</p> : null}
                </div>
              </section>
            </div>
          </div>
        </section>
      )
    }

    if (activeTab === 'pilotage') {
      return (
        <section className="secondary-tab panel">
          <div className="secondary-header">
            <h2>Pilotage</h2>
            <span className="hint">live operations stream and execution health</span>
          </div>
          <div className="secondary-grid">
            <article>
              <h3>Operator messages</h3>
              <p>{directChatMessages.length}</p>
            </article>
            <article>
              <h3>Room messages</h3>
              <p>{conciergeChatMessages.length}</p>
            </article>
            <article>
              <h3>Approvals pending</h3>
              <p>{approvals.length}</p>
            </article>
            <article>
              <h3>Delivery mode</h3>
              <p>{composerLabel}</p>
            </article>
          </div>
          <div className="secondary-columns">
            <section className="secondary-card">
              <h3>OpenRouter</h3>
              <ul className="data-list">
                <li>
                  <span>Status</span>
                  <strong>{openRouterHealth?.status ?? 'unknown'}</strong>
                </li>
                <li>
                  <span>Base URL</span>
                  <strong>{openRouterHealth?.base_url || 'missing'}</strong>
                </li>
                <li>
                  <span>API key</span>
                  <strong>{openRouterHealth?.api_key_present ? 'present' : 'missing'}</strong>
                </li>
                <li>
                  <span>Last OK</span>
                  <strong>{openRouterHealth?.last_ok_at ? new Date(openRouterHealth.last_ok_at).toLocaleTimeString() : 'never'}</strong>
                </li>
                <li>
                  <span>Last error</span>
                  <strong>{openRouterHealth?.last_error || 'none'}</strong>
                </li>
                <li>
                  <span>Error kind</span>
                  <strong>{openRouterHealth?.last_error_kind || 'none'}</strong>
                </li>
                <li>
                  <span>HTTP status</span>
                  <strong>{openRouterHealth?.last_http_status ?? 'none'}</strong>
                </li>
                <li>
                  <span>Request ID</span>
                  <strong>{openRouterHealth?.last_request_id || 'none'}</strong>
                </li>
                <li>
                  <span>Body preview</span>
                  <strong>{openRouterHealth?.last_body_preview || 'none'}</strong>
                </li>
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Latest operator chat</h3>
              <div className="events-log">
                {latestDirect.length === 0 ? (
                  <p>No direct messages yet.</p>
                ) : (
                  latestDirect.map((message) => (
                    <p key={message.message_id}>
                      <strong>@{message.author}</strong> {message.text}
                    </p>
                  ))
                )}
              </div>
            </section>
            <section className="secondary-card">
              <h3>Latest internal + events</h3>
              <div className="events-log">
                {fallbackDiagnostics.slice(0, 6).map((diagnostic) => (
                  <p key={diagnostic.id}>
                    <strong>fallback</strong> [{diagnostic.chatMode}] {diagnostic.error} - {new Date(diagnostic.timestamp).toLocaleTimeString()}
                  </p>
                ))}
                {latestInternal.slice(0, 6).map((message) => (
                  <p key={message.message_id}>
                    <strong>@{message.author}</strong> [{message.visibility}] {message.text}
                  </p>
                ))}
                {latestEvents.slice(0, 10).map((event, index) => (
                  <p key={`${event.timestamp}-${index}`}>
                    <strong>{event.type}</strong> {new Date(event.timestamp).toLocaleTimeString()}
                  </p>
                ))}
                {fallbackDiagnostics.length === 0 && latestInternal.length === 0 && latestEvents.length === 0 ? <p>No diagnostics yet.</p> : null}
              </div>
            </section>
          </div>
        </section>
      )
    }

    if (activeTab === 'overview') {
      const buildStamp = backendHealth?.build_sha ? backendHealth.build_sha.slice(0, 12) : 'unknown'
      return (
        <section className="secondary-tab panel">
          <div className="secondary-header">
            <h2>Overview</h2>
            <span className="hint">project heartbeat, tasks, and runtime truth</span>
          </div>
          <div className="secondary-hero-grid">
            <article className="overview-hero-card">
              <span className="overview-hero-label">Runtime</span>
              <strong>{backendHealth?.status ?? 'unknown'}</strong>
              <p>ws {composerLabel} - build {buildStamp}</p>
            </article>
            <article className="overview-hero-card">
              <span className="overview-hero-label">Agents live</span>
              <strong>{agentsTotal}</strong>
              <p>{chatReadyCount} chat ready - {runningTerminals} terminals live</p>
            </article>
            <article className="overview-hero-card">
              <span className="overview-hero-label">Execution load</span>
              <strong>{taskCounts.todo + taskCounts.in_progress + taskCounts.blocked}</strong>
              <p>{approvals.length} approvals - queue {queueDepth}</p>
            </article>
            <article className="overview-hero-card">
              <span className="overview-hero-label">Credits this month</span>
              <strong>{monthlyCostLabel}</strong>
              <p>{costEventsLabel} cost events tracked</p>
            </article>
          </div>
          <div className="secondary-columns">
            <section className="secondary-card">
              <h3>Runtime quick status</h3>
              <ul className="data-list">
                {quickStatus.map((item) => (
                  <li key={item.label}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </li>
                ))}
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Build and environment</h3>
              <ul className="data-list">
                <li>
                  <span>Project</span>
                  <strong>{projectId}</strong>
                </li>
                <li>
                  <span>Approvals pending</span>
                  <strong>{approvals.length}</strong>
                </li>
                <li>
                  <span>API</span>
                  <strong>{getApiUrl()}</strong>
                </li>
                <li>
                  <span>Build time</span>
                  <strong>{backendHealth?.build_time ?? 'unknown'}</strong>
                </li>
                <li>
                  <span>Last event</span>
                  <strong>{lastEventAt ? new Date(lastEventAt).toLocaleTimeString() : 'none'}</strong>
                </li>
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Project summary</h3>
              <ul className="data-list">
                <li>
                  <span>Project</span>
                  <strong>{currentProjectLabel}</strong>
                </li>
                <li>
                  <span>Phase</span>
                  <strong>{projectPhase}</strong>
                </li>
                <li>
                  <span>Objective</span>
                  <strong>{projectObjective}</strong>
                </li>
                <li>
                  <span>Linked repo</span>
                  <strong>{linkedRepoLabel}</strong>
                </li>
                <li>
                  <span>Open tasks</span>
                  <strong>
                    {projectTaskCounts
                      ? projectTaskCounts.todo + projectTaskCounts.in_progress + projectTaskCounts.blocked
                      : taskCounts.todo + taskCounts.in_progress + taskCounts.blocked}
                  </strong>
                </li>
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Task board snapshot</h3>
              <ul className="data-list">
                {STATUS_ORDER.map((status) => (
                  <li key={status}>
                    <span>{STATUS_LABELS[status]}</span>
                  <strong>{projectTaskCounts ? projectTaskCounts[status] : taskCounts[status]}</strong>
                  </li>
                ))}
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Project actions</h3>
              <div className="events-log">
                <p>Project creation and takeover now live in Le Conseil.</p>
                <p>Use the pinned Project actions card there to create a greenfield project or run repo takeover.</p>
                <p>Overview stays read-only for runtime, costs, roadmap, and task visibility.</p>
              </div>
            </section>
            <section className="secondary-card">
              <h3>Operational focus</h3>
              <ul className="overview-focus-list">
                <li>
                  <span>Direct target</span>
                  <strong>{directTargetLabel}</strong>
                </li>
                <li>
                  <span>Selected agent</span>
                  <strong>{selectedAgent ? `@${selectedAgent.agent_id}` : 'none'}</strong>
                </li>
                <li>
                  <span>L1 leads</span>
                  <strong>{leadsCount}</strong>
                </li>
                <li>
                  <span>Assets loaded</span>
                  <strong>{assetsStatus.donarg && assetsStatus.pixelRef ? 'yes' : 'partial'}</strong>
                </li>
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Roadmap snapshot</h3>
              <div className="project-snapshot-grid">
                <div>
                  <h4>Now</h4>
                  <ul className="simple-list">
                    {(roadmapNow.length > 0 ? roadmapNow : ['No current roadmap items']).map((item) => (
                      <li key={`now-${item}`}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4>Next</h4>
                  <ul className="simple-list">
                    {(roadmapNext.length > 0 ? roadmapNext : ['No next roadmap items']).map((item) => (
                      <li key={`next-${item}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>
            <section className="secondary-card">
              <h3>Recent task movement</h3>
              <div className="events-log">
                {recentTasks.length === 0 ? (
                  <p>No tasks yet.</p>
                ) : (
                  recentTasks.map((task) => (
                    <p key={task.task_id}>
                      <strong>{task.title}</strong> - {STATUS_LABELS[task.status]} - @{task.owner}
                    </p>
                  ))
                )}
              </div>
            </section>
            <section className="secondary-card">
              <h3>Latest operator touch</h3>
              <div className="events-log">
                {latestRoom.length === 0 ? (
                  <p>No board messages yet.</p>
                ) : (
                  latestRoom.slice(0, 6).map((message) => (
                    <p key={message.message_id}>
                      <strong>@{message.author}</strong> {message.text}
                    </p>
                  ))
                )}
              </div>
            </section>
            <section className="secondary-card">
              <h3>Model spend</h3>
              <div className="events-log">
                {modelUsageSummary.length === 0 ? (
                  <p>No model usage tracked yet.</p>
                ) : (
                  modelUsageSummary.map((entry) => (
                    <p key={entry.model}>
                      <strong>{entry.model}</strong> - {formatCurrencyCad(entry.cost_cad)} - {entry.events} events
                    </p>
                  ))
                )}
              </div>
            </section>
          </div>
        </section>
      )
    }

    if (activeTab === 'todo') {
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

    if (activeTab === 'docs') {
      return (
        <section className="secondary-tab panel">
          <div className="secondary-header">
            <h2>Docs</h2>
            <span className="hint">runbook truth + local skills library</span>
          </div>
          <div className="docs-subnav">
                    <button
                      className={`docs-subnav-btn ${docsPanel === 'runbook' ? 'active' : ''}`}
                      type="button"
                      onClick={() => setDocsPanel('runbook')}
                    >
              Runbook
            </button>
                    <button
                      className={`docs-subnav-btn ${docsPanel === 'skills_library' ? 'active' : ''}`}
                      type="button"
                      onClick={() => setDocsPanel('skills_library')}
                    >
              Skills Library
            </button>
                    <button
                      className={`docs-subnav-btn ${docsPanel === 'project' ? 'active' : ''}`}
                      type="button"
                      onClick={() => setDocsPanel('project')}
                    >
              Project
            </button>
          </div>
          {docsPanel === 'runbook' ? (
            <>
              <div className="secondary-grid">
                <article>
                  <h3>Official app path</h3>
                  <p>/Applications/Cockpit.app</p>
                </article>
                <article>
                  <h3>Preflight contracts</h3>
                  <p>/healthz + /chat/approvals + /llm-profile</p>
                </article>
                <article>
                  <h3>Runtime mode</h3>
                  <p>{backendHealth?.app_mode ?? 'cockpit_local'}</p>
                </article>
                <article>
                  <h3>Daily command</h3>
                  <p>open "/Applications/Cockpit.app"</p>
                </article>
              </div>
              <div className="secondary-columns">
                <section className="secondary-card">
                  <h3>Operator checklist</h3>
                  <div className="events-log">
                    <p>1. Launch Cockpit.app</p>
                    <p>2. Check backend and WS badges</p>
                    <p>3. Verify approvals and llm-profile routes</p>
                    <p>4. Work from Pixel Home, To Do, Le Conseil, and Model Routing</p>
                  </div>
                </section>
                <section className="secondary-card">
                  <h3>Reference docs</h3>
                  <div className="events-log">
                    <p><strong>Runbook:</strong> docs/COCKPIT_RUNBOOK.md</p>
                    <p><strong>Protocol:</strong> docs/CLOUD_API_PROTOCOL.md</p>
                    <p><strong>Packaging:</strong> docs/PACKAGING.md</p>
                    <p><strong>Status:</strong> docs/STATUS_REPORT.md</p>
                  </div>
                </section>
              </div>
            </>
          ) : docsPanel === 'skills_library' ? (
            <div className="skills-library-layout">
              <section className="secondary-card">
                <h3>Installed local skills</h3>
                <p className="small-copy">
                  Read-only view from your local Codex skills folder plus project lock state when available.
                </p>
              </section>
              <div className="skills-library-grid">
                {skillsLibraryLoading ? (
                  <section className="secondary-card">
                    <p>Loading skills library...</p>
                  </section>
                ) : skillsLibrary.length === 0 ? (
                  <section className="secondary-card">
                    <p>No local skills were discovered for this project yet.</p>
                  </section>
                ) : (
                  skillsLibrary.map((skill) => (
                    <article key={skill.skill_id} className="secondary-card skill-library-card">
                      <div className="skill-library-head">
                        <div>
                          <h3>{skill.name}</h3>
                          <p className="skill-library-id">{skill.skill_id}</p>
                        </div>
                        <div className="skill-library-badges">
                          {skill.project_locked ? <span className="skill-chip project">project locked</span> : null}
                          {skill.assigned_agents.length > 0 ? <span className="skill-chip assigned">assigned</span> : <span className="skill-chip">local only</span>}
                        </div>
                      </div>
                      <p className="small-copy">{skill.description}</p>
                      <div className="events-log">
                        <p><strong>Source:</strong> {skill.source_path}</p>
                        <p><strong>Status:</strong> {skill.project_status ?? 'not locked'}</p>
                        <p>
                          <strong>Assigned agents:</strong>{' '}
                          {skill.assigned_agents.length > 0 ? skill.assigned_agents.map((agentId) => `@${agentId}`).join(', ') : 'none'}
                        </p>
                      </div>
                    </article>
                  ))
                )}
              </div>
            </div>
          ) : (
            <div className="project-docs-layout">
              <section className="secondary-card">
                <div className="section-title-row compact">
                  <h3>Projects</h3>
                  <span className="hint">{projectCatalogLoading ? 'loading...' : 'current live project only'}</span>
                </div>
                <div className="project-catalog-list">
                  {visibleProjectCards.map((project) => (
                    <button
                      key={project.project_id}
                      type="button"
                      className={`project-catalog-item ${selectedProjectCard.project_id === project.project_id ? 'active' : ''}`}
                      onClick={() => setSelectedProjectDocId(project.project_id)}
                    >
                      <strong>{projectLabel(project.project_id, project.project_name)}</strong>
                      <span>@{project.project_id}</span>
                      <p>{project.phase} - {project.objective}</p>
                    </button>
                  ))}
                </div>
              </section>
              <section className="secondary-card">
                <h3>Project summary</h3>
                <ul className="data-list">
                  <li>
                    <span>Project</span>
                    <strong>{projectLabel(selectedProjectCard.project_id, selectedProjectCard.project_name)}</strong>
                  </li>
                  <li>
                    <span>Linked repo</span>
                    <strong>{selectedProjectCard.linked_repo_path || linkedRepoLabel}</strong>
                  </li>
                  <li>
                    <span>Phase</span>
                    <strong>{selectedProjectCard.phase || projectPhase}</strong>
                  </li>
                  <li>
                    <span>Objective</span>
                    <strong>{selectedProjectCard.objective || projectObjective}</strong>
                  </li>
                  <li>
                    <span>Monthly cost</span>
                    <strong>{monthlyCostLabel}</strong>
                  </li>
                  <li>
                    <span>Cost events</span>
                    <strong>{costEventsLabel}</strong>
                  </li>
                </ul>
              </section>
              <div className="secondary-columns">
                <section className="secondary-card">
                  <h3>Roadmap now</h3>
                  <ul className="simple-list">
                    {(roadmapNow.length > 0 ? roadmapNow : ['No current roadmap items']).map((item) => (
                      <li key={`project-now-${item}`}>{item}</li>
                    ))}
                  </ul>
                </section>
                <section className="secondary-card">
                  <h3>Roadmap next</h3>
                  <ul className="simple-list">
                    {(roadmapNext.length > 0 ? roadmapNext : ['No next roadmap items']).map((item) => (
                      <li key={`project-next-${item}`}>{item}</li>
                    ))}
                  </ul>
                </section>
                <section className="secondary-card">
                  <h3>Latest decisions</h3>
                  <ul className="simple-list">
                    {(projectDecisions.length > 0 ? projectDecisions : ['No decision titles found']).map((item) => (
                      <li key={`decision-${item}`}>{item}</li>
                    ))}
                  </ul>
                </section>
                <section className="secondary-card">
                  <h3>Roadmap risks</h3>
                  <ul className="simple-list">
                    {(roadmapRisks.length > 0 ? roadmapRisks : ['No roadmap risks noted']).map((item) => (
                      <li key={`risk-${item}`}>{item}</li>
                    ))}
                  </ul>
                </section>
                <section className="secondary-card">
                  <h3>Model usage</h3>
                  <div className="events-log">
                    {modelUsageSummary.length === 0 ? (
                      <p>No model usage tracked yet.</p>
                    ) : (
                      modelUsageSummary.map((entry) => (
                        <p key={`project-usage-${entry.model}`}>
                          <strong>{entry.model}</strong> - {formatCurrencyCad(entry.cost_cad)} - {entry.events} events
                        </p>
                      ))
                    )}
                  </div>
                </section>
              </div>
            </div>
          )}
        </section>
      )
    }

    if (activeTab === 'model_routing' && profileDraft) {
      return (
        <section className="secondary-tab panel">
          <div className="secondary-header">
            <h2>Model Routing</h2>
            <span className="hint">role-based OpenRouter routing with project persistence</span>
          </div>
          <div className="routing-layout">
            <section className="secondary-card">
              <h3>Clems (L0)</h3>
              <div className="option-grid">
                {CLEMS_MODEL_OPTIONS.map((option) => (
                    <button
                      key={option.id}
                      className={`route-option ${profileDraft.clems_model === option.id ? 'active' : ''}`}
                      type="button"
                      onClick={() =>
                      setProfileDraft((previous) =>
                        previous ? { ...previous, clems_model: option.id, clems_catalog: CLEMS_MODEL_OPTIONS.map((item) => item.id) } : previous,
                      )
                    }
                  >
                    <strong>{option.label}</strong>
                    <span>{option.note}</span>
                  </button>
                ))}
              </div>
            </section>
            <section className="secondary-card">
              <h3>L1 models</h3>
              <div className="routing-agent-list">
                {l1Agents.map((agentId) => (
                  <label key={agentId} className="routing-agent-row">
                    <span>@{agentId}</span>
                    <select
                      value={profileDraft.l1_models[agentId] ?? 'moonshotai/kimi-k2.5'}
                      onChange={(event) =>
                        setProfileDraft((previous) =>
                          previous
                            ? {
                                ...previous,
                                l1_catalog: L1_MODEL_OPTIONS.map((item) => item.id),
                                l1_models: {
                                  ...previous.l1_models,
                                  [agentId]: event.target.value,
                                },
                              }
                            : previous,
                        )
                      }
                    >
                      {L1_MODEL_OPTIONS.map((option) => (
                        <option key={option.id} value={option.id}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
            </section>
            <section className="secondary-card">
              <h3>L2 surgical pool</h3>
              <label className="routing-primary">
                <span>Primary model</span>
                <select
                  value={profileDraft.l2_default_model}
                  onChange={(event) =>
                    setProfileDraft((previous) =>
                      previous
                        ? {
                            ...previous,
                            l2_default_model: event.target.value,
                            l2_pool: previous.l2_pool.includes(event.target.value)
                              ? previous.l2_pool
                              : [event.target.value, ...previous.l2_pool],
                          }
                        : previous,
                    )
                  }
                >
                  {L2_MODEL_OPTIONS.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <div className="routing-pool">
                {L2_MODEL_OPTIONS.map((option) => {
                  const active = profileDraft.l2_pool.includes(option.id)
                  return (
                    <button
                      key={option.id}
                      className={`route-option compact ${active ? 'active' : ''}`}
                      type="button"
                      onClick={() =>
                        setProfileDraft((previous) => {
                          if (!previous) {
                            return previous
                          }
                          const nextPool = active
                            ? previous.l2_pool.filter((item) => item !== option.id)
                            : [...previous.l2_pool, option.id]
                          const normalizedPool = nextPool.length === 0 ? [previous.l2_default_model] : nextPool
                          return {
                            ...previous,
                            l2_pool: normalizedPool,
                            l2_default_model: normalizedPool.includes(previous.l2_default_model)
                              ? previous.l2_default_model
                              : normalizedPool[0],
                          }
                        })
                      }
                    >
                      <strong>{option.label}</strong>
                      <span>{option.note}</span>
                    </button>
                  )
                })}
              </div>
              <ul className="data-list">
                <li>
                  <span>Selection mode</span>
                  <strong>{profileDraft.l2_selection_mode}</strong>
                </li>
                <li>
                  <span>Stream enabled</span>
                  <strong>{profileDraft.stream_enabled ? 'yes' : 'no'}</strong>
                </li>
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Voice STT</h3>
              <label className="routing-primary">
                <span>Voice transcription model</span>
                <select
                  value={profileDraft.voice_stt_model}
                  onChange={(event) =>
                    setProfileDraft((previous) =>
                      previous ? { ...previous, voice_stt_model: event.target.value } : previous,
                    )
                  }
                >
                  {[...VOICE_STT_OPTIONS, profileDraft.voice_stt_model]
                    .filter((value, index, values) => values.indexOf(value) === index)
                    .map((modelId) => (
                      <option key={modelId} value={modelId}>
                        {modelId}
                      </option>
                    ))}
                </select>
              </label>
              <p className="small-copy">
                Voice is OpenRouter-only. The desktop recorder sends audio to the local Rust backend, which transcribes with this model and injects text into the composer.
              </p>
            </section>
            <section className="secondary-card">
              <h3>Current profile</h3>
              <ul className="data-list">
                <li>
                  <span>Clems</span>
                  <strong>{modelLabel(profileDraft.clems_model)}</strong>
                </li>
                <li>
                  <span>Voice STT</span>
                  <strong>{profileDraft.voice_stt_model}</strong>
                </li>
                <li>
                  <span>L2 primary</span>
                  <strong>{modelLabel(profileDraft.l2_default_model)}</strong>
                </li>
                <li>
                  <span>Unavailable refs</span>
                  <strong>
                    {[profileDraft.clems_model, ...Object.values(profileDraft.l1_models), ...profileDraft.l2_pool].some(
                      (modelId) => isUnavailableModel(modelId),
                    )
                      ? 'review'
                      : 'none'}
                  </strong>
                </li>
                <li>
                  <span>Draft</span>
                  <strong>{profileDirty ? 'unsaved changes' : 'saved'}</strong>
                </li>
              </ul>
              <div className="todo-editor-actions">
                <button className="send-btn" onClick={() => void handleSaveLlmProfile()} disabled={isSavingProfile}>
                  {isSavingProfile ? 'Saving...' : 'Save model routing'}
                </button>
              </div>
            </section>
          </div>
        </section>
      )
    }

    return (
      <section className="secondary-tab panel">
        <div className="secondary-header">
          <h2>Diagnostics</h2>
          <span className="hint">fallback runtime snapshot</span>
        </div>
        <div className="secondary-grid">
          <article>
            <h3>Project</h3>
            <p>{projectId}</p>
          </article>
          <article>
            <h3>Agents</h3>
            <p>{feed?.agents.length ?? 0}</p>
          </article>
          <article>
            <h3>Pending approvals</h3>
            <p>{approvals.length}</p>
          </article>
          <article>
            <h3>Chat transport</h3>
            <p>{composerLabel}</p>
          </article>
        </div>
      </section>
    )
  }

  return (
    <div className={`app-shell ${activeTab === 'pixel_home' ? 'pixel-mode' : 'secondary-mode'}`}>
      <header className="app-header panel">
        <div>
          <p className="eyebrow">Cockpit official</p>
          <h1>Pixel Home</h1>
          <p className="header-subcopy">
            {clockNow.toLocaleDateString()} - local control tower for pixel operations, tasks, and model routing
          </p>
        </div>
        <div className="header-status">
          <div className="header-status-cluster header-status-project">
            <label className="project-input">
              Project
              <input
                value={projectLabel(projectId, projectSettings?.project_name ?? projectId)}
                readOnly
              />
            </label>
          </div>
          <div className="header-status-cluster">
            <div className={`status-pill ${backendHealth?.status === 'ok' ? 'ok' : 'warn'}`}>
              Backend {backendHealth?.status ?? 'unknown'}
            </div>
            <div className={`status-pill ${wsConnected ? 'ok' : 'warn'}`}>WS {composerLabel}</div>
            <div className={`status-pill ${openRouterPillTone}`}>{openRouterLabel}</div>
            <div className="status-pill neutral">API {getApiUrl()}</div>
            <div className="status-pill neutral">
              Build {(backendHealth?.build_sha ?? 'unknown').slice(0, 12)}
            </div>
          </div>
          <div className="header-status-cluster">
            <div className="status-pill neutral">Time {clockNow.toLocaleTimeString()}</div>
            <div className="status-pill neutral">
              Sync {lastSyncAt ? new Date(lastSyncAt).toLocaleTimeString() : 'none'}
            </div>
            <div className="status-pill neutral">
              Event {lastEventAt ? new Date(lastEventAt).toLocaleTimeString() : 'none'}
            </div>
          </div>
        </div>
      </header>

      <nav className="top-tabs panel">
        {topTabs.map((tab) => (
                    <button
                      key={tab.id}
                      className={`top-tab ${activeTab === tab.id ? 'active' : ''}`}
                      type="button"
                      onClick={() => setActiveTab(tab.id)}
                    >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="notice-stack">
        {apiError ? <div className="error-banner">{apiError}</div> : null}
        {uiNotice ? <div className="notice-banner">{uiNotice}</div> : null}
      </div>

      {activeTab !== 'pixel_home' ? (
        <div className="secondary-shell">
          {renderSecondaryTab()}
        </div>
      ) : (
        <main className="pixel-shell panel">
          <aside className="left-rail">
            <button
              className={`rail-btn ${workspaceTab === 'agent' && workbenchPanel === 'chat' && directTarget === 'clems' ? 'active' : ''}`}
              type="button"
              onClick={() => {
                setActiveTab('pixel_home')
                setWorkspaceTab('agent')
                setWorkbenchPanel('chat')
                setSelectedAgentId('clems')
                setDirectTarget('clems')
              }}
            >
              home
            </button>
            <button
              className={`rail-btn ${workspaceTab === 'agent' && !(workbenchPanel === 'chat' && directTarget === 'clems') ? 'active' : ''}`}
              type="button"
              onClick={() => {
                setActiveTab('pixel_home')
                setWorkspaceTab('agent')
                window.requestAnimationFrame(() => createAgentIdInputRef.current?.focus())
              }}
            >
              agents
            </button>
            <button
              className={`rail-btn ${workspaceTab === 'layout' ? 'active' : ''}`}
              type="button"
              onClick={() => {
                setActiveTab('pixel_home')
                setWorkspaceTab('layout')
              }}
            >
              layout
            </button>
            <button
              className={`rail-btn ${workbenchPanel === 'chat' ? 'active' : ''}`}
              type="button"
              onClick={() => {
                setActiveTab('pixel_home')
                setWorkbenchPanel('chat')
                if (selectedAgentId && selectedAgentId !== 'clems' && selectedAgentChatReady) {
                  setDirectTarget('selected_agent')
                } else {
                  setDirectTarget('clems')
                }
              }}
            >
              chat
            </button>
            <button
              className={`rail-btn ${workbenchPanel === 'terminal' ? 'active' : ''}`}
              type="button"
              onClick={() => {
                setActiveTab('pixel_home')
                setWorkbenchPanel('terminal')
              }}
            >
              term
            </button>
            <div className="rail-stats">
              <p>L0 {feed?.l0_count ?? 0}</p>
              <p>L1 {feed?.l1_count ?? 0}</p>
              <p>L2 {feed?.l2_count ?? 0}</p>
            </div>
          </aside>

          <section className="pixel-content">
            <div className={`pixel-grid ${workbenchCollapsed ? 'workbench-collapsed' : ''}`}>
              <aside className="workspace-left">{renderWorkspaceLeftPanel()}</aside>

              <section className="center-stage">
                <div className="stage-head">
                  <div>
                    <h2>Pixel Office</h2>
                    <p>Video-style shell with live scene and dedicated terminals</p>
                  </div>
                  <div className="zoom-controls">
                    <button
                      type="button"
                      aria-label={workbenchCollapsed ? 'Open workbench' : 'Collapse workbench'}
                      onClick={() => setWorkbenchCollapsed(!workbenchCollapsed)}
                    >
                      {workbenchCollapsed ? 'workbench' : 'collapse'}
                    </button>
                    <button
                      type="button"
                      aria-label="Zoom out office scene"
                      onClick={() => setZoom((value) => Math.max(0.5, Number((value - 0.2).toFixed(2))))}
                    >
                      -
                    </button>
                    <span>{zoom.toFixed(1)}x</span>
                    <button
                      type="button"
                      aria-label="Zoom in office scene"
                      onClick={() => setZoom((value) => Math.min(4, Number((value + 0.2).toFixed(2))))}
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className="canvas-frame" ref={containerRef}>
                  <OfficeCanvas
                    officeState={officeState}
                    onClick={handleOfficeClick}
                    isEditMode={false}
                    editorState={editorState}
                    onEditorTileAction={() => {}}
                    onEditorEraseAction={() => {}}
                    onEditorSelectionChange={() => {}}
                    onDeleteSelected={() => {}}
                    onRotateSelected={() => {}}
                    onDragMove={() => {}}
                    editorTick={refreshTick}
                    zoom={zoom}
                    onZoomChange={setZoom}
                    panRef={panRef}
                  />
                  <ToolOverlay
                    officeState={officeState}
                    agents={agentNumericIds}
                    agentTools={agentTools}
                    subagentCharacters={[]}
                    viewportWidth={overlayViewport.viewportWidth}
                    viewportHeight={overlayViewport.viewportHeight}
                    panX={overlayViewport.panX}
                    panY={overlayViewport.panY}
                    dpr={overlayViewport.dpr}
                    zoom={zoom}
                    onCloseAgent={handleOfficeClose}
                  />
                </div>
              </section>

              <aside className={`workbench ${workbenchCollapsed ? 'collapsed' : ''}`}>
                {workbenchCollapsed ? (
                  <div className="workbench-collapsed-body">
                    <button className="small-btn" onClick={() => setWorkbenchCollapsed(false)}>
                      Open workbench
                    </button>
                    <p className="hint">chat + terminal hidden</p>
                  </div>
                ) : (
                  <div className="workbench-shell">
                    <div className="workbench-topbar">
                      <div className="workbench-tabs">
                        {workbenchTabs.map((tab) => (
                          <button
                            key={tab.id}
                            className={`workbench-tab-btn ${workbenchPanel === tab.id ? 'active' : ''}`}
                            type="button"
                            onClick={() => setWorkbenchPanel(tab.id)}
                          >
                            <span>{tab.label}</span>
                            {tab.count ? <span className="workbench-tab-count">{tab.count}</span> : null}
                          </button>
                        ))}
                      </div>
                      {workbenchPanel !== 'chat' ? (
                        <div className="workbench-summary">
                          <span className="chat-target">Target {directTargetLabel}</span>
                          <span className={`chat-status ${composerStatus}`}>{composerLabel}</span>
                          <span className="workbench-mini-pill">
                            terminal {selectedAgent?.terminal_state === 'running' ? 'live' : selectedAgentId ? 'offline' : 'none'}
                          </span>
                        </div>
                      ) : null}
                    </div>

                    {workbenchPanel === 'chat' ? (
                      <section className="chat-section">
                        <div className="chat-head-block">
                          <div className="section-title-row">
                            <div className="chat-title-block">
                              <h2>Direct with {directTargetBadge}</h2>
                              <p className="small-copy">One target only. Use Le Conseil for room orchestration.</p>
                            </div>
                            <div className="chat-actions">
                              <span className={`chat-status ${composerStatus}`}>{composerLabel}</span>
                              <span className="chat-target">{directTargetLabel}</span>
                              <button className="small-btn" onClick={() => void handleResetChat()}>
                                Reset chat
                              </button>
                            </div>
                          </div>
                          <div className="chat-toolbar-card">
                            <div className="chat-toolbar-row">
                              <div className="direct-chat-toolbar-group">
                                <span className="mode-pill active">Direct</span>
                                <span className="mode-pill">{directTargetBadge}</span>
                              </div>
                              <div className="chat-actions">
                                {directChatMessages.length > 8 ? (
                                  <>
                                    <span className="hint">latest {Math.min(directVisibleCount, directChatMessages.length || directVisibleCount)}</span>
                                    <button
                                      className="small-btn"
                                      onClick={() => setDirectVisibleCount((value) => Math.min(directChatMessages.length, value + 12))}
                                      disabled={directVisibleCount >= directChatMessages.length}
                                    >
                                      Older
                                    </button>
                                    <button
                                      className="small-btn"
                                      onClick={() => setDirectVisibleCount(8)}
                                      disabled={directVisibleCount <= 8}
                                    >
                                      Latest
                                    </button>
                                  </>
                                ) : null}
                              </div>
                            </div>
                            <div className="chat-toolbar-row">
                              <div className="direct-chat-toolbar-group">
                                <button
                                  className={`target-btn ${directTarget === 'clems' ? 'active' : ''}`}
                                  onClick={() => setDirectTarget('clems')}
                                >
                                  Clems
                                </button>
                                <button
                                  className={`target-btn ${directTarget === 'selected_agent' ? 'active' : ''}`}
                                  onClick={() => setDirectTarget('selected_agent')}
                                  disabled={!selectedAgentChatReady}
                                >
                                  Selected agent
                                </button>
                              </div>
                              {selectedAgent ? (
                                <span className="chat-target-detail compact toolbar-note">
                                  @{selectedAgent.agent_id} - {selectedAgent.scene_present ? 'on scene' : 'off scene'} - {selectedAgent.current_task || 'no active task'}
                                </span>
                              ) : null}
                            </div>
                            {directTargetNotice ? <p className="chat-target-detail compact direct-chat-notice">{directTargetNotice}</p> : null}
                          </div>
                        </div>

                          <div
                            ref={directChatLogRef}
                            className="chat-log"
                            tabIndex={0}
                            aria-label="Direct chat transcript"
                            onScroll={(event) => {
                            const node = event.currentTarget
                            directStickToBottomRef.current = node.scrollHeight - node.scrollTop - node.clientHeight < 40
                          }}
                        >
                          {visibleDirectMessages.length === 0 ? (
                            <p className="chat-empty">No chat yet. Send a first message to start live flow.</p>
                          ) : (
                            visibleDirectMessages.map((message) => (
                              <article
                                key={message.message_id}
                                className={`chat-row ${message.author === 'operator' ? 'operator' : message.author === 'clems' ? 'clems' : 'agent'}`}
                              >
                                <header>
                                  <div className="chat-row-meta">
                                    <strong className="chat-author">@{message.author}</strong>
                                    {messageKindLabel(message) ? <span className="chat-kind">{messageKindLabel(message)}</span> : null}
                                  </div>
                                  <time className="chat-time">{new Date(message.timestamp).toLocaleTimeString()}</time>
                                </header>
                                <p className="chat-body">{message.text}</p>
                              </article>
                            ))
                          )}
                          {directSendPhase ? (
                            <article className="chat-row pending">
                              <header>
                                <div className="chat-row-meta">
                                  <strong className="chat-author">{directTargetLabel}</strong>
                                  <span className="chat-kind">
                                    {directSendPhase === 'degraded'
                                      ? 'degraded'
                                      : directSendPhase === 'retrying'
                                        ? 'retrying'
                                        : 'thinking'}
                                  </span>
                                </div>
                                <time className="chat-time">live</time>
                              </header>
                              <p className="chat-body">
                                {directSendPhase === 'degraded'
                                  ? 'OpenRouter degraded. Direct reply unavailable. Retry or switch to Le Conseil.'
                                  : directSendPhase === 'retrying'
                                    ? `${directTargetLabel} is retrying OpenRouter...`
                                    : `${directTargetLabel} is thinking...`}
                              </p>
                            </article>
                          ) : null}
                        </div>
                        <div className="composer-stack direct-composer-stack">
                          <div className="composer-row composer-row-inline">
                            <input
                              value={directChatInput}
                              aria-label="Direct chat message"
                              onChange={(event) => setDirectChatInput(event.target.value)}
                              onKeyDown={(event) => {
                                if (event.key === 'Enter') {
                                  event.preventDefault()
                                  void handleSendChat()
                                }
                              }}
                              placeholder={
                                directTarget === 'selected_agent'
                                  ? selectedAgentChatReady
                                    ? `Send to @${selectedAgent?.agent_id}`
                                    : 'Select a chat-ready agent or switch back to Clems.'
                                  : 'Talk to @clems directly.'
                              }
                            />
                            <button
                              className={`small-btn voice-btn ${isRecordingVoice ? 'recording' : ''}`}
                              type="button"
                              aria-label={isRecordingVoice ? 'Stop direct voice recording' : 'Start direct voice recording'}
                              onClick={() => void handleToggleVoiceRecording()}
                              disabled={isTranscribingVoice}
                            >
                              {isTranscribingVoice ? 'Transcribing...' : isRecordingVoice ? 'Stop voice' : 'Voice'}
                            </button>
                            <button
                              className="send-btn"
                              type="button"
                              onClick={() => void handleSendChat({ targetMode: directTarget, chatMode: 'direct' })}
                              disabled={isSendingChat}
                            >
                              {isSendingChat
                                ? 'Sending...'
                                : directTarget === 'selected_agent' && selectedAgentChatReady
                                  ? `Send to @${selectedAgent?.agent_id}`
                                  : 'Send to @clems'}
                            </button>
                          </div>
                        </div>
                      </section>
                    ) : null}

                    {workbenchPanel === 'terminal' ? (
                      <section className="terminal-section">
                        <div className="section-title-row">
                          <h2>Terminal</h2>
                          <div className="chat-actions">
                            <span className="hint">{selectedAgentId ? `@${selectedAgentId}` : 'no agent selected'}</span>
                            {selectedAgentId && selectedAgent?.terminal_state !== 'running' ? (
                              <button className="small-btn" onClick={() => void ensureAgentTerminal(selectedAgentId)}>
                                Open terminal
                              </button>
                            ) : null}
                          </div>
                        </div>
                        {selectedAgentId ? (
                          <div className="terminal-external-layout">
                            <div className="terminal-summary-card">
                              <div>
                                <strong>@{selectedAgentId}</strong>
                                <p className="small-copy">
                                  Terminal state: {selectedAgent?.terminal_state === 'running' ? 'live' : 'offline'}
                                </p>
                                <p className="small-copy">
                                  Use the OS terminal when you need manual command entry. Pixel Home stays focused on visibility and chat.
                                </p>
                              </div>
                              <div className="terminal-summary-actions">
                                {selectedAgent?.terminal_state !== 'running' ? (
                                  <button onClick={() => void ensureAgentTerminal(selectedAgentId)}>Start terminal</button>
                                ) : null}
                                <button onClick={() => void handleRestartTerminal()}>Restart</button>
                                <button onClick={() => void handleOpenExternalTerminal()}>Open OS terminal</button>
                              </div>
                            </div>
                            <div className="empty-panel">
                              <h3>External terminal only</h3>
                              <p>
                                Commands are no longer typed inside Cockpit. Select an agent, then open its OS terminal to inspect or drive the session directly.
                              </p>
                            </div>
                          </div>
                        ) : (
                          <div className="empty-panel">
                            <h3>No terminal target selected</h3>
                            <p>Select an agent from the left roster, then open or restart its terminal from here.</p>
                          </div>
                        )}
                      </section>
                    ) : null}

                    {workbenchPanel === 'approvals' ? (
                      <section className="approvals-section">
                        <div className="section-title-row">
                          <h2>Approvals</h2>
                          <span className="hint">pending: {approvals.length}</span>
                        </div>
                        <div className="approvals-log" tabIndex={0} aria-label="Pending approvals log">
                          {approvals.length === 0 ? (
                            <div className="empty-panel compact">
                              <h3>No pending approvals</h3>
                              <p>Requests from L1 and L2 will land here when an operator decision is required.</p>
                            </div>
                          ) : (
                            approvals.map((approval) => (
                              <article key={approval.request_id} className="approval-row">
                                <p>
                                  <strong>{approval.requester}</strong> asks L2 on <strong>{approval.section_tag}</strong>
                                </p>
                                <p className="approval-reason">{approval.reason}</p>
                                <div className="approval-actions">
                                  <button
                                    disabled={approvalBusy[approval.request_id] === true}
                                    onClick={() => {
                                      void handleApproval(approval.request_id, 'approve')
                                    }}
                                  >
                                    Approve
                                  </button>
                                  <button
                                    disabled={approvalBusy[approval.request_id] === true}
                                    onClick={() => {
                                      void handleApproval(approval.request_id, 'reject')
                                    }}
                                  >
                                    Reject
                                  </button>
                                </div>
                              </article>
                            ))
                          )}
                        </div>
                      </section>
                    ) : null}

                    {workbenchPanel === 'events' ? (
                      <section className="events-section">
                        <div className="section-title-row">
                          <h2>Recent Events</h2>
                          <span className="hint">{eventLog.length} tracked</span>
                        </div>
                        <div className="events-log" tabIndex={0} aria-label="Recent events log">
                          {eventLog.length === 0 ? (
                            <div className="empty-panel compact">
                              <h3>No events yet</h3>
                              <p>Runtime events will appear here once the workspace starts receiving traffic.</p>
                            </div>
                          ) : (
                            eventLog.map((event, index) => (
                              <p key={`${event.timestamp}-${index}`}>
                                <strong>{event.type}</strong> {new Date(event.timestamp).toLocaleTimeString()}
                              </p>
                            ))
                          )}
                        </div>
                      </section>
                    ) : null}
                  </div>
                )}
              </aside>
            </div>

            <footer className="workspace-tabs">
              {workspaceTabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`workspace-tab ${workspaceTab === tab.id ? 'active' : ''}`}
                  onClick={() => {
                    setWorkspaceTab(tab.id)
                    if (tab.id === 'agent') {
                      window.requestAnimationFrame(() => createAgentIdInputRef.current?.focus())
                    }
                  }}
                >
                  {tab.label}
                </button>
              ))}

              <div className="runtime-health">
                <span>terminals {feed?.terminals_alive ?? 0}</span>
                <span>queue {feed?.queue_depth ?? 0}</span>
                <span>ws {wsConnected ? 'up' : 'down'}</span>
              </div>
            </footer>
          </section>
        </main>
      )}
    </div>
  )
}

export default App
