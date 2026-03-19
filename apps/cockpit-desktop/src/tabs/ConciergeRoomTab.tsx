import { memo } from 'react'
import type { RefObject } from 'react'
import {
  useCockpitStore,
  useConciergeChatMessages,
} from '../store/index.js'
import type { ChatMessage, ExecutionMode, LlmProfile, TaskStatus, TakeoverStartResponse } from '../lib/cockpitClient'
import type { ComposerStatus, ProjectActionMode, RoomParticipantMode, RosterAgentView, TopTab } from '../types.js'
import { messageKindLabel } from '../lib/formatters.js'

export interface ConciergeRoomTabProps {
  composerStatus: ComposerStatus
  composerLabel: string
  roomChatInput: string
  executionMode: ExecutionMode
  showRoomAddMenu: boolean
  roomVisibleCount: number
  roomParticipantMode: RoomParticipantMode
  roomCustomParticipants: string[]
  roomCandidateAgents: RosterAgentView[]
  effectiveRoomParticipantIds: string[]
  roomParticipantLabel: string
  roomDispatchContext: Record<string, unknown>
  agentsTotal: number
  chatReadyCount: number
  taskCounts: Record<TaskStatus, number>
  selectedAgent: RosterAgentView | null
  directTargetLabel: string
  lastEventAt: string | null
  currentProjectLabel: string
  linkedRepoLabel: string
  projectActionMode: ProjectActionMode
  newProjectIdDraft: string
  newProjectNameDraft: string
  newProjectRepoDraft: string
  linkedRepoDraft: string
  isChoosingFolder: boolean
  isCreatingProject: boolean
  isRunningTakeover: boolean
  isApplyingTakeover: boolean
  isSendingChat: boolean
  isRecordingVoice: boolean
  isTranscribingVoice: boolean
  takeoverResult: TakeoverStartResponse | null
  profileDraft: LlmProfile | null
  visibleConciergeMessages: ChatMessage[]
  visibleInternalConciergeMessages: ChatMessage[]
  roomChatLogRef: RefObject<HTMLDivElement | null>
  roomStickToBottomRef: RefObject<boolean>
  resolvedModelForAgent: (agent: RosterAgentView) => string
  setRoomChatInput: (value: string | ((previous: string) => string)) => void
  setExecutionMode: (value: ExecutionMode) => void
  setShowRoomAddMenu: (value: boolean | ((previous: boolean) => boolean)) => void
  setRoomVisibleCount: (value: number | ((previous: number) => number)) => void
  setRoomParticipantMode: (value: RoomParticipantMode) => void
  setRoomCustomParticipants: (value: string[] | ((previous: string[]) => string[])) => void
  setProjectActionMode: (value: ProjectActionMode | ((previous: ProjectActionMode) => ProjectActionMode)) => void
  setNewProjectIdDraft: (value: string) => void
  setNewProjectNameDraft: (value: string) => void
  setNewProjectRepoDraft: (value: string) => void
  setLinkedRepoDraft: (value: string) => void
  setActiveTab: (value: TopTab) => void
  setSelectedTaskId: (value: string | null | ((previous: string | null) => string | null)) => void
  addMention: (mention: string, surface: 'direct' | 'room') => void
  handleSendChat: (options: { chatMode: 'conceal_room'; contextRef: Record<string, unknown> }) => Promise<void>
  handleToggleVoiceRecording: () => Promise<void>
  handleChooseRepoFolder: (target: 'takeover' | 'create') => Promise<void>
  handleCreateProject: () => Promise<void>
  handleRunTakeover: () => Promise<void>
  handleSaveProjectLink: () => Promise<void>
  handleApplyTakeoverRoadmap: () => Promise<void>
  handleApplyTakeoverTasks: () => Promise<void>
  handleLaunchTakeoverPlan: () => Promise<void>
}

export const ConciergeRoomTab = memo(function ConciergeRoomTab({
  composerStatus,
  composerLabel,
  roomChatInput,
  executionMode,
  showRoomAddMenu,
  roomVisibleCount,
  roomParticipantMode,
  roomCustomParticipants,
  roomCandidateAgents,
  effectiveRoomParticipantIds,
  roomParticipantLabel,
  roomDispatchContext,
  agentsTotal,
  chatReadyCount,
  taskCounts,
  selectedAgent,
  directTargetLabel,
  lastEventAt,
  currentProjectLabel,
  linkedRepoLabel,
  projectActionMode,
  newProjectIdDraft,
  newProjectNameDraft,
  newProjectRepoDraft,
  linkedRepoDraft,
  isChoosingFolder,
  isCreatingProject,
  isRunningTakeover,
  isApplyingTakeover,
  isSendingChat,
  isRecordingVoice,
  isTranscribingVoice,
  takeoverResult,
  visibleConciergeMessages,
  visibleInternalConciergeMessages,
  roomChatLogRef,
  roomStickToBottomRef,
  resolvedModelForAgent,
  setRoomChatInput,
  setExecutionMode,
  setShowRoomAddMenu,
  setRoomVisibleCount,
  setRoomParticipantMode,
  setRoomCustomParticipants,
  setProjectActionMode,
  setNewProjectIdDraft,
  setNewProjectNameDraft,
  setNewProjectRepoDraft,
  setLinkedRepoDraft,
  setActiveTab,
  addMention,
  handleSendChat,
  handleToggleVoiceRecording,
  handleChooseRepoFolder,
  handleCreateProject,
  handleRunTakeover,
  handleSaveProjectLink,
  handleApplyTakeoverRoadmap,
  handleApplyTakeoverTasks,
  handleLaunchTakeoverPlan,
}: ConciergeRoomTabProps) {
  const conciergeChatMessages = useConciergeChatMessages()
  const approvals = useCockpitStore((state) => state.approvals)

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
})
