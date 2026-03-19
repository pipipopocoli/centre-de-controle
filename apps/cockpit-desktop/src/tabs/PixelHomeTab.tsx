import type { FormEvent, RefObject } from 'react'
import { useCallback, useMemo } from 'react'
import {
  useCockpitStore,
  selectActiveChatMode,
  useDirectChatMessages,
} from '../store/index.js'
import type { ChatMode } from '../lib/cockpitClient'
import { getApiUrl, openTerminal, restartTerminal } from '../lib/cockpitClient'
import { openOsTerminal } from '../lib/tauriOps'
import type {
  DirectTargetMode,
  RosterAgentView,
  WorkbenchPanel,
} from '../types.js'
import {
  messageKindLabel,
} from '../lib/formatters.js'
import { QUICK_AGENT_PRESETS } from '../lib/appConstants.js'
import { AgentDashboard } from '../components/AgentDashboard.js'
import type { OfficeState } from '../office/engine/officeState.js'
import type { EditorState } from '../office/editor/editorState.js'
import { OfficeCanvas } from '../office/components/OfficeCanvas.js'
import { ToolOverlay } from '../office/components/ToolOverlay.js'

export interface PixelHomeTabProps {
  officeState: OfficeState
  editorState: EditorState
  containerRef: RefObject<HTMLDivElement | null>
  panRef: RefObject<{ x: number; y: number }>
  createAgentIdInputRef: RefObject<HTMLInputElement | null>
  directChatLogRef: RefObject<HTMLDivElement | null>
  directStickToBottomRef: RefObject<boolean>
  rosterAgents: RosterAgentView[]
  selectedAgent: RosterAgentView | null
  selectedAgentChatReady: boolean
  activeTasksByOwner: Map<string, { title: string }>
  resolvedModelForAgent: (agent: RosterAgentView) => string
  agentNumericIds: number[]
  directTargetLabel: string
  directTargetBadge: string
  directTargetNotice: string
  composerLabel: string
  handleSelectAgent: (agentId: string) => void
  handleCreateAgent: (event: FormEvent) => Promise<void>
  handleDeleteAgent: (agentId: string) => Promise<void>
  handleQuickAgent: (agentId: string) => Promise<void>
  handleOfficeClick: (numericId: number) => Promise<void>
  handleOfficeClose: (numericId: number) => void
  handleSendChat: (options?: {
    targetMode?: DirectTargetMode
    chatMode?: ChatMode
    contextRef?: Record<string, unknown> | null
  }) => Promise<void>
  handleResetChat: () => Promise<void>
  handleToggleVoiceRecording: () => Promise<void>
  handleApproval: (requestId: string, decision: 'approve' | 'reject') => Promise<void>
  handleApplyVideoPreset: () => Promise<void>
  bootstrap: () => Promise<void>
  refreshPixelFeed: () => Promise<void>
}

export function PixelHomeTab({
  officeState,
  editorState,
  containerRef,
  panRef,
  createAgentIdInputRef,
  directChatLogRef,
  directStickToBottomRef,
  rosterAgents,
  selectedAgent,
  selectedAgentChatReady,
  activeTasksByOwner,
  resolvedModelForAgent,
  agentNumericIds,
  directTargetLabel,
  directTargetBadge,
  directTargetNotice,
  composerLabel,
  handleSelectAgent,
  handleCreateAgent,
  handleDeleteAgent,
  handleQuickAgent,
  handleOfficeClick,
  handleOfficeClose,
  handleSendChat,
  handleResetChat,
  handleToggleVoiceRecording,
  handleApproval,
  handleApplyVideoPreset,
  bootstrap,
  refreshPixelFeed,
}: PixelHomeTabProps) {
  const projectId = useCockpitStore((s) => s.projectId)
  const feed = useCockpitStore((s) => s.feed)
  const agentRecords = useCockpitStore((s) => s.agentRecords)
  const selectedAgentId = useCockpitStore((s) => s.selectedAgentId)
  const setSelectedAgentId = useCockpitStore((s) => s.setSelectedAgentId)
  const directTarget = useCockpitStore((s) => s.directTarget)
  const setDirectTarget = useCockpitStore((s) => s.setDirectTarget)
  const directChatInput = useCockpitStore((s) => s.directChatInput)
  const setDirectChatInput = useCockpitStore((s) => s.setDirectChatInput)
  const directVisibleCount = useCockpitStore((s) => s.directVisibleCount)
  const setDirectVisibleCount = useCockpitStore((s) => s.setDirectVisibleCount)
  const directSendPhase = useCockpitStore((s) => s.directSendPhase)
  const composerStatus = useCockpitStore((s) => s.composerStatus)
  const isSendingChat = useCockpitStore((s) => s.isSendingChat)
  const isRecordingVoice = useCockpitStore((s) => s.isRecordingVoice)
  const isTranscribingVoice = useCockpitStore((s) => s.isTranscribingVoice)
  const isSubmitting = useCockpitStore((s) => s.isSubmitting)
  const createAgentId = useCockpitStore((s) => s.createAgentId)
  const setCreateAgentId = useCockpitStore((s) => s.setCreateAgentId)
  const createAgentName = useCockpitStore((s) => s.createAgentName)
  const setCreateAgentName = useCockpitStore((s) => s.setCreateAgentName)
  const createAgentSkills = useCockpitStore((s) => s.createAgentSkills)
  const setCreateAgentSkills = useCockpitStore((s) => s.setCreateAgentSkills)
  const workspaceTab = useCockpitStore((s) => s.workspaceTab)
  const setWorkspaceTab = useCockpitStore((s) => s.setWorkspaceTab)
  const workbenchPanel = useCockpitStore((s) => s.workbenchPanel)
  const setWorkbenchPanel = useCockpitStore((s) => s.setWorkbenchPanel)
  const workbenchCollapsed = useCockpitStore((s) => s.workbenchCollapsed)
  const setWorkbenchCollapsed = useCockpitStore((s) => s.setWorkbenchCollapsed)
  const zoom = useCockpitStore((s) => s.zoom)
  const setZoom = useCockpitStore((s) => s.setZoom)
  const refreshTick = useCockpitStore((s) => s.refreshTick)
  const agentTools = useCockpitStore((s) => s.agentTools)
  const overlayViewport = useCockpitStore((s) => s.overlayViewport)
  const approvals = useCockpitStore((s) => s.approvals)
  const approvalBusy = useCockpitStore((s) => s.approvalBusy)
  const eventLog = useCockpitStore((s) => s.eventLog)
  const wsConnected = useCockpitStore((s) => s.wsConnected)
  const lastSyncAt = useCockpitStore((s) => s.lastSyncAt)
  const executionMode = useCockpitStore((s) => s.executionMode)
  const setApiError = useCockpitStore((s) => s.setApiError)
  const setActiveTab = useCockpitStore((s) => s.setActiveTab)
  const activeChatMode = useCockpitStore(selectActiveChatMode)
  const directChatMessages = useDirectChatMessages()

  const visibleDirectMessages = useMemo(
    () => directChatMessages.slice(-directVisibleCount),
    [directChatMessages, directVisibleCount],
  )

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
  }, [projectId, refreshPixelFeed, selectedAgentId, setApiError])

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
  }, [projectId, selectedAgentId, setApiError])

  const workspaceTabs = useMemo(
    () => [
      { id: 'agent' as const, label: 'Agents' },
      { id: 'layout' as const, label: 'Layout' },
      { id: 'settings' as const, label: 'Settings' },
    ],
    [],
  )

  const workbenchTabs = useMemo(() => [
    { id: 'chat' as const, label: 'Chat' },
    {
      id: 'terminal' as const,
      label: 'Terminal',
      count: selectedAgent?.terminal_state === 'running' ? 'live' : selectedAgentId ? 'offline' : 'none',
    },
    { id: 'approvals' as const, label: 'Approvals', count: approvals.length > 0 ? String(approvals.length) : undefined },
    { id: 'events' as const, label: 'Events', count: eventLog.length > 0 ? String(Math.min(eventLog.length, 99)) : undefined },
  ] satisfies Array<{ id: WorkbenchPanel; label: string; count?: string }>, [selectedAgent?.terminal_state, selectedAgentId, approvals.length, eventLog.length])

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
        <AgentDashboard
          rosterAgents={rosterAgents}
          selectedAgentId={selectedAgentId}
          activeTasksByOwner={activeTasksByOwner}
          resolvedModelForAgent={resolvedModelForAgent}
          onSelectAgent={handleSelectAgent}
          onDeleteAgent={handleDeleteAgent}
          onNewAgent={() => {
            window.requestAnimationFrame(() => createAgentIdInputRef.current?.focus())
          }}
        />

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
        </div>
      </section>
    )
  }

  return (
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
  )
}
