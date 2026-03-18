import { create } from 'zustand'
import type {
  AgentRecord,
  ApprovalRequest,
  ChatMessage,
  ExecutionMode,
  HealthzResponse,
  LlmProfile,
  PixelFeedResponse,
  ProjectCatalogEntry,
  ProjectSettings,
  ProjectSummaryResponse,
  RoadmapResponse,
  SkillLibraryEntry,
  TaskRecord,
  TakeoverStartResponse,
  WsEventEnvelope,
} from '../lib/cockpitClient'
import type { ToolActivity } from '../office/types.js'
import type {
  ComposerStatus,
  DirectSendPhase,
  DirectTargetMode,
  DocsPanel,
  FallbackDiagnostic,
  ProjectActionMode,
  RoomParticipantMode,
  TaskEditorState,
  TopTab,
  WorkbenchPanel,
  WorkspaceTab,
} from '../types.js'
import { DEFAULT_PROJECT_ID } from '../lib/appConstants.js'
import { emptyTaskEditor, messageChatMode, isSyntheticDirectReply, isLegacyPendingRoomSummary } from '../lib/formatters.js'

export interface CockpitState {
  // ── Project ────────────────────────────────────────────────
  projectId: string
  projectCatalog: ProjectCatalogEntry[]
  projectCatalogLoading: boolean
  projectSettings: ProjectSettings | null
  projectSummary: ProjectSummaryResponse | null
  projectRoadmap: RoadmapResponse | null
  selectedProjectDocId: string
  projectActionMode: ProjectActionMode
  newProjectIdDraft: string
  newProjectNameDraft: string
  newProjectRepoDraft: string
  linkedRepoDraft: string
  isCreatingProject: boolean
  isChoosingFolder: boolean
  takeoverResult: TakeoverStartResponse | null
  isRunningTakeover: boolean
  isApplyingTakeover: boolean

  // ── Agents ─────────────────────────────────────────────────
  agentRecords: AgentRecord[]
  feed: PixelFeedResponse | null
  selectedAgentId: string | null
  createAgentId: string
  createAgentName: string
  createAgentSkills: string
  isSubmitting: boolean
  agentTools: Record<number, ToolActivity[]>

  // ── Chat ───────────────────────────────────────────────────
  chatMessages: ChatMessage[]
  directChatInput: string
  roomChatInput: string
  executionMode: ExecutionMode
  directTarget: DirectTargetMode
  directSendPhase: DirectSendPhase | null
  isSendingChat: boolean
  showRoomAddMenu: boolean
  directVisibleCount: number
  roomVisibleCount: number
  roomParticipantMode: RoomParticipantMode
  roomCustomParticipants: string[]
  fallbackDiagnostics: FallbackDiagnostic[]

  // ── UI ─────────────────────────────────────────────────────
  activeTab: TopTab
  workspaceTab: WorkspaceTab
  workbenchPanel: WorkbenchPanel
  workbenchCollapsed: boolean
  docsPanel: DocsPanel
  zoom: number
  loading: boolean
  apiError: string | null
  uiNotice: string | null
  refreshTick: number
  overlayViewport: {
    viewportWidth: number
    viewportHeight: number
    panX: number
    panY: number
    dpr: number
  }
  assetsStatus: { donarg: boolean; pixelRef: boolean }

  // ── Connection ─────────────────────────────────────────────
  wsConnected: boolean
  composerStatus: ComposerStatus
  eventLog: WsEventEnvelope[]
  backendHealth: HealthzResponse | null
  lastEventAt: string | null
  lastSyncAt: string | null

  // ── Tasks ──────────────────────────────────────────────────
  tasks: TaskRecord[]
  taskEditor: TaskEditorState
  selectedTaskId: string | null
  isSavingTask: boolean

  // ── LLM ────────────────────────────────────────────────────
  llmProfile: LlmProfile | null
  profileDraft: LlmProfile | null
  isSavingProfile: boolean

  // ── Approvals ──────────────────────────────────────────────
  approvals: ApprovalRequest[]
  approvalBusy: Record<string, boolean>

  // ── Voice ──────────────────────────────────────────────────
  isRecordingVoice: boolean
  isTranscribingVoice: boolean

  // ── Skills ─────────────────────────────────────────────────
  skillsLibrary: SkillLibraryEntry[]
  skillsLibraryLoading: boolean

  // ── Derived (computed via selectors, but cached merge lives here) ──
  clockNow: Date

  // ── Actions ────────────────────────────────────────────────
  setProjectId: (id: string) => void
  setApiError: (error: string | null) => void
  setUiNotice: (notice: string | null) => void
  setLoading: (loading: boolean) => void
  setActiveTab: (tab: TopTab) => void
  setWorkspaceTab: (tab: WorkspaceTab) => void
  setWorkbenchPanel: (panel: WorkbenchPanel) => void
  setWorkbenchCollapsed: (collapsed: boolean) => void
  setDocsPanel: (panel: DocsPanel) => void
  setZoom: (zoom: number | ((prev: number) => number)) => void
  setSelectedAgentId: (id: string | null) => void
  setDirectTarget: (mode: DirectTargetMode) => void
  setDirectChatInput: (input: string | ((prev: string) => string)) => void
  setRoomChatInput: (input: string | ((prev: string) => string)) => void
  setExecutionMode: (mode: ExecutionMode) => void
  setIsSendingChat: (sending: boolean) => void
  setDirectSendPhase: (phase: DirectSendPhase | null | ((prev: DirectSendPhase | null) => DirectSendPhase | null)) => void
  setShowRoomAddMenu: (show: boolean | ((prev: boolean) => boolean)) => void
  setDirectVisibleCount: (count: number | ((prev: number) => number)) => void
  setRoomVisibleCount: (count: number | ((prev: number) => number)) => void
  setRoomParticipantMode: (mode: RoomParticipantMode) => void
  setRoomCustomParticipants: (participants: string[] | ((prev: string[]) => string[])) => void
  setFeed: (feed: PixelFeedResponse | null) => void
  setAgentRecords: (records: AgentRecord[]) => void
  setChatMessages: (messages: ChatMessage[]) => void
  mergeChatMessages: (incoming: ChatMessage[]) => void
  setWsConnected: (connected: boolean) => void
  setComposerStatus: (status: ComposerStatus) => void
  setEventLog: (updater: (prev: WsEventEnvelope[]) => WsEventEnvelope[]) => void
  setLastEventAt: (time: string | null) => void
  setLastSyncAt: (time: string | null) => void
  markSynced: () => void
  setBackendHealth: (health: HealthzResponse | null) => void
  setApprovals: (approvals: ApprovalRequest[]) => void
  setApprovalBusy: (updater: (prev: Record<string, boolean>) => Record<string, boolean>) => void
  setTasks: (tasks: TaskRecord[] | ((prev: TaskRecord[]) => TaskRecord[])) => void
  setTaskEditor: (editor: TaskEditorState | ((prev: TaskEditorState) => TaskEditorState)) => void
  setSelectedTaskId: (id: string | null | ((prev: string | null) => string | null)) => void
  setIsSavingTask: (saving: boolean) => void
  setLlmProfile: (profile: LlmProfile | null) => void
  setProfileDraft: (draft: LlmProfile | null | ((prev: LlmProfile | null) => LlmProfile | null)) => void
  setIsSavingProfile: (saving: boolean) => void
  setProjectSettings: (settings: ProjectSettings | null) => void
  setProjectSummary: (summary: ProjectSummaryResponse | null) => void
  setProjectCatalog: (catalog: ProjectCatalogEntry[]) => void
  setProjectCatalogLoading: (loading: boolean) => void
  setProjectRoadmap: (roadmap: RoadmapResponse | null) => void
  setLinkedRepoDraft: (draft: string) => void
  setSelectedProjectDocId: (id: string) => void
  setProjectActionMode: (mode: ProjectActionMode | ((prev: ProjectActionMode) => ProjectActionMode)) => void
  setNewProjectIdDraft: (draft: string) => void
  setNewProjectNameDraft: (draft: string) => void
  setNewProjectRepoDraft: (draft: string) => void
  setTakeoverResult: (result: TakeoverStartResponse | null) => void
  setIsRunningTakeover: (running: boolean) => void
  setIsApplyingTakeover: (applying: boolean) => void
  setIsChoosingFolder: (choosing: boolean) => void
  setIsCreatingProject: (creating: boolean) => void
  setIsRecordingVoice: (recording: boolean) => void
  setIsTranscribingVoice: (transcribing: boolean) => void
  setCreateAgentId: (id: string) => void
  setCreateAgentName: (name: string) => void
  setCreateAgentSkills: (skills: string) => void
  setIsSubmitting: (submitting: boolean) => void
  setAgentTools: (tools: Record<number, ToolActivity[]>) => void
  setRefreshTick: (updater: (prev: number) => number) => void
  setOverlayViewport: (viewport: CockpitState['overlayViewport'] | ((prev: CockpitState['overlayViewport']) => CockpitState['overlayViewport'])) => void
  setAssetsStatus: (status: { donarg: boolean; pixelRef: boolean }) => void
  setSkillsLibrary: (library: SkillLibraryEntry[]) => void
  setSkillsLibraryLoading: (loading: boolean) => void
  setClockNow: (now: Date) => void
  setFallbackDiagnostics: (updater: (prev: FallbackDiagnostic[]) => FallbackDiagnostic[]) => void
}

export const useCockpitStore = create<CockpitState>()((set) => ({
  // ── Project defaults ───────────────────────────────────────
  projectId: DEFAULT_PROJECT_ID,
  projectCatalog: [],
  projectCatalogLoading: false,
  projectSettings: null,
  projectSummary: null,
  projectRoadmap: null,
  selectedProjectDocId: DEFAULT_PROJECT_ID,
  projectActionMode: null,
  newProjectIdDraft: '',
  newProjectNameDraft: '',
  newProjectRepoDraft: '',
  linkedRepoDraft: '',
  isCreatingProject: false,
  isChoosingFolder: false,
  takeoverResult: null,
  isRunningTakeover: false,
  isApplyingTakeover: false,

  // ── Agent defaults ─────────────────────────────────────────
  agentRecords: [],
  feed: null,
  selectedAgentId: null,
  createAgentId: '',
  createAgentName: '',
  createAgentSkills: '',
  isSubmitting: false,
  agentTools: {},

  // ── Chat defaults ──────────────────────────────────────────
  chatMessages: [],
  directChatInput: '',
  roomChatInput: '',
  executionMode: 'chat',
  directTarget: 'clems',
  directSendPhase: null,
  isSendingChat: false,
  showRoomAddMenu: false,
  directVisibleCount: 8,
  roomVisibleCount: 8,
  roomParticipantMode: 'all_active',
  roomCustomParticipants: ['clems'],
  fallbackDiagnostics: [],

  // ── UI defaults ────────────────────────────────────────────
  activeTab: 'pixel_home',
  workspaceTab: 'agent',
  workbenchPanel: 'chat',
  workbenchCollapsed: false,
  docsPanel: 'runbook',
  zoom: 2,
  loading: true,
  apiError: null,
  uiNotice: null,
  refreshTick: 0,
  overlayViewport: { viewportWidth: 0, viewportHeight: 0, panX: 0, panY: 0, dpr: 1 },
  assetsStatus: { donarg: false, pixelRef: false },

  // ── Connection defaults ────────────────────────────────────
  wsConnected: false,
  composerStatus: 'reconnecting',
  eventLog: [],
  backendHealth: null,
  lastEventAt: null,
  lastSyncAt: null,

  // ── Task defaults ──────────────────────────────────────────
  tasks: [],
  taskEditor: emptyTaskEditor(),
  selectedTaskId: null,
  isSavingTask: false,

  // ── LLM defaults ───────────────────────────────────────────
  llmProfile: null,
  profileDraft: null,
  isSavingProfile: false,

  // ── Approval defaults ──────────────────────────────────────
  approvals: [],
  approvalBusy: {},

  // ── Voice defaults ─────────────────────────────────────────
  isRecordingVoice: false,
  isTranscribingVoice: false,

  // ── Skills defaults ────────────────────────────────────────
  skillsLibrary: [],
  skillsLibraryLoading: false,

  // ── Misc ───────────────────────────────────────────────────
  clockNow: new Date(),

  // ── Actions ────────────────────────────────────────────────
  setProjectId: (id) => set({ projectId: id }),
  setApiError: (error) => set({ apiError: error }),
  setUiNotice: (notice) => set({ uiNotice: notice }),
  setLoading: (loading) => set({ loading }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setWorkspaceTab: (tab) => set({ workspaceTab: tab }),
  setWorkbenchPanel: (panel) => set({ workbenchPanel: panel }),
  setWorkbenchCollapsed: (collapsed) => set({ workbenchCollapsed: collapsed }),
  setDocsPanel: (panel) => set({ docsPanel: panel }),
  setZoom: (zoom) => set((s) => ({ zoom: typeof zoom === 'function' ? zoom(s.zoom) : zoom })),
  setSelectedAgentId: (id) => set({ selectedAgentId: id }),
  setDirectTarget: (mode) => set({ directTarget: mode }),
  setDirectChatInput: (input) => set((s) => ({ directChatInput: typeof input === 'function' ? input(s.directChatInput) : input })),
  setRoomChatInput: (input) => set((s) => ({ roomChatInput: typeof input === 'function' ? input(s.roomChatInput) : input })),
  setExecutionMode: (mode) => set({ executionMode: mode }),
  setIsSendingChat: (sending) => set({ isSendingChat: sending }),
  setDirectSendPhase: (phase) => set((s) => ({ directSendPhase: typeof phase === 'function' ? phase(s.directSendPhase) : phase })),
  setShowRoomAddMenu: (show) => set((s) => ({ showRoomAddMenu: typeof show === 'function' ? show(s.showRoomAddMenu) : show })),
  setDirectVisibleCount: (count) => set((s) => ({ directVisibleCount: typeof count === 'function' ? count(s.directVisibleCount) : count })),
  setRoomVisibleCount: (count) => set((s) => ({ roomVisibleCount: typeof count === 'function' ? count(s.roomVisibleCount) : count })),
  setRoomParticipantMode: (mode) => set({ roomParticipantMode: mode }),
  setRoomCustomParticipants: (p) => set((s) => ({ roomCustomParticipants: typeof p === 'function' ? p(s.roomCustomParticipants) : p })),
  setFeed: (feed) => set({ feed }),
  setAgentRecords: (records) => set({ agentRecords: records }),
  setChatMessages: (messages) => set({ chatMessages: messages }),

  mergeChatMessages: (incoming) => set((state) => {
    if (incoming.length === 0) {
      return state
    }
    const byId = new Map<string, ChatMessage>()
    for (const row of state.chatMessages) {
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
    const sorted = [...byId.values()].sort((a, b) => {
      if (a.timestamp === b.timestamp) {
        return a.message_id.localeCompare(b.message_id)
      }
      return a.timestamp.localeCompare(b.timestamp)
    })
    return { chatMessages: sorted }
  }),

  setWsConnected: (connected) => set({ wsConnected: connected }),
  setComposerStatus: (status) => set({ composerStatus: status }),
  setEventLog: (updater) => set((s) => ({ eventLog: updater(s.eventLog) })),
  setLastEventAt: (time) => set({ lastEventAt: time }),
  setLastSyncAt: (time) => set({ lastSyncAt: time }),
  markSynced: () => set({ lastSyncAt: new Date().toISOString() }),
  setBackendHealth: (health) => set({ backendHealth: health }),
  setApprovals: (approvals) => set({ approvals }),
  setApprovalBusy: (updater) => set((s) => ({ approvalBusy: updater(s.approvalBusy) })),
  setTasks: (tasks) => set((s) => ({ tasks: typeof tasks === 'function' ? tasks(s.tasks) : tasks })),
  setTaskEditor: (editor) => set((s) => ({ taskEditor: typeof editor === 'function' ? editor(s.taskEditor) : editor })),
  setSelectedTaskId: (id) => set((s) => ({ selectedTaskId: typeof id === 'function' ? id(s.selectedTaskId) : id })),
  setIsSavingTask: (saving) => set({ isSavingTask: saving }),
  setLlmProfile: (profile) => set({ llmProfile: profile }),
  setProfileDraft: (draft) => set((s) => ({ profileDraft: typeof draft === 'function' ? draft(s.profileDraft) : draft })),
  setIsSavingProfile: (saving) => set({ isSavingProfile: saving }),
  setProjectSettings: (settings) => set({ projectSettings: settings }),
  setProjectSummary: (summary) => set({ projectSummary: summary }),
  setProjectCatalog: (catalog) => set({ projectCatalog: catalog }),
  setProjectCatalogLoading: (loading) => set({ projectCatalogLoading: loading }),
  setProjectRoadmap: (roadmap) => set({ projectRoadmap: roadmap }),
  setLinkedRepoDraft: (draft) => set({ linkedRepoDraft: draft }),
  setSelectedProjectDocId: (id) => set({ selectedProjectDocId: id }),
  setProjectActionMode: (mode) => set((s) => ({ projectActionMode: typeof mode === 'function' ? mode(s.projectActionMode) : mode })),
  setNewProjectIdDraft: (draft) => set({ newProjectIdDraft: draft }),
  setNewProjectNameDraft: (draft) => set({ newProjectNameDraft: draft }),
  setNewProjectRepoDraft: (draft) => set({ newProjectRepoDraft: draft }),
  setTakeoverResult: (result) => set({ takeoverResult: result }),
  setIsRunningTakeover: (running) => set({ isRunningTakeover: running }),
  setIsApplyingTakeover: (applying) => set({ isApplyingTakeover: applying }),
  setIsChoosingFolder: (choosing) => set({ isChoosingFolder: choosing }),
  setIsCreatingProject: (creating) => set({ isCreatingProject: creating }),
  setIsRecordingVoice: (recording) => set({ isRecordingVoice: recording }),
  setIsTranscribingVoice: (transcribing) => set({ isTranscribingVoice: transcribing }),
  setCreateAgentId: (id) => set({ createAgentId: id }),
  setCreateAgentName: (name) => set({ createAgentName: name }),
  setCreateAgentSkills: (skills) => set({ createAgentSkills: skills }),
  setIsSubmitting: (submitting) => set({ isSubmitting: submitting }),
  setAgentTools: (tools) => set({ agentTools: tools }),
  setRefreshTick: (updater) => set((s) => ({ refreshTick: updater(s.refreshTick) })),
  setOverlayViewport: (viewport) => set((s) => ({ overlayViewport: typeof viewport === 'function' ? viewport(s.overlayViewport) : viewport })),
  setAssetsStatus: (status) => set({ assetsStatus: status }),
  setSkillsLibrary: (library) => set({ skillsLibrary: library }),
  setSkillsLibraryLoading: (loading) => set({ skillsLibraryLoading: loading }),
  setClockNow: (now) => set({ clockNow: now }),
  setFallbackDiagnostics: (updater) => set((s) => ({ fallbackDiagnostics: updater(s.fallbackDiagnostics) })),
}))

// ── Selectors ──────────────────────────────────────────────────
export const selectOperatorChatMessages = (state: CockpitState) =>
  state.chatMessages.filter((message) => message.visibility !== 'internal')

export const selectDirectChatMessages = (state: CockpitState) =>
  selectOperatorChatMessages(state).filter(
    (message) => messageChatMode(message) === 'direct' && !isSyntheticDirectReply(message),
  )

export const selectConciergeChatMessages = (state: CockpitState) =>
  selectOperatorChatMessages(state).filter(
    (message) => messageChatMode(message) === 'conceal_room' && !isLegacyPendingRoomSummary(message),
  )

export const selectInternalConciergeMessages = (state: CockpitState) =>
  state.chatMessages.filter(
    (message) => message.visibility === 'internal' && messageChatMode(message) === 'conceal_room',
  )

export const selectActiveChatMode = (state: CockpitState) =>
  state.activeTab === 'concierge_room' ? 'conceal_room' as const : 'direct' as const
