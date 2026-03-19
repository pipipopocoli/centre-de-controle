import { useMemo } from 'react'
import { useCockpitStore } from '../store/index.js'
import type { HealthzResponse, ProjectCatalogEntry } from '../lib/cockpitClient'
import { projectLabel, formatCurrencyCad } from '../lib/formatters.js'

export interface DocsTabProps {
  backendHealth: HealthzResponse | null
}

export function DocsTab({
  backendHealth,
}: DocsTabProps) {
  const projectId = useCockpitStore((state) => state.projectId)
  const projectSettings = useCockpitStore((state) => state.projectSettings)
  const projectSummary = useCockpitStore((state) => state.projectSummary)
  const projectRoadmap = useCockpitStore((state) => state.projectRoadmap)
  const projectCatalog = useCockpitStore((state) => state.projectCatalog)
  const projectCatalogLoading = useCockpitStore((state) => state.projectCatalogLoading)
  const selectedProjectDocId = useCockpitStore((state) => state.selectedProjectDocId)
  const setSelectedProjectDocId = useCockpitStore((state) => state.setSelectedProjectDocId)
  const docsPanel = useCockpitStore((state) => state.docsPanel)
  const setDocsPanel = useCockpitStore((state) => state.setDocsPanel)
  const skillsLibrary = useCockpitStore((state) => state.skillsLibrary)
  const skillsLibraryLoading = useCockpitStore((state) => state.skillsLibraryLoading)

  const linkedRepoLabel = projectSummary?.linked_repo_path ?? projectSettings?.linked_repo_path ?? 'not linked'
  const projectPhase = projectSummary?.phase ?? 'unknown'
  const projectObjective = projectSummary?.objective ?? 'No objective set yet.'
  const roadmapNow = projectSummary?.roadmap_now ?? projectRoadmap?.sections.now ?? []
  const roadmapNext = projectSummary?.roadmap_next ?? projectRoadmap?.sections.next ?? []
  const roadmapRisks = projectSummary?.roadmap_risks ?? projectRoadmap?.sections.risks ?? []
  const projectDecisions = projectSummary?.latest_decisions ?? []
  const monthlyCostLabel = formatCurrencyCad(projectSummary?.monthly_cost_estimate_cad)
  const costEventsLabel = String(projectSummary?.cost_events_this_month ?? 0)
  const modelUsageSummary = projectSummary?.model_usage_summary ?? []

  const activeProjectCard = useMemo<ProjectCatalogEntry>(
    () =>
      projectCatalog.find((project) => project.project_id === projectId) ?? {
        project_id: projectId,
        project_name: projectSettings?.project_name ?? projectId,
        linked_repo_path: projectSettings?.linked_repo_path ?? null,
        phase: projectSummary?.phase ?? 'Implement',
        objective: projectSummary?.objective ?? 'No objective set yet.',
      },
    [
      projectCatalog,
      projectId,
      projectSettings?.linked_repo_path,
      projectSettings?.project_name,
      projectSummary?.objective,
      projectSummary?.phase,
    ],
  )
  const visibleProjectCards = useMemo(() => [activeProjectCard], [activeProjectCard])
  const selectedProjectCard =
    visibleProjectCards.find((project) => project.project_id === selectedProjectDocId) ?? activeProjectCard

  return (
    <section className="secondary-tab panel">
      <div className="secondary-header">
        <h2>Docs</h2>
        <span className="hint">runbook truth + local skills library</span>
      </div>
      <div className="docs-subnav">
                <button
                  className={`docs-subnav-btn ${docsPanel === 'runbook' ? 'active' : ''}`}
                  type="button"
                  onClick={() => setDocsPanel('runbook')}
                >
          Runbook
        </button>
                <button
                  className={`docs-subnav-btn ${docsPanel === 'skills_library' ? 'active' : ''}`}
                  type="button"
                  onClick={() => setDocsPanel('skills_library')}
                >
          Skills Library
        </button>
                <button
                  className={`docs-subnav-btn ${docsPanel === 'project' ? 'active' : ''}`}
                  type="button"
                  onClick={() => setDocsPanel('project')}
                >
          Project
        </button>
      </div>
      {docsPanel === 'runbook' ? (
        <>
          <div className="secondary-grid">
            <article>
              <h3>Official app path</h3>
              <p>/Applications/Cockpit.app</p>
            </article>
            <article>
              <h3>Preflight contracts</h3>
              <p>/healthz + /chat/approvals + /llm-profile</p>
            </article>
            <article>
              <h3>Runtime mode</h3>
              <p>{backendHealth?.app_mode ?? 'cockpit_local'}</p>
            </article>
            <article>
              <h3>Daily command</h3>
              <p>open "/Applications/Cockpit.app"</p>
            </article>
          </div>
          <div className="secondary-columns">
            <section className="secondary-card">
              <h3>Operator checklist</h3>
              <div className="events-log">
                <p>1. Launch Cockpit.app</p>
                <p>2. Check backend and WS badges</p>
                <p>3. Verify approvals and llm-profile routes</p>
                <p>4. Work from Pixel Home, To Do, Le Conseil, and Model Routing</p>
              </div>
            </section>
            <section className="secondary-card">
              <h3>Reference docs</h3>
              <div className="events-log">
                <p><strong>Runbook:</strong> docs/COCKPIT_RUNBOOK.md</p>
                <p><strong>Protocol:</strong> docs/CLOUD_API_PROTOCOL.md</p>
                <p><strong>Packaging:</strong> docs/PACKAGING.md</p>
                <p><strong>Status:</strong> docs/STATUS_REPORT.md</p>
              </div>
            </section>
          </div>
        </>
      ) : docsPanel === 'skills_library' ? (
        <div className="skills-library-layout">
          <section className="secondary-card">
            <h3>Installed local skills</h3>
            <p className="small-copy">
              Read-only view from your local Codex skills folder plus project lock state when available.
            </p>
          </section>
          <div className="skills-library-grid">
            {skillsLibraryLoading ? (
              <section className="secondary-card">
                <p>Loading skills library...</p>
              </section>
            ) : skillsLibrary.length === 0 ? (
              <section className="secondary-card">
                <p>No local skills were discovered for this project yet.</p>
              </section>
            ) : (
              skillsLibrary.map((skill) => (
                <article key={skill.skill_id} className="secondary-card skill-library-card">
                  <div className="skill-library-head">
                    <div>
                      <h3>{skill.name}</h3>
                      <p className="skill-library-id">{skill.skill_id}</p>
                    </div>
                    <div className="skill-library-badges">
                      {skill.project_locked ? <span className="skill-chip project">project locked</span> : null}
                      {skill.assigned_agents.length > 0 ? <span className="skill-chip assigned">assigned</span> : <span className="skill-chip">local only</span>}
                    </div>
                  </div>
                  <p className="small-copy">{skill.description}</p>
                  <div className="events-log">
                    <p><strong>Source:</strong> {skill.source_path}</p>
                    <p><strong>Status:</strong> {skill.project_status ?? 'not locked'}</p>
                    <p>
                      <strong>Assigned agents:</strong>{' '}
                      {skill.assigned_agents.length > 0 ? skill.assigned_agents.map((agentId) => `@${agentId}`).join(', ') : 'none'}
                    </p>
                  </div>
                </article>
              ))
            )}
          </div>
        </div>
      ) : (
        <div className="project-docs-layout">
          <section className="secondary-card">
            <div className="section-title-row compact">
              <h3>Projects</h3>
              <span className="hint">{projectCatalogLoading ? 'loading...' : 'current live project only'}</span>
            </div>
            <div className="project-catalog-list">
              {visibleProjectCards.map((project) => (
                <button
                  key={project.project_id}
                  type="button"
                  className={`project-catalog-item ${selectedProjectCard.project_id === project.project_id ? 'active' : ''}`}
                  onClick={() => setSelectedProjectDocId(project.project_id)}
                >
                  <strong>{projectLabel(project.project_id, project.project_name)}</strong>
                  <span>@{project.project_id}</span>
                  <p>{project.phase} - {project.objective}</p>
                </button>
              ))}
            </div>
          </section>
          <section className="secondary-card">
            <h3>Project summary</h3>
            <ul className="data-list">
              <li>
                <span>Project</span>
                <strong>{projectLabel(selectedProjectCard.project_id, selectedProjectCard.project_name)}</strong>
              </li>
              <li>
                <span>Linked repo</span>
                <strong>{selectedProjectCard.linked_repo_path || linkedRepoLabel}</strong>
              </li>
              <li>
                <span>Phase</span>
                <strong>{selectedProjectCard.phase || projectPhase}</strong>
              </li>
              <li>
                <span>Objective</span>
                <strong>{selectedProjectCard.objective || projectObjective}</strong>
              </li>
              <li>
                <span>Monthly cost</span>
                <strong>{monthlyCostLabel}</strong>
              </li>
              <li>
                <span>Cost events</span>
                <strong>{costEventsLabel}</strong>
              </li>
            </ul>
          </section>
          <div className="secondary-columns">
            <section className="secondary-card">
              <h3>Roadmap now</h3>
              <ul className="simple-list">
                {(roadmapNow.length > 0 ? roadmapNow : ['No current roadmap items']).map((item) => (
                  <li key={`project-now-${item}`}>{item}</li>
                ))}
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Roadmap next</h3>
              <ul className="simple-list">
                {(roadmapNext.length > 0 ? roadmapNext : ['No next roadmap items']).map((item) => (
                  <li key={`project-next-${item}`}>{item}</li>
                ))}
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Latest decisions</h3>
              <ul className="simple-list">
                {(projectDecisions.length > 0 ? projectDecisions : ['No decision titles found']).map((item) => (
                  <li key={`decision-${item}`}>{item}</li>
                ))}
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Roadmap risks</h3>
              <ul className="simple-list">
                {(roadmapRisks.length > 0 ? roadmapRisks : ['No roadmap risks noted']).map((item) => (
                  <li key={`risk-${item}`}>{item}</li>
                ))}
              </ul>
            </section>
            <section className="secondary-card">
              <h3>Model usage</h3>
              <div className="events-log">
                {modelUsageSummary.length === 0 ? (
                  <p>No model usage tracked yet.</p>
                ) : (
                  modelUsageSummary.map((entry) => (
                    <p key={`project-usage-${entry.model}`}>
                      <strong>{entry.model}</strong> - {formatCurrencyCad(entry.cost_cad)} - {entry.events} events
                    </p>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      )}
    </section>
  )
}
