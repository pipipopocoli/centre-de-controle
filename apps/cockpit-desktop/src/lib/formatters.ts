import type { ChatMessage, ChatMode } from './cockpitClient'
import { CLEMS_MODEL_OPTIONS, L1_MODEL_OPTIONS, L2_MODEL_OPTIONS } from './appConstants.js'

export function parseSkillsInput(raw: string): string[] {
  return [...new Set(raw.split(',').map((item) => item.trim()).filter(Boolean))]
}

export function formatSkillChip(skillId: string): string {
  return skillId.replaceAll('-', ' ')
}

export function agentInitials(name: string, agentId: string): string {
  const source = name.trim() || agentId.trim()
  const parts = source.split(/\s+/).filter(Boolean)
  if (parts.length === 0) {
    return 'AG'
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase()
  }
  return `${parts[0][0] ?? ''}${parts[1][0] ?? ''}`.toUpperCase()
}

export function formatHeartbeat(ts: string | null | undefined): string {
  if (!ts) {
    return 'heartbeat n/a'
  }
  const parsed = Date.parse(ts)
  if (Number.isNaN(parsed)) {
    return 'heartbeat unknown'
  }
  const deltaSeconds = Math.max(0, Math.floor((Date.now() - parsed) / 1000))
  if (deltaSeconds < 60) {
    return 'heartbeat now'
  }
  const deltaMinutes = Math.floor(deltaSeconds / 60)
  if (deltaMinutes < 60) {
    return `heartbeat ${deltaMinutes}m ago`
  }
  const deltaHours = Math.floor(deltaMinutes / 60)
  if (deltaHours < 24) {
    return `heartbeat ${deltaHours}h ago`
  }
  const deltaDays = Math.floor(deltaHours / 24)
  return `heartbeat ${deltaDays}d ago`
}

export function formatAgentState(phase: string | null | undefined, status: string | null | undefined): string {
  const cleanPhase = phase?.trim()
  const cleanStatus = status?.trim()
  if (cleanPhase && cleanStatus) {
    return `${cleanPhase} - ${cleanStatus}`
  }
  return cleanPhase || cleanStatus || 'state unknown'
}

export function formatCurrencyCad(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return 'n/a'
  }
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value)
}

export function projectLabel(projectId: string, projectName?: string | null): string {
  const cleanName = projectName?.trim()
  if (cleanName && cleanName.toLowerCase() !== projectId.trim().toLowerCase()) {
    return cleanName
  }

  if (projectId.trim().length === 0) {
    return 'Project'
  }

  return projectId
    .split(/[-_]/g)
    .filter(Boolean)
    .map((chunk) => `${chunk.slice(0, 1).toUpperCase()}${chunk.slice(1)}`)
    .join(' ')
}

export function modelLabel(modelId: string): string {
  const found = [...CLEMS_MODEL_OPTIONS, ...L1_MODEL_OPTIONS, ...L2_MODEL_OPTIONS].find(
    (option) => option.id === modelId,
  )
  return found ? found.label : `${modelId} (unavailable)`
}

export function isUnavailableModel(modelId: string): boolean {
  return modelLabel(modelId).endsWith('(unavailable)')
}

export function messageKindLabel(message: ChatMessage): string | null {
  const rawKind = typeof message.metadata?.kind === 'string' ? message.metadata.kind : null
  if (!rawKind) {
    return message.author === 'operator' ? 'operator' : null
  }

  const labels: Record<string, string> = {
    direct_reply: 'direct reply',
    direct_summary: 'internal summary',
    direct_fallback: 'fallback',
    conceal_reply: 'room reply',
    conceal_summary: 'room summary',
    approval_pending: 'approval pending',
    approval_spawn: 'approval spawn',
    terminal_online_ack: 'terminal ready',
  }

  return labels[rawKind] ?? rawKind.replaceAll('_', ' ')
}

export function messageChatMode(message: ChatMessage): ChatMode {
  const rawMode = typeof message.metadata?.chat_mode === 'string'
    ? message.metadata.chat_mode
    : typeof message.metadata?.mode === 'string'
      ? message.metadata.mode
      : null

  return rawMode === 'conceal_room' ? 'conceal_room' : 'direct'
}

export function messageReplySource(message: ChatMessage): string | null {
  return typeof message.metadata?.reply_source === 'string' ? message.metadata.reply_source : null
}

export function isSyntheticDirectReply(message: ChatMessage): boolean {
  if (message.author === 'operator' || messageChatMode(message) !== 'direct') {
    return false
  }
  if (messageReplySource(message) === 'fallback') {
    return true
  }
  if (typeof message.metadata?.kind === 'string' && message.metadata.kind === 'direct_fallback') {
    return true
  }
  return message.text.includes('recu en direct. Action immediate sur:')
}

export function isLegacyPendingRoomSummary(message: ChatMessage): boolean {
  if (messageChatMode(message) !== 'conceal_room') {
    return false
  }
  if (message.author !== 'clems') {
    return false
  }
  const kind = typeof message.metadata?.kind === 'string' ? message.metadata.kind : ''
  if (kind !== 'conceal_summary') {
    return false
  }
  return message.text.includes('contribution(s) en attente')
}

export function roomLeadAgentIdsFromRecords(agentRecords: { agent_id: string; level: number }[]): string[] {
  return agentRecords
    .filter((agent) => agent.agent_id !== 'clems' && agent.level === 1)
    .map((agent) => agent.agent_id)
    .sort()
}

export function preferredVoiceRecorder(): { mimeType: string; format: string } | null {
  if (typeof window === 'undefined' || typeof MediaRecorder === 'undefined') {
    return null
  }

  const candidates = [
    { mimeType: 'audio/mp4', format: 'm4a' },
    { mimeType: 'audio/ogg;codecs=opus', format: 'ogg' },
    { mimeType: 'audio/webm;codecs=opus', format: 'webm' },
  ] as const

  for (const candidate of candidates) {
    if (MediaRecorder.isTypeSupported(candidate.mimeType)) {
      return { mimeType: candidate.mimeType, format: candidate.format }
    }
  }

  return null
}

export async function blobToBase64(blob: Blob): Promise<string> {
  const buffer = await blob.arrayBuffer()
  let binary = ''
  const bytes = new Uint8Array(buffer)
  for (const value of bytes) {
    binary += String.fromCharCode(value)
  }
  return window.btoa(binary)
}

export function emptyTaskEditor() {
  return {
    title: '',
    owner: 'clems',
    phase: 'Implement',
    status: 'todo' as const,
    objective: '',
    done_definition: '',
  }
}

export function compareTasksByFreshness(left: { task_id: string; updated_at: string }, right: { task_id: string; updated_at: string }): number {
  const leftTime = Date.parse(left.updated_at)
  const rightTime = Date.parse(right.updated_at)
  if (Number.isNaN(leftTime) || Number.isNaN(rightTime)) {
    return left.task_id.localeCompare(right.task_id)
  }
  return rightTime - leftTime
}
