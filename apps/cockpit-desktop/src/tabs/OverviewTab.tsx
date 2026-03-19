import { memo, useMemo } from 'react'
import {
  useCockpitStore,
  useConciergeChatMessages,
} from '../store/index.js'
import type { HealthzResponse, TaskStatus } from '../lib/cockpitClient'
import type { RosterAgentView } from '../types.js'
import { projectLabel, formatCurrencyCad, compareTasksByFreshness } from '../lib/formatters.js'
import { STATUS_ORDER, STATUS_LABELS } from '../lib/appConstants.js'
import { getApiUrl } from '../lib/cockpitClient'

export interface OverviewTabProps {
  composerLabel: string
  backendHealth: HealthzResponse | null
  directTargetLabel: string
  selectedAgent: RosterAgentView | null
  lastEventAt: string | null
}

export const OverviewTab = memo(function OverviewTab({
  composerLabel,
  backendHealth,
  directTargetLabel,
  selectedAgent,
  lastEventAt,
}: OverviewTabProps) {
  const feed = useCockpitStore((state) => state.feed)
  const tasks = useCockpitStore((state) => state.tasks)
  const approvals = useCockpitStore((state) => state.approvals)
  const projectId = useCockpitStore((state) => state.projectId)
  const projectSettings = useCockpitStore((state) => state.projectSettings)
  const projectSummary = useCockpitStore((state) => state.projectSummary)
  const projectRoadmap = useCockpitStore((state) => state.projectRoadmap)
  const agentRecords = useCockpitStore((state) => state.agentRecords)
  const assetsStatus = useCockpitStore((state) => state.assetsStatus)
  const conciergeChatMessages = useConciergeChatMessages()

  const agentsTotal = feed?.agents.length ?? 0
  const runningTerminals = feed?.terminals_alive ?? 0
  const queueDepth = feed?.queue_depth ?? 0

  const openRouterHealth = backendHealth?.openrouter ?? null

  const rosterAgents = useMemo<RosterAgentView[]>(() => {
    const recordsByAgentId = new Map(agentRecords.map((agent) => [agent.agent_id, agent]))
    const feedByAgentId = new Map((feed?.agents ?? []).map((agent) => [agent.agent_id, agent]))
    const mergedIds = [...new Set([...Array.from(recordsByAgentId.keys()), ...Array.from(feedByAgentId.keys())])]
    return mergedIds
      .map((agentId) => {
        const record = recordsByAgentId.get(agentId)
        const feedAgent = feedByAgentId.get(agentId)
        if (!record && !feedAgent) return null
        return {
          agent_id: agentId,
          name: feedAgent?.name ?? record?.name ?? agentId,
          engine: record?.engine ?? 'openrouter',
          platform: record?.platform ?? 'openrouter',
          level: feedAgent?.level ?? record?.level ?? 2,
          lead_id: feedAgent?.lead_id ?? record?.lead_id ?? null,
          role: feedAgent?.role ?? record?.role ?? 'specialist',
          chat_targetable: feedAgent?.chat_targetable ?? agentId === 'clems',
          terminal_state: feedAgent?.terminal_state ?? 'offline',
          terminal_session_id: feedAgent?.terminal_session_id ?? null,
          skills: record?.skills ?? [],
          phase: record?.phase ?? null,
          status: record?.status ?? null,
          current_task: record?.current_task ?? null,
          heartbeat: record?.heartbeat ?? null,
          scene_present: Boolean(feedAgent),
        }
      })
      .filter((agent): agent is RosterAgentView => agent !== null)
  }, [agentRecords, feed])

  const chatReadyCount = rosterAgents.filter((agent) => agent.chat_targetable).length
  const leadsCount = rosterAgents.filter((agent) => agent.level === 1).length

  const taskCounts = STATUS_ORDER.reduce<Record<TaskStatus, number>>(
    (accumulator, status) => ({
      ...accumulator,
      [status]: tasks.filter((task) => task.status === status).length,
    }),
    { todo: 0, in_progress: 0, blocked: 0, done: 0 },
  )

  const linkedRepoLabel = projectSummary?.linked_repo_path ?? projectSettings?.linked_repo_path ?? 'not linked'
  const currentProjectLabel = projectLabel(projectId, projectSettings?.project_name ?? projectId)
  const projectPhase = projectSummary?.phase ?? 'unknown'
  const projectObjective = projectSummary?.objective ?? 'No objective set yet.'
  const roadmapNow = projectSummary?.roadmap_now ?? projectRoadmap?.sections.now ?? []
  const roadmapNext = projectSummary?.roadmap_next ?? projectRoadmap?.sections.next ?? []
  const projectTaskCounts = projectSummary?.open_task_counts
  const monthlyCostLabel = formatCurrencyCad(projectSummary?.monthly_cost_estimate_cad)
  const costEventsLabel = String(projectSummary?.cost_events_this_month ?? 0)
  const modelUsageSummary = projectSummary?.model_usage_summary ?? []
  const recentTasks = [...tasks].sort(compareTasksByFreshness).slice(0, 5)
  const latestRoom = conciergeChatMessages.slice(-8).reverse()

  const quickStatus = [
    { label: 'Backend', value: backendHealth?.status ?? 'unknown' },
    { label: 'OpenRouter', value: openRouterHealth?.status ?? 'unknown' },
    { label: 'WS', value: composerLabel },
    { label: 'Agents', value: String(agentsTotal) },
    { label: 'Terminals live', value: String(runningTerminals) },
    { label: 'Queue', value: String(queueDepth) },
    {
      label: 'Tasks open',
      value: String(
        projectTaskCounts
          ? projectTaskCounts.todo + projectTaskCounts.in_progress + projectTaskCounts.blocked
          : taskCounts.todo + taskCounts.in_progress + taskCounts.blocked,
      ),
    },
  ]

  const buildStamp = backendHealth?.build_sha ? backendHealth.build_sha.slice(0, 12) : 'unknown'

  return (
    <section className="secondary-tab panel">
      <div className="secondary-header">
        <h2>Overview</h2>
        <span className="hint">project heartbeat, tasks, and runtime truth</span>
      </div>
      <div className="secondary-hero-grid">
        <article className="overview-hero-card">
          <span className="overview-hero-label">Runtime</span>
          <strong>{backendHealth?.status ?? 'unknown'}</strong>
          <p>ws {composerLabel} - build {buildStamp}</p>
        </article>
        <article className="overview-hero-card">
          <span className="overview-hero-label">Agents live</span>
          <strong>{agentsTotal}</strong>
          <p>{chatReadyCount} chat ready - {runningTerminals} terminals live</p>
        </article>
        <article className="overview-hero-card">
          <span className="overview-hero-label">Execution load</span>
          <strong>{taskCounts.todo + taskCounts.in_progress + taskCounts.blocked}</strong>
          <p>{approvals.length} approvals - queue {queueDepth}</p>
        </article>
        <article className="overview-hero-card">
          <span className="overview-hero-label">Credits this month</span>
          <strong>{monthlyCostLabel}</strong>
          <p>{costEventsLabel} cost events tracked</p>
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
          <h3>Project summary</h3>
          <ul className="data-list">
            <li>
              <span>Project</span>
              <strong>{currentProjectLabel}</strong>
            </li>
            <li>
              <span>Phase</span>
              <strong>{projectPhase}</strong>
            </li>
            <li>
              <span>Objective</span>
              <strong>{projectObjective}</strong>
            </li>
            <li>
              <span>Linked repo</span>
              <strong>{linkedRepoLabel}</strong>
            </li>
            <li>
              <span>Open tasks</span>
              <strong>
                {projectTaskCounts
                  ? projectTaskCounts.todo + projectTaskCounts.in_progress + projectTaskCounts.blocked
                  : taskCounts.todo + taskCounts.in_progress + taskCounts.blocked}
              </strong>
            </li>
          </ul>
        </section>
        <section className="secondary-card">
          <h3>Task board snapshot</h3>
          <ul className="data-list">
            {STATUS_ORDER.map((status) => (
              <li key={status}>
                <span>{STATUS_LABELS[status]}</span>
              <strong>{projectTaskCounts ? projectTaskCounts[status] : taskCounts[status]}</strong>
              </li>
            ))}
          </ul>
        </section>
        <section className="secondary-card">
          <h3>Project actions</h3>
          <div className="events-log">
            <p>Project creation and takeover now live in Le Conseil.</p>
            <p>Use the pinned Project actions card there to create a greenfield project or run repo takeover.</p>
            <p>Overview stays read-only for runtime, costs, roadmap, and task visibility.</p>
          </div>
        </section>
        <section className="secondary-card">
          <h3>Operational focus</h3>
          <ul className="overview-focus-list">
            <li>
              <span>Direct target</span>
              <strong>{directTargetLabel}</strong>
            </li>
            <li>
              <span>Selected agent</span>
              <strong>{selectedAgent ? `@${selectedAgent.agent_id}` : 'none'}</strong>
            </li>
            <li>
              <span>L1 leads</span>
              <strong>{leadsCount}</strong>
            </li>
            <li>
              <span>Assets loaded</span>
              <strong>{assetsStatus.donarg && assetsStatus.pixelRef ? 'yes' : 'partial'}</strong>
            </li>
          </ul>
        </section>
        <section className="secondary-card">
          <h3>Roadmap snapshot</h3>
          <div className="project-snapshot-grid">
            <div>
              <h4>Now</h4>
              <ul className="simple-list">
                {(roadmapNow.length > 0 ? roadmapNow : ['No current roadmap items']).map((item) => (
                  <li key={`now-${item}`}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4>Next</h4>
              <ul className="simple-list">
                {(roadmapNext.length > 0 ? roadmapNext : ['No next roadmap items']).map((item) => (
                  <li key={`next-${item}`}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>
        <section className="secondary-card">
          <h3>Recent task movement</h3>
          <div className="events-log">
            {recentTasks.length === 0 ? (
              <p>No tasks yet.</p>
            ) : (
              recentTasks.map((task) => (
                <p key={task.task_id}>
                  <strong>{task.title}</strong> - {STATUS_LABELS[task.status]} - @{task.owner}
                </p>
              ))
            )}
          </div>
        </section>
        <section className="secondary-card">
          <h3>Latest operator touch</h3>
          <div className="events-log">
            {latestRoom.length === 0 ? (
              <p>No board messages yet.</p>
            ) : (
              latestRoom.slice(0, 6).map((message) => (
                <p key={message.message_id}>
                  <strong>@{message.author}</strong> {message.text}
                </p>
              ))
            )}
          </div>
        </section>
        <section className="secondary-card">
          <h3>Model spend</h3>
          <div className="events-log">
            {modelUsageSummary.length === 0 ? (
              <p>No model usage tracked yet.</p>
            ) : (
              modelUsageSummary.map((entry) => (
                <p key={entry.model}>
                  <strong>{entry.model}</strong> - {formatCurrencyCad(entry.cost_cad)} - {entry.events} events
                </p>
              ))
            )}
          </div>
        </section>
      </div>
    </section>
  )
})
