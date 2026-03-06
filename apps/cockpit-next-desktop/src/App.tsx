import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import { EditorState } from './office/editor/editorState.js'
import { OfficeState } from './office/engine/officeState.js'
import { OfficeCanvas } from './office/components/OfficeCanvas.js'
import { ToolOverlay } from './office/components/ToolOverlay.js'
import type { ToolActivity } from './office/types.js'
import { loadDonargTheme } from './office/themes/donargTheme.js'
import { loadPixelReferenceTheme } from './office/themes/pixelReferenceTheme.js'
import {
  approveApproval,
  createTask,
  createAgent,
  deleteAgent,
  getApiUrl,
  getApprovals,
  getChat,
  getHealth,
  getLayout,
  getLlmProfile,
  getPixelFeed,
  getTasks,
  liveTurn,
  openTerminal,
  putLlmProfile,
  putLayout,
  resetChat,
  restartTerminal,
  sendTerminalInput,
  connectEvents,
  rejectApproval,
  updateTask,
} from './lib/cockpitClient'
import type {
  ApprovalRequest,
  ChatMessage,
  ChatMode,
  ExecutionMode,
  HealthzResponse,
  LlmProfile,
  PixelFeedResponse,
  TaskRecord,
  TaskStatus,
  WsEventEnvelope,
} from './lib/cockpitClient'
import { openOsTerminal } from './lib/tauriOps'

const DEFAULT_PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID ?? 'cockpit'

type TopTab = 'pixel_home' | 'overview' | 'pilotage' | 'docs' | 'todo' | 'model_routing'
type WorkspaceTab = 'agent' | 'layout' | 'settings'
type ComposerStatus = 'live' | 'reconnecting' | 'http_fallback'
type DirectTargetMode = 'clems' | 'selected_agent'
type WorkbenchPanel = 'chat' | 'terminal' | 'approvals' | 'events'

type TaskEditorState = {
  title: string
  owner: string
  phase: string
  status: TaskStatus
  objective: string
  done_definition: string
}

const STATUS_ORDER: TaskStatus[] = ['todo', 'in_progress', 'blocked', 'done']
const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'Todo',
  in_progress: 'In Progress',
  blocked: 'Blocked',
  done: 'Done',
}

const CLEMS_MODEL_OPTIONS = [
  { id: 'moonshotai/kimi-k2.5', label: 'Kimi K2.5', note: 'default L0' },
  { id: 'anthropic/claude-sonnet-4.6', label: 'Claude Sonnet 4.6', note: 'higher reasoning' },
  { id: 'anthropic/claude-opus-4.6', label: 'Claude Opus 4.6', note: 'max depth' },
] as const

const L1_MODEL_OPTIONS = [
  { id: 'moonshotai/kimi-k2.5', label: 'Kimi K2.5', note: 'fast default' },
  { id: 'anthropic/claude-sonnet-4.6', label: 'Claude Sonnet 4.6', note: 'strong lead' },
  { id: 'anthropic/claude-opus-4.6', label: 'Claude Opus 4.6', note: 'max depth' },
  { id: 'openai/gpt-5.4', label: 'GPT-5.4', note: 'broad reasoning' },
  { id: 'google/gemini-3.1-pro-preview', label: 'Gemini 3.1 Pro Preview', note: 'wide context' },
  { id: 'x-ai/grok-4', label: 'Grok 4', note: 'current OpenRouter grok 4.x entry' },
] as const

const L2_MODEL_OPTIONS = [
  { id: 'minimax/minimax-m2.5', label: 'MiniMax M2.5', note: 'surgical primary' },
  { id: 'moonshotai/kimi-k2.5', label: 'Kimi K2.5', note: 'precise fallback' },
  { id: 'deepseek/deepseek-chat-v3.1', label: 'DeepSeek Chat V3.1', note: 'bounded execution' },
] as const

function modelLabel(modelId: string): string {
  const found = [...CLEMS_MODEL_OPTIONS, ...L1_MODEL_OPTIONS, ...L2_MODEL_OPTIONS].find(
    (option) => option.id === modelId,
  )
  return found ? found.label : `${modelId} (unavailable)`
}

function isUnavailableModel(modelId: string): boolean {
  return modelLabel(modelId).endsWith('(unavailable)')
}

function emptyTaskEditor(): TaskEditorState {
  return {
    title: '',
    owner: 'clems',
    phase: 'Implement',
    status: 'todo',
    objective: '',
    done_definition: '',
  }
}

function compareTasksByFreshness(left: TaskRecord, right: TaskRecord): number {
  const leftTime = Date.parse(left.updated_at)
  const rightTime = Date.parse(right.updated_at)
  if (Number.isNaN(leftTime) || Number.isNaN(rightTime)) {
    return left.task_id.localeCompare(right.task_id)
  }
  return rightTime - leftTime
}

function messageKindLabel(message: ChatMessage): string | null {
  const rawKind = typeof message.metadata?.kind === 'string' ? message.metadata.kind : null
  if (!rawKind) {
    return message.author === 'operator' ? 'operator' : null
  }

  const labels: Record<string, string> = {
    direct_reply: 'direct reply',
    direct_summary: 'internal summary',
    conceal_reply: 'room reply',
    conceal_summary: 'room summary',
    approval_pending: 'approval pending',
    approval_spawn: 'approval spawn',
    terminal_online_ack: 'terminal ready',
  }

  return labels[rawKind] ?? rawKind.replaceAll('_', ' ')
}

function App() {
  const [projectId, setProjectId] = useState(DEFAULT_PROJECT_ID)
  const [apiError, setApiError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [feed, setFeed] = useState<PixelFeedResponse | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatMode, setChatMode] = useState<ChatMode>('direct')
  const [executionMode, setExecutionMode] = useState<ExecutionMode>('chat')
  const [wsConnected, setWsConnected] = useState(false)
  const [composerStatus, setComposerStatus] = useState<ComposerStatus>('reconnecting')
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null)
  const [directTarget, setDirectTarget] = useState<DirectTargetMode>('clems')
  const [terminalInput, setTerminalInput] = useState('')
  const [terminalLogs, setTerminalLogs] = useState<Record<string, string[]>>({})
  const [eventLog, setEventLog] = useState<WsEventEnvelope[]>([])
  const [createAgentId, setCreateAgentId] = useState('')
  const [createAgentName, setCreateAgentName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSendingChat, setIsSendingChat] = useState(false)
  const [showAddMenu, setShowAddMenu] = useState(false)
  const [refreshTick, setRefreshTick] = useState(0)
  const [agentTools, setAgentTools] = useState<Record<number, ToolActivity[]>>({})
  const [overlayViewport, setOverlayViewport] = useState({
    viewportWidth: 0,
    viewportHeight: 0,
    panX: 0,
    panY: 0,
    dpr: 1,
  })
  const [activeTab, setActiveTab] = useState<TopTab>('pixel_home')
  const [workspaceTab, setWorkspaceTab] = useState<WorkspaceTab>('agent')
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [approvalBusy, setApprovalBusy] = useState<Record<string, boolean>>({})
  const [uiNotice, setUiNotice] = useState<string | null>(null)
  const [zoom, setZoom] = useState(2)
  const [workbenchCollapsed, setWorkbenchCollapsed] = useState(false)
  const [workbenchPanel, setWorkbenchPanel] = useState<WorkbenchPanel>('chat')
  const [backendHealth, setBackendHealth] = useState<HealthzResponse | null>(null)
  const [llmProfile, setLlmProfile] = useState<LlmProfile | null>(null)
  const [profileDraft, setProfileDraft] = useState<LlmProfile | null>(null)
  const [tasks, setTasks] = useState<TaskRecord[]>([])
  const [taskEditor, setTaskEditor] = useState<TaskEditorState>(emptyTaskEditor)
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [isSavingTask, setIsSavingTask] = useState(false)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [clockNow, setClockNow] = useState(() => new Date())
  const [lastEventAt, setLastEventAt] = useState<string | null>(null)
  const [lastSyncAt, setLastSyncAt] = useState<string | null>(null)
  const [assetsStatus, setAssetsStatus] = useState<{ donarg: boolean; pixelRef: boolean }>({
    donarg: false,
    pixelRef: false,
  })

  const officeState = useMemo(() => new OfficeState(), [])
  const editorState = useMemo(() => new EditorState(), [])
  const panRef = useRef({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)
  const wsConnectedRef = useRef(false)
  const fallbackPollingRef = useRef(false)
  const fallbackPollTimerRef = useRef<number | null>(null)
  const fallbackStopTimerRef = useRef<number | null>(null)

  const idToNumericRef = useRef(new Map<string, number>())
  const numericToIdRef = useRef(new Map<number, string>())
  const nextNumericRef = useRef(1)

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

  const mergeChatMessages = useCallback((incoming: ChatMessage[]) => {
    if (incoming.length === 0) {
      return
    }

    setChatMessages((previous) => {
      const byId = new Map<string, ChatMessage>()
      for (const row of previous) {
        byId.set(row.message_id, {
          ...row,
          visibility: row.visibility ?? 'operator',
        })
      }
      for (const row of incoming) {
        if (!row?.message_id) {
          continue
        }
        byId.set(row.message_id, {
          ...row,
          visibility: row.visibility ?? 'operator',
        })
      }

      return [...byId.values()].sort((a, b) => {
        if (a.timestamp === b.timestamp) {
          return a.message_id.localeCompare(b.message_id)
        }
        return a.timestamp.localeCompare(b.timestamp)
      })
    })
  }, [])

  const operatorChatMessages = useMemo(
    () => chatMessages.filter((message) => message.visibility !== 'internal'),
    [chatMessages],
  )

  const internalChatMessages = useMemo(
    () => chatMessages.filter((message) => message.visibility === 'internal'),
    [chatMessages],
  )

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

  const markSynced = useCallback(() => {
    setLastSyncAt(new Date().toISOString())
  }, [])

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

      setSelectedAgentId((previous) => {
        if (previous && ids.has(previous)) {
          return previous
        }
        return nextFeed.agents[0]?.agent_id ?? null
      })

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

      const [layout, pixel, chat, pendingApprovals, health, profile, taskPayload] = await Promise.all([
        getLayout(projectId),
        getPixelFeed(projectId),
        getChat(projectId, 300, 'all'),
        getApprovals(projectId, 'pending'),
        getHealth(),
        getLlmProfile(projectId),
        getTasks(projectId),
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
      setSelectedTaskId((previous) => previous ?? taskPayload.tasks[0]?.task_id ?? null)
      setAssetsStatus({
        donarg: themeLoaded,
        pixelRef: pixelRefLoaded,
      })
      setLastEventAt(health.time ?? null)
      markSynced()
      syncOfficeAgents(pixel)

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
  }, [markSynced, mergeChatMessages, officeState, projectId, syncOfficeAgents])

  const selectedTask = useMemo(
    () => tasks.find((task) => task.task_id === selectedTaskId) ?? null,
    [selectedTaskId, tasks],
  )

  useEffect(() => {
    const timer = window.setInterval(() => setClockNow(new Date()), 1000)
    return () => window.clearInterval(timer)
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
          return
        }

        if (event.type === 'agent.terminal.status') {
          const agentId = String(event.payload.agent_id ?? '')
          const chunk = event.payload.chunk
          if (agentId && typeof chunk === 'string' && chunk.length > 0) {
            setTerminalLogs((previous) => {
              const history = [...(previous[agentId] ?? []), chunk].slice(-260)
              return {
                ...previous,
                [agentId]: history,
              }
            })
          }

          const state = String(event.payload.state ?? '')
          if (state !== 'output') {
            void refreshPixelFeed()
          }
          return
        }

        if (
          event.type === 'agent.created' ||
          event.type === 'agent.updated' ||
          event.type === 'pixel.updated' ||
          event.type === 'layout.updated' ||
          event.type === 'agent.spawn.completed'
        ) {
          void refreshPixelFeed()
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
  }, [projectId, mergeChatMessages, refreshApprovals, refreshPixelFeed, refreshTasks, stopFallbackPolling])

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
        }
        const created = await createAgent(projectId, payload)
        setCreateAgentId('')
        setCreateAgentName('')
        setSelectedAgentId(created.agent.agent_id)
        await refreshPixelFeed()
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      } finally {
        setIsSubmitting(false)
      }
    },
    [createAgentId, createAgentName, isSubmitting, projectId, refreshPixelFeed],
  )

  const handleDeleteAgent = useCallback(
    async (agentId: string) => {
      setApiError(null)
      try {
        await deleteAgent(projectId, agentId)
        await refreshPixelFeed()
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      }
    },
    [projectId, refreshPixelFeed],
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
      setUiNotice(`task created: ${created.task_id}`)
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsSavingTask(false)
    }
  }, [isSavingTask, projectId, taskEditor])

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
      setUiNotice(`task updated: ${updated.task_id}`)
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setIsSavingTask(false)
    }
  }, [isSavingTask, projectId, selectedTaskId, taskEditor])

  const handleTaskStatusMove = useCallback(
    async (taskId: string, status: TaskStatus) => {
      setApiError(null)
      try {
        const updated = await updateTask(projectId, taskId, { status })
        setTasks((previous) =>
          previous.map((task) => (task.task_id === updated.task_id ? updated : task)),
        )
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      }
    },
    [projectId],
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

  const handleOfficeClick = useCallback(
    async (numericId: number) => {
      const agentId = numericToIdRef.current.get(numericId)
      if (!agentId) {
        return
      }

      await ensureAgentTerminal(agentId)
    },
    [ensureAgentTerminal],
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

  const selectedAgent = useMemo(
    () => feed?.agents.find((agent) => agent.agent_id === selectedAgentId) ?? null,
    [feed, selectedAgentId],
  )

  const selectedAgentChatReady = selectedAgent?.chat_targetable ?? false

  const handleSendChat = useCallback(async (targetMode: DirectTargetMode = directTarget) => {
    const text = chatInput.trim()
    if (!text || isSendingChat) {
      return
    }

    const targetAgentId =
      chatMode === 'direct' && targetMode === 'selected_agent' ? (selectedAgent?.chat_targetable ? selectedAgent.agent_id : null) : null
    if (chatMode === 'direct' && targetMode === 'selected_agent' && !targetAgentId) {
      setUiNotice('select a chat-ready agent first')
      return
    }

    setChatInput('')
    setApiError(null)
    setUiNotice(null)
    setIsSendingChat(true)
    if (chatMode === 'direct') {
      setDirectTarget(targetMode)
    }

    try {
      const response = await liveTurn(projectId, {
        text,
        chat_mode: chatMode,
        execution_mode: executionMode,
        target_agent_id: targetAgentId,
      })

      mergeChatMessages(response.messages)
      if (response.approval_requests.length > 0) {
        void refreshApprovals()
      }

      if (response.error) {
        setUiNotice(`degraded mode: ${response.error}`)
      }

      if (!wsConnectedRef.current || response.delivery_mode !== 'ws') {
        startFallbackPolling()
      } else {
        setComposerStatus('live')
      }
    } catch (error) {
      setChatInput(text)
      setApiError(error instanceof Error ? error.message : String(error))
      setUiNotice('send failed. draft restored.')
    } finally {
      setIsSendingChat(false)
    }
  }, [
    chatInput,
    chatMode,
    directTarget,
    executionMode,
    isSendingChat,
    mergeChatMessages,
    projectId,
    refreshApprovals,
    selectedAgent,
    startFallbackPolling,
  ])

  const handleSendTerminal = useCallback(async () => {
    if (!selectedAgentId) {
      return
    }
    const text = terminalInput.trim()
    if (!text) {
      return
    }

    setTerminalInput('')
    setApiError(null)
    try {
      await sendTerminalInput(projectId, selectedAgentId, text)
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    }
  }, [projectId, selectedAgentId, terminalInput])

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
            decided_by: 'olivier',
            note: 'approved from cockpit next ui',
          })
        } else {
          await rejectApproval(projectId, requestId, {
            decided_by: 'olivier',
            note: 'rejected from cockpit next ui',
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

  const addMention = useCallback((mention: string) => {
    setChatInput((previous) => {
      if (previous.trim().length === 0) {
        return `@${mention} `
      }
      return `${previous} @${mention} `
    })
    setShowAddMenu(false)
  }, [])

  const agentNumericIds = useMemo(() => {
    if (!feed) {
      return []
    }
    return feed.agents.map((agent) => toNumericId(agent.agent_id))
  }, [feed, toNumericId])

  const selectedLog = useMemo(() => {
    if (!selectedAgentId) {
      return []
    }
    return terminalLogs[selectedAgentId] ?? []
  }, [selectedAgentId, terminalLogs])
  const profileDirty = useMemo(() => {
    if (!llmProfile || !profileDraft) {
      return false
    }
    return JSON.stringify(llmProfile) !== JSON.stringify(profileDraft)
  }, [llmProfile, profileDraft])
  const l1Agents = useMemo(() => {
    const fromFeed = (feed?.agents ?? [])
      .filter((agent) => agent.level === 1)
      .map((agent) => agent.agent_id)
    const fromProfile = profileDraft ? Object.keys(profileDraft.l1_models ?? {}) : []
    return [...new Set([...fromFeed, ...fromProfile])].sort()
  }, [feed?.agents, profileDraft])
  const directTargetLabel =
    directTarget === 'selected_agent'
      ? selectedAgent
        ? selectedAgentChatReady
          ? `@${selectedAgent.agent_id}`
          : `@${selectedAgent.agent_id} unavailable`
        : 'selected agent unavailable'
      : '@clems'

  const topTabs = useMemo(
    () => [
      { id: 'pixel_home' as const, label: 'Pixel Home' },
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
      { id: 'agent' as const, label: '+ Agent' },
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
            <li>chat mode: {chatMode}</li>
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
          <span className="hint">chat + terminal</span>
        </div>

        <div className="agent-create-card">
          <form className="create-form compact" onSubmit={handleCreateAgent}>
            <input
              placeholder="agent id (optional)"
              value={createAgentId}
              onChange={(event) => setCreateAgentId(event.target.value)}
            />
            <input
              placeholder="name (optional)"
              value={createAgentName}
              onChange={(event) => setCreateAgentName(event.target.value)}
            />
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : '+ Agent'}
            </button>
          </form>
        </div>

        <div className="agent-cards">
          {feed?.agents.map((agent) => (
            <article key={agent.agent_id} className={`agent-card ${selectedAgentId === agent.agent_id ? 'active' : ''}`}>
              <button className="agent-card-main" onClick={() => handleSelectAgent(agent.agent_id)}>
                <div className="agent-card-head">
                  <div>
                    <p className="agent-name">{agent.name}</p>
                    <p className="agent-meta">
                      @{agent.agent_id}
                    </p>
                  </div>
                  <span className="agent-level-pill">L{agent.level}</span>
                </div>
                <p className="agent-role">{agent.role}</p>
                <div className="agent-card-statuses">
                  <span className={`dot ${agent.chat_targetable ? 'green' : 'gray'}`}>
                    {agent.chat_targetable ? 'chat ready' : 'chat unavailable'}
                  </span>
                  <span className={`dot ${agent.terminal_state === 'running' ? 'green' : 'gray'}`}>
                    terminal {agent.terminal_state === 'running' ? 'live' : 'offline'}
                  </span>
                </div>
              </button>
              <div className="agent-card-footer">
                <button
                  className="agent-action"
                  onClick={() => {
                    setSelectedAgentId(agent.agent_id)
                    setWorkbenchPanel('terminal')
                    void ensureAgentTerminal(agent.agent_id)
                  }}
                >
                  Open terminal
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
    const latestOperator = operatorChatMessages.slice(-8).reverse()
    const latestInternal = internalChatMessages.slice(-8).reverse()
    const latestEvents = eventLog.slice(0, 20)
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
      { label: 'WS', value: composerLabel },
      { label: 'Agents', value: String(agentsTotal) },
      { label: 'Terminals live', value: String(runningTerminals) },
      { label: 'Queue', value: String(queueDepth) },
      { label: 'Tasks open', value: String(taskCounts.todo + taskCounts.in_progress + taskCounts.blocked) },
    ]

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
              <p>{operatorChatMessages.length}</p>
            </article>
            <article>
              <h3>Internal messages</h3>
              <p>{internalChatMessages.length}</p>
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
              <h3>Latest operator chat</h3>
              <div className="events-log">
                {latestOperator.length === 0 ? (
                  <p>No operator messages yet.</p>
                ) : (
                  latestOperator.map((message) => (
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
                {latestInternal.length === 0 && latestEvents.length === 0 ? <p>No diagnostics yet.</p> : null}
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
          <div className="secondary-grid">
            <article>
              <h3>Backend status</h3>
              <p>{backendHealth?.status ?? 'unknown'}</p>
            </article>
            <article>
              <h3>Build SHA</h3>
              <p>{buildStamp}</p>
            </article>
            <article>
              <h3>Assets loaded</h3>
              <p>{assetsStatus.donarg && assetsStatus.pixelRef ? 'yes' : 'partial'}</p>
            </article>
            <article>
              <h3>Clock</h3>
              <p>{clockNow.toLocaleTimeString()}</p>
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
              <h3>Task board snapshot</h3>
              <ul className="data-list">
                {STATUS_ORDER.map((status) => (
                  <li key={status}>
                    <span>{STATUS_LABELS[status]}</span>
                    <strong>{taskCounts[status]}</strong>
                  </li>
                ))}
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Operational focus</h3>
              <div className="events-log">
                <p><strong>Direct target:</strong> {directTargetLabel}</p>
                <p><strong>Selected agent:</strong> {selectedAgent ? `@${selectedAgent.agent_id}` : 'none'}</p>
                <p><strong>Chat transport:</strong> {composerLabel}</p>
                <p><strong>Approvals pending:</strong> {approvals.length}</p>
                <p><strong>Open tasks:</strong> {taskCounts.todo + taskCounts.in_progress + taskCounts.blocked}</p>
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
                  <div className="todo-column-body">
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
            <span className="hint">daily path, contracts, and launch truth</span>
          </div>
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
                <p>4. Work from Pixel Home, To Do, and Model Routing only</p>
              </div>
            </section>
            <section className="secondary-card">
              <h3>Reference docs</h3>
              <div className="events-log">
                <p><strong>Runbook:</strong> docs/COCKPIT_NEXT_RUNBOOK.md</p>
                <p><strong>Protocol:</strong> docs/CLOUD_API_PROTOCOL.md</p>
                <p><strong>Packaging:</strong> docs/PACKAGING.md</p>
                <p><strong>Status:</strong> docs/STATUS_REPORT.md</p>
              </div>
            </section>
          </div>
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
    <div className="app-shell">
      <header className="app-header panel">
        <div>
          <p className="eyebrow">Cockpit official</p>
          <h1>Pixel Home</h1>
          <p className="header-subcopy">
            {clockNow.toLocaleDateString()} - local control tower for pixel operations, tasks, and model routing
          </p>
        </div>
        <div className="header-status">
          <label className="project-input">
            Project
            <input
              value={projectId}
              onChange={(event) => setProjectId(event.target.value.trim() || DEFAULT_PROJECT_ID)}
            />
          </label>
          <div className={`status-pill ${backendHealth?.status === 'ok' ? 'ok' : 'warn'}`}>
            Backend {backendHealth?.status ?? 'unknown'}
          </div>
          <div className={`status-pill ${wsConnected ? 'ok' : 'warn'}`}>WS {composerLabel}</div>
          <div className="status-pill neutral">Time {clockNow.toLocaleTimeString()}</div>
          <div className="status-pill neutral">
            Sync {lastSyncAt ? new Date(lastSyncAt).toLocaleTimeString() : 'none'}
          </div>
          <div className="status-pill neutral">API {getApiUrl()}</div>
          <div className="status-pill neutral">
            Build {(backendHealth?.build_sha ?? 'unknown').slice(0, 12)}
          </div>
          <div className="status-pill neutral">
            Event {lastEventAt ? new Date(lastEventAt).toLocaleTimeString() : 'none'}
          </div>
        </div>
      </header>

      <nav className="top-tabs panel">
        {topTabs.map((tab) => (
          <button
            key={tab.id}
            className={`top-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {apiError ? <div className="error-banner">{apiError}</div> : null}
      {uiNotice ? <div className="notice-banner">{uiNotice}</div> : null}

      {activeTab !== 'pixel_home' ? (
        renderSecondaryTab()
      ) : (
        <main className="pixel-shell panel">
          <aside className="left-rail">
            <button className="rail-btn active">home</button>
            <button className="rail-btn">agents</button>
            <button className="rail-btn">layout</button>
            <button className="rail-btn">chat</button>
            <button className="rail-btn">term</button>
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
                    <button onClick={() => setWorkbenchCollapsed((value) => !value)}>
                      {workbenchCollapsed ? 'workbench' : 'collapse'}
                    </button>
                    <button onClick={() => setZoom((value) => Math.max(0.5, Number((value - 0.2).toFixed(2))))}>-</button>
                    <span>{zoom.toFixed(1)}x</span>
                    <button onClick={() => setZoom((value) => Math.min(4, Number((value + 0.2).toFixed(2))))}>+</button>
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
                            onClick={() => setWorkbenchPanel(tab.id)}
                          >
                            <span>{tab.label}</span>
                            {tab.count ? <span className="workbench-tab-count">{tab.count}</span> : null}
                          </button>
                        ))}
                      </div>
                      <div className="workbench-summary">
                        <span className="chat-target">Target {chatMode === 'direct' ? directTargetLabel : 'conceal room'}</span>
                        <span className={`chat-status ${composerStatus}`}>{composerLabel}</span>
                        <span className="workbench-mini-pill">
                          terminal {selectedAgent?.terminal_state === 'running' ? 'live' : selectedAgentId ? 'offline' : 'none'}
                        </span>
                      </div>
                    </div>

                    {workbenchPanel === 'chat' ? (
                      <section className="chat-section">
                        <div className="section-title-row">
                          <h2>Live Chat</h2>
                          <div className="chat-actions">
                            <button className="small-btn" onClick={() => void handleResetChat()}>
                              Reset chat
                            </button>
                          </div>
                        </div>
                        <div className="mode-row">
                          <div className="mode-toggle">
                            <button
                              className={chatMode === 'direct' ? 'active' : ''}
                              onClick={() => setChatMode('direct')}
                            >
                              Direct
                            </button>
                            <button
                              className={chatMode === 'conceal_room' ? 'active' : ''}
                              onClick={() => setChatMode('conceal_room')}
                            >
                              Conceal Room
                            </button>
                          </div>
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

                        {chatMode === 'direct' ? (
                          <div className="chat-target-card">
                            <div className="chat-target-actions">
                              <button
                                className={`target-btn ${directTarget === 'clems' ? 'active' : ''}`}
                                onClick={() => setDirectTarget('clems')}
                              >
                                Talk to Clems
                              </button>
                              <button
                                className={`target-btn ${directTarget === 'selected_agent' ? 'active' : ''}`}
                                onClick={() => setDirectTarget('selected_agent')}
                                disabled={!selectedAgentChatReady}
                              >
                                Talk to selected agent
                              </button>
                            </div>
                            <div className="chat-target-details">
                              <p className="small-copy">Agent chat uses the model lane directly. Terminal state stays separate.</p>
                              <p className="chat-target-detail">
                                {selectedAgent
                                  ? selectedAgentChatReady
                                    ? `Selected target: @${selectedAgent.agent_id}`
                                    : `Selected target: @${selectedAgent.agent_id} is not chat-ready`
                                  : 'No agent selected yet. Pick one from the roster to enable direct agent chat.'}
                              </p>
                            </div>
                          </div>
                        ) : (
                          <p className="small-copy">Conceal Room fans out to L1 and returns a Clems operator summary.</p>
                        )}

                        <div className="chat-log">
                          {operatorChatMessages.length === 0 ? (
                            <p className="chat-empty">No chat yet. Send a first message to start live flow.</p>
                          ) : (
                            operatorChatMessages.map((message) => (
                              <article key={message.message_id} className="chat-row">
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
                          <div className="composer-row">
                            <div className="plus-wrap">
                              <button className="plus-btn" onClick={() => setShowAddMenu((value) => !value)}>
                                +
                              </button>
                              {showAddMenu ? (
                                <div className="plus-menu">
                                  <button onClick={() => addMention('clems')}>mention @clems</button>
                                  <button onClick={() => addMention('victor')}>mention @victor</button>
                                  <button onClick={() => addMention('leo')}>mention @leo</button>
                                  <button onClick={() => addMention('nova')}>mention @nova</button>
                                </div>
                              ) : null}
                            </div>

                            <input
                              value={chatInput}
                              onChange={(event) => setChatInput(event.target.value)}
                              onKeyDown={(event) => {
                                if (event.key === 'Enter') {
                                  event.preventDefault()
                                  void handleSendChat()
                                }
                              }}
                              placeholder={
                                chatMode === 'direct'
                                  ? directTarget === 'selected_agent'
                                    ? selectedAgentChatReady
                                      ? `Send to @${selectedAgent?.agent_id}`
                                      : 'Select a chat-ready agent or switch back to Clems.'
                                    : 'Talk to Clems directly.'
                                  : 'Conceal Room: L1 live fanout + Clems summary'
                              }
                            />
                          </div>
                          <div className="composer-actions-row">
                            {chatMode === 'direct' ? (
                              <div className="composer-actions">
                                <button
                                  className="send-btn"
                                  onClick={() => void handleSendChat('clems')}
                                  disabled={isSendingChat}
                                >
                                  {isSendingChat && directTarget === 'clems' ? 'Sending...' : 'Talk to Clems'}
                                </button>
                                <button
                                  className="send-btn alt"
                                  onClick={() => void handleSendChat('selected_agent')}
                                  disabled={isSendingChat || !selectedAgentChatReady}
                                >
                                  {isSendingChat && directTarget === 'selected_agent'
                                    ? 'Sending...'
                                    : 'Talk to selected agent'}
                                </button>
                              </div>
                            ) : (
                              <button className="send-btn" onClick={() => void handleSendChat()} disabled={isSendingChat}>
                                {isSendingChat ? 'Sending...' : 'Send to room'}
                              </button>
                            )}
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
                          <>
                            <div className="terminal-summary-card">
                              <div>
                                <strong>@{selectedAgentId}</strong>
                                <p className="small-copy">Terminal state: {selectedAgent?.terminal_state === 'running' ? 'live' : 'offline'}</p>
                              </div>
                              <div className="terminal-summary-actions">
                                <button onClick={() => void handleRestartTerminal()}>Restart</button>
                                <button onClick={() => void handleOpenExternalTerminal()}>Open OS</button>
                              </div>
                            </div>
                            <div className="terminal-log">
                              {selectedLog.length === 0 ? (
                                <p className="terminal-empty">No terminal output yet.</p>
                              ) : (
                                selectedLog.map((line, index) => (
                                  <pre key={`${index}-${line.slice(0, 12)}`}>{line}</pre>
                                ))
                              )}
                            </div>
                            <div className="terminal-controls">
                              <input
                                value={terminalInput}
                                onChange={(event) => setTerminalInput(event.target.value)}
                                onKeyDown={(event) => {
                                  if (event.key === 'Enter') {
                                    event.preventDefault()
                                    void handleSendTerminal()
                                  }
                                }}
                                placeholder="terminal command"
                              />
                              <button onClick={() => void handleSendTerminal()}>Send</button>
                            </div>
                          </>
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
                        <div className="approvals-log">
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
                        <div className="events-log">
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
                  onClick={() => setWorkspaceTab(tab.id)}
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
