import { useCallback, useEffect, useMemo, useRef } from 'react'
import './App.css'
import { EditorState } from './office/editor/editorState.js'
import { OfficeState } from './office/engine/officeState.js'
import {
  approveApproval,
  putLayout,
  rejectApproval,
  openTerminal,
} from './lib/cockpitClient'
import type {
  TaskRecord,
  TaskStatus,
} from './lib/cockpitClient'
import {
  modelLabel,
  emptyTaskEditor,
  compareTasksByFreshness,
  projectLabel,
} from './lib/formatters.js'
import { STATUS_ORDER } from './lib/appConstants.js'
import {
  useCockpitStore,
  useDirectChatMessages,
  useConciergeChatMessages,
  useInternalConciergeMessages,
} from './store/index.js'
import type { RosterAgentView } from './types.js'

import { usePolling } from './hooks/usePolling.js'
import { useDataSync } from './hooks/useDataSync.js'
import { useWebSocket } from './hooks/useWebSocket.js'
import { useAgentActions } from './hooks/useAgentActions.js'
import { useChatActions } from './hooks/useChatActions.js'
import { useTaskActions } from './hooks/useTaskActions.js'
import { useProjectActions } from './hooks/useProjectActions.js'

import { PixelHomeTab } from './tabs/PixelHomeTab.js'
import { ConciergeRoomTab } from './tabs/ConciergeRoomTab.js'
import { OverviewTab } from './tabs/OverviewTab.js'
import { PilotageTab } from './tabs/PilotageTab.js'
import { DocsTab } from './tabs/DocsTab.js'
import { TodoTab } from './tabs/TodoTab.js'
import { ModelRoutingTab } from './tabs/ModelRoutingTab.js'


function App() {
  const projectId = useCockpitStore((s) => s.projectId)
  const loading = useCockpitStore((s) => s.loading)
  const apiError = useCockpitStore((s) => s.apiError)
  const feed = useCockpitStore((s) => s.feed)
  const agentRecords = useCockpitStore((s) => s.agentRecords)
  const selectedAgentId = useCockpitStore((s) => s.selectedAgentId)
  const directTarget = useCockpitStore((s) => s.directTarget)
  const activeTab = useCockpitStore((s) => s.activeTab)
  const composerStatus = useCockpitStore((s) => s.composerStatus)
  const wsConnected = useCockpitStore((s) => s.wsConnected)
  const eventLog = useCockpitStore((s) => s.eventLog)
  const tasks = useCockpitStore((s) => s.tasks)
  const selectedTaskId = useCockpitStore((s) => s.selectedTaskId)
  const profileDraft = useCockpitStore((s) => s.profileDraft)
  const roomVisibleCount = useCockpitStore((s) => s.roomVisibleCount)
  const roomParticipantMode = useCockpitStore((s) => s.roomParticipantMode)
  const roomCustomParticipants = useCockpitStore((s) => s.roomCustomParticipants)
  const projectSettings = useCockpitStore((s) => s.projectSettings)
  const projectSummary = useCockpitStore((s) => s.projectSummary)
  const projectCatalog = useCockpitStore((s) => s.projectCatalog)
  const selectedProjectDocId = useCockpitStore((s) => s.selectedProjectDocId)
  const linkedRepoDraft = useCockpitStore((s) => s.linkedRepoDraft)
  const projectActionMode = useCockpitStore((s) => s.projectActionMode)
  const newProjectIdDraft = useCockpitStore((s) => s.newProjectIdDraft)
  const newProjectNameDraft = useCockpitStore((s) => s.newProjectNameDraft)
  const newProjectRepoDraft = useCockpitStore((s) => s.newProjectRepoDraft)
  const takeoverResult = useCockpitStore((s) => s.takeoverResult)
  const isRunningTakeover = useCockpitStore((s) => s.isRunningTakeover)
  const isApplyingTakeover = useCockpitStore((s) => s.isApplyingTakeover)
  const isChoosingFolder = useCockpitStore((s) => s.isChoosingFolder)
  const isCreatingProject = useCockpitStore((s) => s.isCreatingProject)
  const isSendingChat = useCockpitStore((s) => s.isSendingChat)
  const isRecordingVoice = useCockpitStore((s) => s.isRecordingVoice)
  const isTranscribingVoice = useCockpitStore((s) => s.isTranscribingVoice)
  const fallbackDiagnostics = useCockpitStore((s) => s.fallbackDiagnostics)
  const backendHealth = useCockpitStore((s) => s.backendHealth)
  const executionMode = useCockpitStore((s) => s.executionMode)
  const showRoomAddMenu = useCockpitStore((s) => s.showRoomAddMenu)
  const roomChatInput = useCockpitStore((s) => s.roomChatInput)
  const lastEventAt = useCockpitStore((s) => s.lastEventAt)

  const setApiError = useCockpitStore((s) => s.setApiError)
  const setActiveTab = useCockpitStore((s) => s.setActiveTab)
  const setSelectedAgentId = useCockpitStore((s) => s.setSelectedAgentId)
  const setDirectTarget = useCockpitStore((s) => s.setDirectTarget)
  const setApprovalBusy = useCockpitStore((s) => s.setApprovalBusy)
  const setUiNotice = useCockpitStore((s) => s.setUiNotice)
  const setRefreshTick = useCockpitStore((s) => s.setRefreshTick)
  const setSelectedProjectDocId = useCockpitStore((s) => s.setSelectedProjectDocId)
  const setRoomCustomParticipants = useCockpitStore((s) => s.setRoomCustomParticipants)
  const setTaskEditor = useCockpitStore((s) => s.setTaskEditor)
  const setDirectChatInput = useCockpitStore((s) => s.setDirectChatInput)
  const setRoomChatInput = useCockpitStore((s) => s.setRoomChatInput)
  const setShowRoomAddMenu = useCockpitStore((s) => s.setShowRoomAddMenu)
  const setExecutionMode = useCockpitStore((s) => s.setExecutionMode)
  const setRoomVisibleCount = useCockpitStore((s) => s.setRoomVisibleCount)
  const setRoomParticipantMode = useCockpitStore((s) => s.setRoomParticipantMode)
  const setProjectActionMode = useCockpitStore((s) => s.setProjectActionMode)
  const setNewProjectIdDraft = useCockpitStore((s) => s.setNewProjectIdDraft)
  const setNewProjectNameDraft = useCockpitStore((s) => s.setNewProjectNameDraft)
  const setNewProjectRepoDraft = useCockpitStore((s) => s.setNewProjectRepoDraft)
  const setLinkedRepoDraft = useCockpitStore((s) => s.setLinkedRepoDraft)
  const setSelectedTaskId = useCockpitStore((s) => s.setSelectedTaskId)

  const directChatMessages = useDirectChatMessages()
  const conciergeChatMessages = useConciergeChatMessages()
  const internalConciergeMessages = useInternalConciergeMessages()

  // ── Stable refs ───────────────────────────────────────────────────
  const officeState = useMemo(() => new OfficeState(), [])
  const editorState = useMemo(() => new EditorState(), [])
  const panRef = useRef({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)
  const createAgentIdInputRef = useRef<HTMLInputElement>(null)

  const idToNumericRef = useRef(new Map<string, number>())
  const numericToIdRef = useRef(new Map<number, string>())
  const nextNumericRef = useRef(1)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const roomStickToBottomRef = useRef(true)

  // ── Utility functions ─────────────────────────────────────────────
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
    [projectId, setApiError, setSelectedAgentId],
  )

  // ── Hooks ─────────────────────────────────────────────────────────
  const {
    refreshApprovals,
    refreshPixelFeed,
    refreshAgentWorkspace,
    refreshProjectSettings,
    refreshProjectSummary,
    refreshRoadmap,
    refreshTasks,
    bootstrap,
  } = useDataSync({
    officeState,
    toNumericId,
    styleForAgent,
    idToNumericRef,
    numericToIdRef,
  })

  const { wsConnectedRef, startFallbackPolling } = useWebSocket({
    refreshApprovals,
    refreshPixelFeed,
    refreshAgentWorkspace,
    refreshProjectSummary,
    refreshTasks,
  })

  usePolling({
    containerRef,
    panRef,
    mediaRecorderRef,
    mediaStreamRef,
  })

  const {
    handleSelectAgent,
    handleCreateAgent,
    handleDeleteAgent,
    handleOfficeClick,
    handleOfficeClose,
    handleQuickAgent,
  } = useAgentActions({
    refreshAgentWorkspace,
    ensureAgentTerminal,
    numericToIdRef,
  })

  const { handleCreateTask, handleSaveTask, handleTaskStatusMove } = useTaskActions({
    refreshProjectSummary,
  })

  const {
    handleRunTakeover,
    handleApplyTakeoverTasks,
    handleApplyTakeoverRoadmap,
    handleLaunchTakeoverPlan,
    handleSaveLlmProfile,
    handleSaveProjectLink,
    handleChooseRepoFolder,
    handleCreateProject,
  } = useProjectActions({
    refreshApprovals,
    refreshProjectSettings,
    refreshProjectSummary,
    refreshRoadmap,
    refreshTasks,
    roomStickToBottomRef,
  })

  // ── Computed values ───────────────────────────────────────────────
  const selectedTask = useMemo(
    () => tasks.find((task) => task.task_id === selectedTaskId) ?? null,
    [selectedTaskId, tasks],
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
        const preferredOrder = ['clems', 'victor', 'leo', 'nova', 'vulgarisation']
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

  // ── Chat hook (placed after computed values it depends on) ──────
  const {
    handleSendChat,
    handleResetChat,
    handleToggleVoiceRecording,
    directChatLogRef,
    roomChatLogRef,
    directStickToBottomRef,
  } = useChatActions({
    refreshApprovals,
    startFallbackPolling,
    wsConnectedRef,
    selectedAgent,
    roomDispatchContext,
    visibleDirectMessages: directChatMessages,
    visibleConciergeMessages,
    externalMediaRecorderRef: mediaRecorderRef,
    externalMediaStreamRef: mediaStreamRef,
    externalRoomStickToBottomRef: roomStickToBottomRef,
  })

  const agentNumericIds = useMemo(() => {
    if (rosterAgents.length === 0) {
      return []
    }
    return rosterAgents.map((agent) => toNumericId(agent.agent_id))
  }, [rosterAgents, toNumericId])

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

  const composerLabel =
    composerStatus === 'live'
      ? 'Live'
      : composerStatus === 'http_fallback'
        ? 'HTTP fallback'
        : 'Reconnecting'

  const agentsTotal = feed?.agents.length ?? 0
  const chatReadyCount = rosterAgents.filter((agent) => agent.chat_targetable).length
  const taskCounts = STATUS_ORDER.reduce<Record<TaskStatus, number>>(
    (accumulator, status) => ({
      ...accumulator,
      [status]: tasks.filter((task) => task.status === status).length,
    }),
    { todo: 0, in_progress: 0, blocked: 0, done: 0 },
  )

  const currentProjectLabel = projectLabel(projectId, projectSettings?.project_name ?? projectId)
  const linkedRepoLabel = projectSummary?.linked_repo_path ?? projectSettings?.linked_repo_path ?? 'not linked'

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

  // ── Non-hook callbacks ────────────────────────────────────────────
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
    [projectId, refreshApprovals, setApiError, setApprovalBusy],
  )

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
  }, [officeState, projectId, refreshPixelFeed, setApiError, setRefreshTick, setUiNotice])

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
  }, [setDirectChatInput, setRoomChatInput, setShowRoomAddMenu])

  // ── Side-effect: sync task editor when selectedTask changes ───────
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
  }, [selectedTask, setTaskEditor])

  // ── Side-effect: cockpit-office-message listener ──────────────────
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

  // ── Side-effect: fallback agent selection when selected disappears ─
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
  }, [rosterAgents, selectedAgentId, setDirectTarget, setSelectedAgentId])

  // ── Side-effect: fallback direct target when agent not chat-ready ─
  useEffect(() => {
    if (directTarget === 'selected_agent' && !selectedAgentChatReady) {
      setDirectTarget('clems')
    }
  }, [directTarget, selectedAgentChatReady, setDirectTarget])

  // ── Side-effect: keep selectedProjectDocId in sync with catalog ────
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
  }, [projectCatalog, projectId, selectedProjectDocId, setSelectedProjectDocId])

  // ── Side-effect: prune roomCustomParticipants to valid agents ──────
  useEffect(() => {
    const valid = new Set(roomCandidateAgents.map((agent) => agent.agent_id))
    setRoomCustomParticipants((previous) => {
      const filtered = previous.filter((agentId) => valid.has(agentId))
      if (filtered.length > 0) {
        return filtered
      }
      return valid.has('clems') ? ['clems'] : filtered
    })
  }, [roomCandidateAgents, setRoomCustomParticipants])

  // ── Loading screen ────────────────────────────────────────────────
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

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-left">
          <h1>Cockpit</h1>
          <span className="project-badge">{projectId}</span>
        </div>
        <nav className="top-tabs">
          {topTabs.map((tab) => (
            <button
              key={tab.id}
              className={`top-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
              {tab.id === 'concierge_room' && conciergeChatMessages.length > 0 ? (
                <span className="tab-badge">{conciergeChatMessages.length}</span>
              ) : null}
              {tab.id === 'todo' ? (
                <span className="tab-badge">
                  {taskCounts.todo + taskCounts.in_progress + taskCounts.blocked}
                </span>
              ) : null}
            </button>
          ))}
        </nav>
        <div className="header-right">
          <span className={`status-pill ${wsConnected ? 'ok' : 'warn'}`}>{composerLabel}</span>
          {apiError ? <span className="status-pill warn" title={apiError}>Error</span> : null}
        </div>
      </header>

      {activeTab === 'pixel_home' ? (
        <PixelHomeTab
          officeState={officeState}
          editorState={editorState}
          containerRef={containerRef}
          panRef={panRef}
          createAgentIdInputRef={createAgentIdInputRef}
          directChatLogRef={directChatLogRef}
          directStickToBottomRef={directStickToBottomRef}
          rosterAgents={rosterAgents}
          selectedAgent={selectedAgent}
          selectedAgentChatReady={selectedAgentChatReady}
          activeTasksByOwner={activeTasksByOwner}
          resolvedModelForAgent={resolvedModelForAgent}
          agentNumericIds={agentNumericIds}
          directTargetLabel={directTargetLabel}
          directTargetBadge={directTargetBadge}
          directTargetNotice={directTargetNotice}
          composerLabel={composerLabel}
          handleSelectAgent={handleSelectAgent}
          handleCreateAgent={handleCreateAgent}
          handleDeleteAgent={handleDeleteAgent}
          handleQuickAgent={handleQuickAgent}
          handleOfficeClick={handleOfficeClick}
          handleOfficeClose={handleOfficeClose}
          handleSendChat={handleSendChat}
          handleResetChat={handleResetChat}
          handleToggleVoiceRecording={handleToggleVoiceRecording}
          handleApproval={handleApproval}
          handleApplyVideoPreset={handleApplyVideoPreset}
          bootstrap={bootstrap}
          refreshPixelFeed={refreshPixelFeed}
        />
      ) : activeTab === 'concierge_room' ? (
        <ConciergeRoomTab
          composerStatus={composerStatus}
          composerLabel={composerLabel}
          roomChatInput={roomChatInput}
          executionMode={executionMode}
          showRoomAddMenu={showRoomAddMenu}
          roomVisibleCount={roomVisibleCount}
          roomParticipantMode={roomParticipantMode}
          roomCustomParticipants={roomCustomParticipants}
          roomCandidateAgents={roomCandidateAgents}
          effectiveRoomParticipantIds={effectiveRoomParticipantIds}
          roomParticipantLabel={roomParticipantLabel}
          roomDispatchContext={roomDispatchContext}
          agentsTotal={agentsTotal}
          chatReadyCount={chatReadyCount}
          taskCounts={taskCounts}
          selectedAgent={selectedAgent}
          directTargetLabel={directTargetLabel}
          lastEventAt={lastEventAt}
          currentProjectLabel={currentProjectLabel}
          linkedRepoLabel={linkedRepoLabel}
          projectActionMode={projectActionMode}
          newProjectIdDraft={newProjectIdDraft}
          newProjectNameDraft={newProjectNameDraft}
          newProjectRepoDraft={newProjectRepoDraft}
          linkedRepoDraft={linkedRepoDraft}
          isChoosingFolder={isChoosingFolder}
          isCreatingProject={isCreatingProject}
          isRunningTakeover={isRunningTakeover}
          isApplyingTakeover={isApplyingTakeover}
          isSendingChat={isSendingChat}
          isRecordingVoice={isRecordingVoice}
          isTranscribingVoice={isTranscribingVoice}
          takeoverResult={takeoverResult}
          profileDraft={profileDraft}
          visibleConciergeMessages={visibleConciergeMessages}
          visibleInternalConciergeMessages={visibleInternalConciergeMessages}
          roomChatLogRef={roomChatLogRef}
          roomStickToBottomRef={roomStickToBottomRef}
          resolvedModelForAgent={resolvedModelForAgent}
          setRoomChatInput={setRoomChatInput}
          setExecutionMode={setExecutionMode}
          setShowRoomAddMenu={setShowRoomAddMenu}
          setRoomVisibleCount={setRoomVisibleCount}
          setRoomParticipantMode={setRoomParticipantMode}
          setRoomCustomParticipants={setRoomCustomParticipants}
          setProjectActionMode={setProjectActionMode}
          setNewProjectIdDraft={setNewProjectIdDraft}
          setNewProjectNameDraft={setNewProjectNameDraft}
          setNewProjectRepoDraft={setNewProjectRepoDraft}
          setLinkedRepoDraft={setLinkedRepoDraft}
          setActiveTab={setActiveTab}
          setSelectedTaskId={setSelectedTaskId}
          addMention={addMention}
          handleSendChat={handleSendChat}
          handleToggleVoiceRecording={handleToggleVoiceRecording}
          handleChooseRepoFolder={handleChooseRepoFolder}
          handleCreateProject={handleCreateProject}
          handleRunTakeover={handleRunTakeover}
          handleSaveProjectLink={handleSaveProjectLink}
          handleApplyTakeoverRoadmap={handleApplyTakeoverRoadmap}
          handleApplyTakeoverTasks={handleApplyTakeoverTasks}
          handleLaunchTakeoverPlan={handleLaunchTakeoverPlan}
        />
      ) : activeTab === 'overview' ? (
        <OverviewTab
          composerLabel={composerLabel}
          backendHealth={backendHealth}
          directTargetLabel={directTargetLabel}
          selectedAgent={selectedAgent}
          lastEventAt={lastEventAt}
        />
      ) : activeTab === 'pilotage' ? (
        <PilotageTab
          composerLabel={composerLabel}
          fallbackDiagnostics={fallbackDiagnostics}
          backendHealth={backendHealth}
          eventLog={eventLog}
        />
      ) : activeTab === 'docs' ? (
        <DocsTab backendHealth={backendHealth} />
      ) : activeTab === 'todo' ? (
        <TodoTab
          handleCreateTask={handleCreateTask}
          handleSaveTask={handleSaveTask}
          handleTaskStatusMove={handleTaskStatusMove}
        />
      ) : activeTab === 'model_routing' ? (
        <ModelRoutingTab handleSaveLlmProfile={handleSaveLlmProfile} />
      ) : null}
    </div>
  )
}

export default App
