import type { RosterAgentView } from '../types.js'
import {
  agentInitials,
  formatAgentState,
} from '../lib/formatters.js'

const AGENT_PALETTE = [
  'var(--accent)',
  'var(--ok)',
  'var(--warn)',
  'var(--accent-2)',
  '#bc8cff',
  '#f778ba',
  '#79c0ff',
  '#7ee787',
] as const

const PHASE_STEPS = ['Plan', 'Implement', 'Test', 'Review', 'Ship'] as const

function statusColor(status: string | null): string {
  if (!status) return 'var(--fg-2)'
  const lower = status.toLowerCase()
  if (lower.includes('execut') || lower.includes('running') || lower.includes('active')) return 'var(--ok)'
  if (lower.includes('idle') || lower.includes('wait')) return 'var(--accent)'
  if (lower.includes('plan')) return 'var(--warn)'
  if (lower.includes('block') || lower.includes('error') || lower.includes('fail')) return 'var(--err, #f85149)'
  return 'var(--fg-2)'
}

function heartbeatLabel(ts: string | null): string {
  if (!ts) return 'offline'
  const parsed = Date.parse(ts)
  if (Number.isNaN(parsed)) return 'offline'
  const delta = Math.max(0, Math.floor((Date.now() - parsed) / 1000))
  if (delta < 60) return 'now'
  const mins = Math.floor(delta / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return 'offline'
}

function avatarColor(agentId: string): string {
  let hash = 0
  for (let i = 0; i < agentId.length; i++) {
    hash = (hash * 31 + agentId.charCodeAt(i)) | 0
  }
  return AGENT_PALETTE[Math.abs(hash) % AGENT_PALETTE.length]
}

function phaseIndex(phase: string | null): number {
  if (!phase) return -1
  const lower = phase.toLowerCase()
  for (let i = 0; i < PHASE_STEPS.length; i++) {
    if (lower.includes(PHASE_STEPS[i].toLowerCase())) return i
  }
  return -1
}

export interface AgentCardProps {
  agent: RosterAgentView
  isSelected: boolean
  resolvedModel: string
  activeTask: string | null
  onSelect: (agentId: string) => void
  onDelete: (agentId: string) => Promise<void>
}

export function AgentCard({
  agent,
  isSelected,
  resolvedModel,
  activeTask,
  onSelect,
  onDelete,
}: AgentCardProps) {
  const initials = agentInitials(agent.name, agent.agent_id)
  const color = avatarColor(agent.agent_id)
  const stateLabel = formatAgentState(agent.phase, agent.status)
  const heartbeat = heartbeatLabel(agent.heartbeat)
  const currentPhaseIdx = phaseIndex(agent.phase)
  const taskLabel = agent.current_task ?? activeTask ?? null

  return (
    <article
      className={`ad-card level-${agent.level}${isSelected ? ' ad-card-active' : ''}`}
      onClick={() => onSelect(agent.agent_id)}
    >
      <div className="ad-card-header">
        <div className="ad-card-identity">
          <div className="ad-card-avatar" style={{ background: color }}>
            {initials}
          </div>
          <div className="ad-card-names">
            <span className="ad-card-name">{agent.name || agent.agent_id}</span>
            <span className="ad-card-handle">@{agent.agent_id}</span>
          </div>
        </div>
        <div className="ad-card-badges">
          <span className="ad-card-level">L{agent.level}</span>
          <span className="ad-card-role">{agent.role || 'agent'}</span>
        </div>
      </div>

      <div className="ad-card-status-row">
        <span
          className="ad-card-status-dot"
          style={{ background: statusColor(agent.status) }}
        />
        <span className="ad-card-status-text">{stateLabel}</span>
      </div>

      {currentPhaseIdx >= 0 && (
        <div className="ad-card-progress">
          <div className="ad-card-phase-labels">
            {PHASE_STEPS.map((step, i) => (
              <span
                key={step}
                className={`ad-phase-step${i <= currentPhaseIdx ? ' ad-phase-done' : ''}`}
              >
                {step}
              </span>
            ))}
          </div>
          <div className="ad-card-progress-bar">
            <div
              className="ad-card-progress-fill"
              style={{ width: `${((currentPhaseIdx + 1) / PHASE_STEPS.length) * 100}%` }}
            />
          </div>
        </div>
      )}

      {taskLabel && (
        <p className="ad-card-task" title={taskLabel}>
          {taskLabel}
        </p>
      )}

      <div className="ad-card-footer">
        <span className="ad-card-heartbeat">{heartbeat}</span>
        <span className="ad-card-model">{resolvedModel}</span>
        <span className={`ad-card-indicator ${agent.terminal_state === 'running' ? 'on' : 'off'}`}>
          term
        </span>
        <span className={`ad-card-indicator ${agent.chat_targetable ? 'on' : 'off'}`}>
          chat
        </span>
        {agent.agent_id !== 'clems' && (
          <button
            className="ad-card-delete"
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              void onDelete(agent.agent_id)
            }}
          >
            Remove
          </button>
        )}
      </div>
    </article>
  )
}
