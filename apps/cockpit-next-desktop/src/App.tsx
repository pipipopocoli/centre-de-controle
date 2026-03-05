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
  createAgent,
  deleteAgent,
  getApiUrl,
  getApprovals,
  getChat,
  getLayout,
  getPixelFeed,
  liveTurn,
  openTerminal,
  putLayout,
  resetChat,
  restartTerminal,
  sendTerminalInput,
  connectEvents,
  rejectApproval,
} from './lib/cockpitClient'
import type {
  ApprovalRequest,
  ChatMessage,
  ChatMode,
  ExecutionMode,
  PixelFeedResponse,
  WsEventEnvelope,
} from './lib/cockpitClient'
import { openOsTerminal } from './lib/tauriOps'

const DEFAULT_PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID ?? 'cockpit'

type TopTab = 'pixel_home' | 'overview' | 'pilotage' | 'docs' | 'model_routing'
type WorkspaceTab = 'agent' | 'layout' | 'settings'
type ComposerStatus = 'live' | 'reconnecting' | 'http_fallback'

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

  const refreshApprovals = useCallback(async () => {
    try {
      const response = await getApprovals(projectId, 'pending')
      setApprovals(response.approvals)
    } catch {
      // keep silent to avoid noisy UI while reconnecting
    }
  }, [projectId])

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

      if (!selectedAgentId || !ids.has(selectedAgentId)) {
        setSelectedAgentId(nextFeed.agents[0]?.agent_id ?? null)
      }

      setAgentTools(tools)
      setRefreshTick((value) => value + 1)
    },
    [officeState, selectedAgentId, styleForAgent, toNumericId],
  )

  const refreshPixelFeed = useCallback(async () => {
    const nextFeed = await getPixelFeed(projectId)
    setFeed(nextFeed)
    syncOfficeAgents(nextFeed)
  }, [projectId, syncOfficeAgents])

  const bootstrap = useCallback(async () => {
    setLoading(true)
    setApiError(null)

    try {
      const [themeLoaded, pixelRefLoaded] = await Promise.all([loadDonargTheme(), loadPixelReferenceTheme()])

      const [layout, pixel, chat, pendingApprovals] = await Promise.all([
        getLayout(projectId),
        getPixelFeed(projectId),
        getChat(projectId, 300, 'all'),
        getApprovals(projectId, 'pending'),
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
  }, [mergeChatMessages, officeState, projectId, syncOfficeAgents])

  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  useEffect(() => {
    const disconnect = connectEvents(
      projectId,
      (event) => {
        setEventLog((previous) => [event, ...previous].slice(0, 160))

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
  }, [projectId, mergeChatMessages, refreshApprovals, refreshPixelFeed, stopFallbackPolling])

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

  const handleSendChat = useCallback(async () => {
    const text = chatInput.trim()
    if (!text || isSendingChat) {
      return
    }

    setChatInput('')
    setApiError(null)
    setUiNotice(null)
    setIsSendingChat(true)

    try {
      const response = await liveTurn(projectId, {
        text,
        chat_mode: chatMode,
        execution_mode: executionMode,
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
    executionMode,
    isSendingChat,
    mergeChatMessages,
    projectId,
    refreshApprovals,
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

  const topTabs = useMemo(
    () => [
      { id: 'pixel_home' as const, label: 'Pixel Home' },
      { id: 'overview' as const, label: 'Overview' },
      { id: 'pilotage' as const, label: 'Pilotage' },
      { id: 'docs' as const, label: 'Docs' },
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
          <h1>Cockpit Next</h1>
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
          </ul>
        </section>
      )
    }

    return (
      <section className="workspace-section">
        <div className="section-title-row">
          <h2>Agents</h2>
          <span className="hint">1 agent = 1 terminal</span>
        </div>

        <form className="create-form" onSubmit={handleCreateAgent}>
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

        <div className="agent-cards">
          {feed?.agents.map((agent) => (
            <button
              key={agent.agent_id}
              className={`agent-card ${selectedAgentId === agent.agent_id ? 'active' : ''}`}
              onClick={() => {
                void ensureAgentTerminal(agent.agent_id)
              }}
            >
              <div>
                <p className="agent-name">{agent.name}</p>
                <p className="agent-meta">
                  @{agent.agent_id} - L{agent.level} - {agent.role}
                </p>
              </div>
              <div className="agent-card-right">
                <span className={`dot ${agent.terminal_state === 'running' ? 'green' : 'gray'}`}>
                  {agent.terminal_state}
                </span>
                {agent.agent_id !== 'clems' ? (
                  <span
                    className="agent-delete"
                    onClick={(event) => {
                      event.stopPropagation()
                      void handleDeleteAgent(agent.agent_id)
                    }}
                  >
                    x
                  </span>
                ) : null}
              </div>
            </button>
          ))}
        </div>
      </section>
    )
  }

  const renderSecondaryTab = () => {
    const title = topTabs.find((tab) => tab.id === activeTab)?.label ?? 'Overview'
    if (activeTab === 'pilotage') {
      return (
        <section className="secondary-tab panel">
          <div className="secondary-header">
            <h2>Pilotage</h2>
            <span className="hint">diagnostics stream (visibility=all)</span>
          </div>
          <div className="secondary-grid">
            <article>
              <h3>Operator chat msgs</h3>
              <p>{operatorChatMessages.length}</p>
            </article>
            <article>
              <h3>Internal msgs</h3>
              <p>{internalChatMessages.length}</p>
            </article>
            <article>
              <h3>Pending approvals</h3>
              <p>{approvals.length}</p>
            </article>
            <article>
              <h3>WS status</h3>
              <p>{composerLabel}</p>
            </article>
          </div>
          <div className="events-log">
            {chatMessages
              .slice(-30)
              .reverse()
              .map((message) => (
                <p key={message.message_id}>
                  <strong>@{message.author}</strong> [{message.visibility}] {message.text}
                </p>
              ))}
          </div>
        </section>
      )
    }

    return (
      <section className="secondary-tab panel">
        <div className="secondary-header">
          <h2>{title}</h2>
          <span className="hint">Cockpit tab preserved in first release</span>
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
          <p className="eyebrow">Cockpit Next Rewrite</p>
          <h1>Pixel Home</h1>
        </div>
        <div className="header-status">
          <label className="project-input">
            Project
            <input
              value={projectId}
              onChange={(event) => setProjectId(event.target.value.trim() || DEFAULT_PROJECT_ID)}
            />
          </label>
          <div className={`status-pill ${wsConnected ? 'ok' : 'warn'}`}>WS {composerLabel}</div>
          <div className="status-pill neutral">API {getApiUrl()}</div>
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
                  <>
                    <section className="chat-section">
                      <div className="section-title-row">
                        <h2>Live Chat</h2>
                        <div className="chat-actions">
                          <button className="small-btn" onClick={() => void handleResetChat()}>
                            Reset Chat
                          </button>
                          <span className={`chat-status ${composerStatus}`}>{composerLabel}</span>
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

                      <div className="chat-log">
                        {operatorChatMessages.map((message) => (
                          <article key={message.message_id} className="chat-row">
                            <header>
                              <strong>@{message.author}</strong>
                              <time>{new Date(message.timestamp).toLocaleTimeString()}</time>
                            </header>
                            <p>{message.text}</p>
                          </article>
                        ))}
                      </div>

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
                              ? 'Say hello. Clems replies by default.'
                              : 'Conceal Room: L1 live fanout + Clems summary'
                          }
                        />
                        <button className="send-btn" onClick={() => void handleSendChat()} disabled={isSendingChat}>
                          {isSendingChat ? 'Sending...' : 'Send'}
                        </button>
                      </div>
                    </section>

                    <section className="terminal-section">
                      <div className="section-title-row">
                        <h2>Terminal</h2>
                        <span className="hint">{selectedAgentId ? `@${selectedAgentId}` : 'no agent selected'}</span>
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
                        <button onClick={() => void handleRestartTerminal()}>Restart</button>
                        <button onClick={() => void handleOpenExternalTerminal()}>Open OS</button>
                      </div>
                    </section>

                    <section className="approvals-section">
                      <div className="section-title-row">
                        <h2>Approvals</h2>
                        <span className="hint">pending: {approvals.length}</span>
                      </div>
                      <div className="approvals-log">
                        {approvals.length === 0 ? (
                          <p className="terminal-empty">No pending approvals.</p>
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

                    <section className="events-section">
                      <h2>Recent Events</h2>
                      <div className="events-log">
                        {eventLog.map((event, index) => (
                          <p key={`${event.timestamp}-${index}`}>
                            <strong>{event.type}</strong> {new Date(event.timestamp).toLocaleTimeString()}
                          </p>
                        ))}
                      </div>
                    </section>
                  </>
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
