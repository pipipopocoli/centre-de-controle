import type { ChatMode, TaskStatus } from './lib/cockpitClient'

export type TopTab = 'pixel_home' | 'concierge_room' | 'overview' | 'pilotage' | 'docs' | 'todo' | 'model_routing'
export type WorkspaceTab = 'agent' | 'layout' | 'settings'
export type ComposerStatus = 'live' | 'reconnecting' | 'http_fallback'
export type DirectTargetMode = 'clems' | 'selected_agent'
export type WorkbenchPanel = 'chat' | 'terminal' | 'approvals' | 'events'
export type DocsPanel = 'runbook' | 'skills_library' | 'project'
export type RoomParticipantMode = 'all_active' | 'lead_only' | 'custom'
export type ProjectActionMode = 'create' | 'takeover' | null

export type FallbackDiagnostic = {
  id: string
  timestamp: string
  chatMode: ChatMode
  error: string
}

export type DirectSendPhase = 'thinking' | 'retrying' | 'degraded'

export type RosterAgentView = {
  agent_id: string
  name: string
  engine: string
  platform: string
  level: number
  lead_id: string | null
  role: string
  chat_targetable: boolean
  terminal_state: string
  terminal_session_id: string | null
  skills: string[]
  phase: string | null
  status: string | null
  current_task: string | null
  heartbeat: string | null
  scene_present: boolean
}

export type TaskEditorState = {
  title: string
  owner: string
  phase: string
  status: TaskStatus
  objective: string
  done_definition: string
}
