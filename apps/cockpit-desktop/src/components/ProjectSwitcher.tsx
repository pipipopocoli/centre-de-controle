import { useCallback, useEffect, useRef, useState } from 'react'
import { useCockpitStore } from '../store/index.js'
import { getProjects } from '../lib/cockpitClient.js'

export function ProjectSwitcher() {
  const projectId = useCockpitStore((s) => s.projectId)
  const projectCatalog = useCockpitStore((s) => s.projectCatalog)
  const projectSettings = useCockpitStore((s) => s.projectSettings)
  const setProjectId = useCockpitStore((s) => s.setProjectId)
  const setProjectCatalog = useCockpitStore((s) => s.setProjectCatalog)
  const setProjectActionMode = useCockpitStore((s) => s.setProjectActionMode)
  const setActiveTab = useCockpitStore((s) => s.setActiveTab)

  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const currentName = projectSettings?.project_name ?? projectId

  // Close dropdown on outside click
  useEffect(() => {
    if (!open) return
    const handler = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  // Refresh catalog when dropdown opens
  useEffect(() => {
    if (!open) return
    getProjects()
      .then((projects) => setProjectCatalog(projects))
      .catch(() => { /* catalog refresh failed silently */ })
  }, [open, setProjectCatalog])

  const handleSwitch = useCallback(
    (targetProjectId: string) => {
      if (targetProjectId === projectId) {
        setOpen(false)
        return
      }
      setProjectId(targetProjectId)
      setOpen(false)
      // Trigger a full reload so bootstrap re-runs for the new project
      window.location.reload()
    },
    [projectId, setProjectId],
  )

  const handleCreateNew = useCallback(() => {
    setOpen(false)
    setProjectActionMode('create')
    setActiveTab('concierge_room')
  }, [setProjectActionMode, setActiveTab])

  const truncatePath = (path: string | null | undefined, maxLen = 28): string => {
    if (!path) return 'no repo linked'
    if (path.length <= maxLen) return path
    return '\u2026' + path.slice(-(maxLen - 1))
  }

  return (
    <div className="project-switcher" ref={containerRef}>
      <button
        className="project-switcher-trigger"
        onClick={() => setOpen((prev) => !prev)}
        type="button"
      >
        <span className="project-switcher-current">
          <span className="project-switcher-name">{currentName}</span>
          <span className="project-switcher-id">{projectId}</span>
        </span>
        <span className="project-switcher-chevron">{open ? '\u25B4' : '\u25BE'}</span>
      </button>

      {open && (
        <div className="project-switcher-dropdown">
          {projectCatalog.length === 0 && (
            <div className="project-switcher-empty">No projects found</div>
          )}
          {projectCatalog.map((project) => (
            <button
              key={project.project_id}
              className={`project-switcher-item ${project.project_id === projectId ? 'active' : ''}`}
              onClick={() => handleSwitch(project.project_id)}
              type="button"
            >
              <span className="project-switcher-item-name">
                {project.project_name || project.project_id}
              </span>
              <span className="project-switcher-item-repo">
                {truncatePath(project.linked_repo_path)}
              </span>
            </button>
          ))}
          <button
            className="project-switcher-create"
            onClick={handleCreateNew}
            type="button"
          >
            + Create project
          </button>
        </div>
      )}
    </div>
  )
}
