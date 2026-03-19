import { useCallback, useEffect } from 'react'
import { useCockpitStore } from '../store/index.js'
import {
  createAgent,
  getAgents,
  getApprovals,
  getChat,
  getHealth,
  getLayout,
  getLlmProfile,
  getPixelFeed,
  getProjects,
  getProjectSettings,
  getProjectSummary,
  getRoadmap,
  getSkillsLibrary,
  getTasks,
  openTerminal,
  putLayout,
} from '../lib/cockpitClient'
import type { PixelFeedResponse } from '../lib/cockpitClient'
import type { ToolActivity } from '../office/types.js'
import { loadDonargTheme } from '../office/themes/donargTheme.js'
import { loadPixelReferenceTheme } from '../office/themes/pixelReferenceTheme.js'
import type { OfficeState } from '../office/engine/officeState.js'
import type { OfficeLayout } from '../office/types.js'

/**
 * All refresh* callbacks, bootstrap, syncOfficeAgents, and tab-conditional refresh effects.
 */
export function useDataSync({
  officeState,
  toNumericId,
  styleForAgent,
  idToNumericRef,
  numericToIdRef,
}: {
  officeState: OfficeState
  toNumericId: (agentId: string) => number
  styleForAgent: (agentId: string) => { palette: number; hueShift: number }
  idToNumericRef: React.RefObject<Map<string, number>>
  numericToIdRef: React.RefObject<Map<number, string>>
}) {
  const projectId = useCockpitStore((s) => s.projectId)
  const activeTab = useCockpitStore((s) => s.activeTab)
  const docsPanel = useCockpitStore((s) => s.docsPanel)
  const markSynced = useCockpitStore((s) => s.markSynced)
  const setApiError = useCockpitStore((s) => s.setApiError)
  const setFeed = useCockpitStore((s) => s.setFeed)
  const setAgentRecords = useCockpitStore((s) => s.setAgentRecords)
  const setSelectedAgentId = useCockpitStore((s) => s.setSelectedAgentId)
  const setAgentTools = useCockpitStore((s) => s.setAgentTools)
  const setRefreshTick = useCockpitStore((s) => s.setRefreshTick)
  const setApprovals = useCockpitStore((s) => s.setApprovals)
  const setLoading = useCockpitStore((s) => s.setLoading)
  const mergeChatMessages = useCockpitStore((s) => s.mergeChatMessages)
  const setBackendHealth = useCockpitStore((s) => s.setBackendHealth)
  const setLlmProfile = useCockpitStore((s) => s.setLlmProfile)
  const setProfileDraft = useCockpitStore((s) => s.setProfileDraft)
  const setTasks = useCockpitStore((s) => s.setTasks)
  const setSelectedTaskId = useCockpitStore((s) => s.setSelectedTaskId)
  const setProjectSettings = useCockpitStore((s) => s.setProjectSettings)
  const setLinkedRepoDraft = useCockpitStore((s) => s.setLinkedRepoDraft)
  const setProjectRoadmap = useCockpitStore((s) => s.setProjectRoadmap)
  const setProjectSummary = useCockpitStore((s) => s.setProjectSummary)
  const setProjectCatalog = useCockpitStore((s) => s.setProjectCatalog)
  const setProjectCatalogLoading = useCockpitStore((s) => s.setProjectCatalogLoading)
  const setSkillsLibrary = useCockpitStore((s) => s.setSkillsLibrary)
  const setSkillsLibraryLoading = useCockpitStore((s) => s.setSkillsLibraryLoading)
  const setLastEventAt = useCockpitStore((s) => s.setLastEventAt)
  const setActiveTab = useCockpitStore((s) => s.setActiveTab)
  const setWorkspaceTab = useCockpitStore((s) => s.setWorkspaceTab)
  const setWorkbenchPanel = useCockpitStore((s) => s.setWorkbenchPanel)
  const setDirectTarget = useCockpitStore((s) => s.setDirectTarget)
  const setUiNotice = useCockpitStore((s) => s.setUiNotice)
  const setAssetsStatus = useCockpitStore((s) => s.setAssetsStatus)

  const refreshApprovals = useCallback(async () => {
    try {
      const response = await getApprovals(projectId, 'pending')
      setApprovals(response.approvals)
      markSynced()
    } catch {
      // keep silent to avoid noisy UI while reconnecting
    }
  }, [markSynced, projectId, setApprovals])

  const syncOfficeAgents = useCallback(
    (nextFeed: PixelFeedResponse | null) => {
      if (!nextFeed) {
        return
      }

      const ids = new Set(nextFeed.agents.map((agent) => agent.agent_id))

      for (const [agentId, numericId] of idToNumericRef.current.entries()) {
        if (!ids.has(agentId)) {
          officeState.removeAgent(numericId)
          idToNumericRef.current.delete(agentId)
          numericToIdRef.current.delete(numericId)
        }
      }

      const tools: Record<number, ToolActivity[]> = {}

      for (const agent of nextFeed.agents) {
        const numericId = toNumericId(agent.agent_id)
        const exists = officeState.characters.has(numericId)
        if (!exists) {
          const style = styleForAgent(agent.agent_id)
          officeState.addAgent(
            numericId,
            style.palette,
            style.hueShift,
            undefined,
            true,
            agent.name,
          )
        }

        const isActive = agent.terminal_state === 'running'
        officeState.setAgentActive(numericId, isActive)
        officeState.setAgentTool(numericId, isActive ? 'terminal' : null)

        tools[numericId] = [
          {
            toolId: `terminal-${agent.agent_id}`,
            status: isActive ? 'Terminal live' : 'Idle',
            done: !isActive,
          },
        ]
      }

      const currentSelected = useCockpitStore.getState().selectedAgentId
      if (!currentSelected || !ids.has(currentSelected)) {
        setSelectedAgentId(ids.has('clems') ? 'clems' : nextFeed.agents[0]?.agent_id ?? null)
      }

      setAgentTools(tools)
      setRefreshTick((value) => value + 1)
    },
    [officeState, styleForAgent, toNumericId, idToNumericRef, numericToIdRef, setSelectedAgentId, setAgentTools, setRefreshTick],
  )

  const refreshPixelFeed = useCallback(async () => {
    const nextFeed = await getPixelFeed(projectId)
    setFeed(nextFeed)
    syncOfficeAgents(nextFeed)
    markSynced()
  }, [markSynced, projectId, setFeed, syncOfficeAgents])

  const refreshAgentWorkspace = useCallback(async () => {
    const [nextFeed, nextAgents] = await Promise.all([getPixelFeed(projectId), getAgents(projectId)])
    setFeed(nextFeed)
    setAgentRecords(nextAgents)
    syncOfficeAgents(nextFeed)
    markSynced()
    return { nextFeed, nextAgents }
  }, [markSynced, projectId, setFeed, setAgentRecords, syncOfficeAgents])

  const refreshSkillsLibrary = useCallback(async () => {
    setSkillsLibraryLoading(true)

    try {
      const response = await getSkillsLibrary(projectId)
      setSkillsLibrary(response.skills)
      markSynced()
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setSkillsLibraryLoading(false)
    }
  }, [markSynced, projectId, setApiError, setSkillsLibrary, setSkillsLibraryLoading])

  const refreshProjectSettings = useCallback(async () => {
    const settings = await getProjectSettings(projectId)
    setProjectSettings(settings)
    setLinkedRepoDraft(settings.linked_repo_path ?? '')
    markSynced()
    return settings
  }, [markSynced, projectId, setProjectSettings, setLinkedRepoDraft])

  const refreshProjectSummary = useCallback(async () => {
    const summary = await getProjectSummary(projectId)
    setProjectSummary(summary)
    markSynced()
    return summary
  }, [markSynced, projectId, setProjectSummary])

  const refreshProjectCatalog = useCallback(async () => {
    setProjectCatalogLoading(true)
    try {
      const projects = await getProjects()
      setProjectCatalog(projects)
      markSynced()
      return projects
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
      return []
    } finally {
      setProjectCatalogLoading(false)
    }
  }, [markSynced, setApiError, setProjectCatalog, setProjectCatalogLoading])

  const refreshRoadmap = useCallback(async () => {
    const roadmap = await getRoadmap(projectId)
    setProjectRoadmap(roadmap)
    markSynced()
    return roadmap
  }, [markSynced, projectId, setProjectRoadmap])

  const ensureClemsAgent = useCallback(async () => {
    let nextAgents = await getAgents(projectId)
    if (!nextAgents.some((agent) => agent.agent_id === 'clems')) {
      await createAgent(projectId, { agent_id: 'clems' })
      nextAgents = await getAgents(projectId)
    }
    setAgentRecords(nextAgents)
    return nextAgents
  }, [projectId, setAgentRecords])

  const refreshTasks = useCallback(async () => {
    const response = await getTasks(projectId)
    setTasks(response.tasks)
    setSelectedTaskId((previous) => previous ?? response.tasks[0]?.task_id ?? null)
    markSynced()
  }, [markSynced, projectId, setTasks, setSelectedTaskId])

  const bootstrap = useCallback(async () => {
    setLoading(true)
    setApiError(null)

    try {
      const [themeLoaded, pixelRefLoaded] = await Promise.all([loadDonargTheme(), loadPixelReferenceTheme()])

      await ensureClemsAgent()

      const [layout, pixel, chat, pendingApprovals, health, profile, taskPayload, settings, roadmap, summary, projects] = await Promise.all([
        getLayout(projectId),
        getPixelFeed(projectId),
        getChat(projectId, 300, 'all'),
        getApprovals(projectId, 'pending'),
        getHealth(),
        getLlmProfile(projectId),
        getTasks(projectId),
        getProjectSettings(projectId),
        getRoadmap(projectId),
        getProjectSummary(projectId),
        getProjects(),
      ])

      const presetKey = `cockpit.video_preset_applied.${projectId}`
      let activeLayout = layout
      if (!window.localStorage.getItem(presetKey)) {
        try {
          const presetResponse = await fetch('/local-assets/presets/video-scene.layout.json')
          if (presetResponse.ok) {
            const presetLayout = (await presetResponse.json()) as Record<string, unknown>
            await putLayout(projectId, presetLayout)
            activeLayout = presetLayout
            window.localStorage.setItem(presetKey, '1')
            setUiNotice('video preset auto-applied')
          }
        } catch {
          // ignore and keep project layout
        }
      }

      officeState.rebuildFromLayout(activeLayout as unknown as OfficeLayout)
      setFeed(pixel)
      mergeChatMessages(chat.messages)
      setApprovals(pendingApprovals.approvals)
      setBackendHealth(health)
      setLlmProfile(profile)
      setProfileDraft(profile)
      setTasks(taskPayload.tasks)
      setProjectSettings(settings)
      setProjectCatalog(projects)
      setLinkedRepoDraft(settings.linked_repo_path ?? '')
      setProjectRoadmap(roadmap)
      setProjectSummary(summary)
      setSelectedTaskId((previous) => previous ?? taskPayload.tasks[0]?.task_id ?? null)
      setAssetsStatus({
        donarg: themeLoaded,
        pixelRef: pixelRefLoaded,
      })
      setLastEventAt(health.time ?? null)
      setActiveTab('pixel_home')
      setWorkspaceTab('agent')
      setWorkbenchPanel('chat')
      setSelectedAgentId('clems')
      setDirectTarget('clems')
      markSynced()
      syncOfficeAgents(pixel)

      if (health.status === 'ok') {
        try {
          await openTerminal(projectId, 'clems')
          await refreshPixelFeed()
        } catch {
          setUiNotice('clems terminal did not auto-open. open it from the terminal panel.')
        }
      }

      if (!themeLoaded) {
        setUiNotice('donarg assets not loaded. run import_office_tileset.sh if needed.')
      } else if (!pixelRefLoaded) {
        setUiNotice('pixel reference character assets missing. run import_pixel_reference_assets.sh.')
      }
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    } finally {
      setLoading(false)
    }
  }, [
    ensureClemsAgent,
    markSynced,
    mergeChatMessages,
    officeState,
    projectId,
    refreshPixelFeed,
    syncOfficeAgents,
    setApiError,
    setApprovals,
    setAssetsStatus,
    setBackendHealth,
    setDirectTarget,
    setFeed,
    setLastEventAt,
    setLinkedRepoDraft,
    setLlmProfile,
    setLoading,
    setActiveTab,
    setProfileDraft,
    setProjectCatalog,
    setProjectRoadmap,
    setProjectSettings,
    setProjectSummary,
    setSelectedAgentId,
    setSelectedTaskId,
    setTasks,
    setUiNotice,
    setWorkbenchPanel,
    setWorkspaceTab,
  ])

  // Bootstrap on mount / projectId change
  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  // Tab-conditional refresh: skills library
  useEffect(() => {
    if (activeTab === 'docs' && docsPanel === 'skills_library') {
      void refreshSkillsLibrary()
    }
  }, [activeTab, docsPanel, refreshSkillsLibrary])

  // Tab-conditional refresh: project summary
  useEffect(() => {
    if (activeTab === 'overview' || (activeTab === 'docs' && docsPanel === 'project')) {
      void refreshProjectSummary()
    }
  }, [activeTab, docsPanel, refreshProjectSummary])

  // Tab-conditional refresh: project catalog
  useEffect(() => {
    if (activeTab === 'overview' || (activeTab === 'docs' && docsPanel === 'project')) {
      void refreshProjectCatalog()
    }
  }, [activeTab, docsPanel, refreshProjectCatalog])

  return {
    refreshApprovals,
    refreshPixelFeed,
    refreshAgentWorkspace,
    refreshSkillsLibrary,
    refreshProjectSettings,
    refreshProjectSummary,
    refreshProjectCatalog,
    refreshRoadmap,
    refreshTasks,
    ensureClemsAgent,
    bootstrap,
    syncOfficeAgents,
  }
}
