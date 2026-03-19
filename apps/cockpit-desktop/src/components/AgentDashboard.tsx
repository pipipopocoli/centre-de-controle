import { useState, useMemo } from 'react'
import type { RosterAgentView } from '../types.js'
import { AgentCard } from './AgentCard.js'

type FilterKey = 'all' | 'l0' | 'l1' | 'l2' | 'active' | 'idle' | 'blocked'

const FILTERS: Array<{ key: FilterKey; label: string }> = [
  { key: 'all', label: 'All' },
  { key: 'l0', label: 'L0' },
  { key: 'l1', label: 'L1' },
  { key: 'l2', label: 'L2' },
  { key: 'active', label: 'Active' },
  { key: 'idle', label: 'Idle' },
  { key: 'blocked', label: 'Blocked' },
]

function matchesFilter(agent: RosterAgentView, filter: FilterKey): boolean {
  switch (filter) {
    case 'all':
      return true
    case 'l0':
      return agent.level === 0
    case 'l1':
      return agent.level === 1
    case 'l2':
      return agent.level === 2
    case 'active': {
      const s = (agent.status ?? '').toLowerCase()
      return s.includes('execut') || s.includes('running') || s.includes('active') || agent.terminal_state === 'running'
    }
    case 'idle': {
      const s = (agent.status ?? '').toLowerCase()
      return s.includes('idle') || s.includes('wait') || (!s.includes('execut') && !s.includes('running') && !s.includes('block') && !s.includes('error'))
    }
    case 'blocked': {
      const s = (agent.status ?? '').toLowerCase()
      return s.includes('block') || s.includes('error') || s.includes('fail')
    }
    default:
      return true
  }
}

export interface AgentDashboardProps {
  rosterAgents: RosterAgentView[]
  selectedAgentId: string | null
  activeTasksByOwner: Map<string, { title: string }>
  resolvedModelForAgent: (agent: RosterAgentView) => string
  onSelectAgent: (agentId: string) => void
  onDeleteAgent: (agentId: string) => Promise<void>
  onNewAgent: () => void
}

export function AgentDashboard({
  rosterAgents,
  selectedAgentId,
  activeTasksByOwner,
  resolvedModelForAgent,
  onSelectAgent,
  onDeleteAgent,
  onNewAgent,
}: AgentDashboardProps) {
  const [filter, setFilter] = useState<FilterKey>('all')

  const filtered = useMemo(
    () => rosterAgents.filter((a) => matchesFilter(a, filter)),
    [rosterAgents, filter],
  )

  return (
    <div className="agent-dashboard">
      <div className="agent-dashboard-header">
        <div className="agent-dashboard-title-row">
          <h2>Agent Fleet</h2>
          <span className="agent-dashboard-count">{filtered.length}</span>
        </div>
        <div className="agent-dashboard-actions">
          <div className="agent-dashboard-filters">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                className={`ad-filter-btn${filter === f.key ? ' active' : ''}`}
                type="button"
                onClick={() => setFilter(f.key)}
              >
                {f.label}
              </button>
            ))}
          </div>
          <button className="ad-new-agent-btn" type="button" onClick={onNewAgent}>
            + New Agent
          </button>
        </div>
      </div>

      <div className="agent-dashboard-grid">
        {filtered.length === 0 ? (
          <div className="agent-dashboard-empty">
            <p>No agents match the current filter.</p>
          </div>
        ) : (
          filtered.map((agent) => (
            <AgentCard
              key={agent.agent_id}
              agent={agent}
              isSelected={selectedAgentId === agent.agent_id}
              resolvedModel={resolvedModelForAgent(agent)}
              activeTask={activeTasksByOwner.get(agent.agent_id)?.title ?? null}
              onSelect={onSelectAgent}
              onDelete={onDeleteAgent}
            />
          ))
        )}
      </div>
    </div>
  )
}
