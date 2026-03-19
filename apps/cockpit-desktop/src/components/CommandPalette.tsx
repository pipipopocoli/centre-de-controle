import { useCallback, useMemo, useRef, useState } from 'react'
import { useCockpitStore } from '../store/index.js'
import type { TopTab } from '../types.js'

interface CommandItem {
  id: string
  label: string
  shortcut?: string
  action: () => void
}

interface CommandPaletteProps {
  open: boolean
  onClose: () => void
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  if (!open) return null
  return <CommandPaletteInner onClose={onClose} />
}

function CommandPaletteInner({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const setActiveTab = useCockpitStore((s) => s.setActiveTab)
  const agentRecords = useCockpitStore((s) => s.agentRecords)
  const setSelectedAgentId = useCockpitStore((s) => s.setSelectedAgentId)
  const setWorkbenchPanel = useCockpitStore((s) => s.setWorkbenchPanel)

  const commands = useMemo<CommandItem[]>(() => {
    const tabItems: CommandItem[] = [
      { id: 'tab:pixel_home', label: 'Switch to Pixel Home', shortcut: '\u2318+1', action: () => { setActiveTab('pixel_home' as TopTab); onClose() } },
      { id: 'tab:concierge_room', label: 'Switch to Le Conseil', shortcut: '\u2318+2', action: () => { setActiveTab('concierge_room' as TopTab); onClose() } },
      { id: 'tab:overview', label: 'Switch to Overview', shortcut: '\u2318+3', action: () => { setActiveTab('overview' as TopTab); onClose() } },
      { id: 'tab:pilotage', label: 'Switch to Pilotage', shortcut: '\u2318+4', action: () => { setActiveTab('pilotage' as TopTab); onClose() } },
      { id: 'tab:docs', label: 'Switch to Docs', shortcut: '\u2318+5', action: () => { setActiveTab('docs' as TopTab); onClose() } },
      { id: 'tab:todo', label: 'Switch to To Do', shortcut: '\u2318+6', action: () => { setActiveTab('todo' as TopTab); onClose() } },
      { id: 'tab:model_routing', label: 'Switch to Model Routing', shortcut: '\u2318+7', action: () => { setActiveTab('model_routing' as TopTab); onClose() } },
    ]

    const agentItems: CommandItem[] = agentRecords.map((agent) => ({
      id: `agent:${agent.agent_id}`,
      label: `Select agent: ${agent.name ?? agent.agent_id}`,
      action: () => { setSelectedAgentId(agent.agent_id); onClose() },
    }))

    const actionItems: CommandItem[] = [
      { id: 'action:terminal', label: 'Open Terminal panel', action: () => { setWorkbenchPanel('terminal'); onClose() } },
      { id: 'action:chat', label: 'Open Chat panel', action: () => { setWorkbenchPanel('chat'); onClose() } },
      { id: 'action:approvals', label: 'Open Approvals panel', action: () => { setWorkbenchPanel('approvals'); onClose() } },
      { id: 'action:events', label: 'Open Events panel', action: () => { setWorkbenchPanel('events'); onClose() } },
    ]

    return [...tabItems, ...agentItems, ...actionItems]
  }, [agentRecords, onClose, setActiveTab, setSelectedAgentId, setWorkbenchPanel])

  const filtered = useMemo(() => {
    if (!query.trim()) return commands
    const lower = query.toLowerCase()
    return commands.filter((cmd) => cmd.label.toLowerCase().includes(lower))
  }, [commands, query])

  const clampedIndex = Math.min(selectedIndex, Math.max(filtered.length - 1, 0))

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, filtered.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, 0))
      } else if (e.key === 'Enter') {
        e.preventDefault()
        const item = filtered[clampedIndex]
        if (item) item.action()
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    },
    [filtered, clampedIndex, onClose],
  )

  return (
    <div className="command-palette-overlay" onClick={onClose}>
      <div className="command-palette" onClick={(e) => e.stopPropagation()} onKeyDown={handleKeyDown}>
        <input
          ref={inputRef}
          className="command-palette-input"
          type="text"
          placeholder="Type a command..."
          value={query}
          onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0) }}
          autoFocus
        />
        <div className="command-palette-results">
          {filtered.map((item, index) => (
            <div
              key={item.id}
              className={`command-palette-item ${index === clampedIndex ? 'selected' : ''}`}
              onClick={() => item.action()}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <span className="command-palette-item-label">{item.label}</span>
              {item.shortcut ? <span className="command-palette-item-shortcut">{item.shortcut}</span> : null}
            </div>
          ))}
          {filtered.length === 0 ? (
            <div className="command-palette-item command-palette-empty">No matching commands</div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
