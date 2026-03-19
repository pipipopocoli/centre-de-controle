import { useCallback } from 'react'
import type { FormEvent } from 'react'
import { useCockpitStore } from '../store/index.js'
import {
  createAgent,
  deleteAgent,
} from '../lib/cockpitClient'
import { parseSkillsInput } from '../lib/formatters.js'

/**
 * Agent CRUD actions: create, delete, select, ensure terminal, office click/close, quick agent.
 */
export function useAgentActions({
  refreshAgentWorkspace,
  ensureAgentTerminal,
  numericToIdRef,
}: {
  refreshAgentWorkspace: () => Promise<{ nextFeed: unknown; nextAgents: unknown }>
  ensureAgentTerminal: (agentId: string) => Promise<void>
  numericToIdRef: React.RefObject<Map<number, string>>
}) {
  const projectId = useCockpitStore((s) => s.projectId)
  const createAgentId = useCockpitStore((s) => s.createAgentId)
  const createAgentName = useCockpitStore((s) => s.createAgentName)
  const createAgentSkills = useCockpitStore((s) => s.createAgentSkills)
  const isSubmitting = useCockpitStore((s) => s.isSubmitting)
  const agentRecords = useCockpitStore((s) => s.agentRecords)
  const setApiError = useCockpitStore((s) => s.setApiError)
  const setSelectedAgentId = useCockpitStore((s) => s.setSelectedAgentId)
  const setDirectTarget = useCockpitStore((s) => s.setDirectTarget)
  const setCreateAgentId = useCockpitStore((s) => s.setCreateAgentId)
  const setCreateAgentName = useCockpitStore((s) => s.setCreateAgentName)
  const setCreateAgentSkills = useCockpitStore((s) => s.setCreateAgentSkills)
  const setIsSubmitting = useCockpitStore((s) => s.setIsSubmitting)
  const setActiveTab = useCockpitStore((s) => s.setActiveTab)
  const setWorkspaceTab = useCockpitStore((s) => s.setWorkspaceTab)
  const setWorkbenchPanel = useCockpitStore((s) => s.setWorkbenchPanel)

  const handleSelectAgent = useCallback((agentId: string) => {
    setSelectedAgentId(agentId)
    setDirectTarget(agentId === 'clems' ? 'clems' : 'selected_agent')
  }, [setSelectedAgentId, setDirectTarget])

  const handleCreateAgent = useCallback(
    async (event: FormEvent) => {
      event.preventDefault()
      if (isSubmitting) {
        return
      }

      setIsSubmitting(true)
      setApiError(null)
      try {
        const payload = {
          agent_id: createAgentId.trim() || undefined,
          name: createAgentName.trim() || undefined,
          skills: parseSkillsInput(createAgentSkills),
        }
        const created = await createAgent(projectId, payload)
        setCreateAgentId('')
        setCreateAgentName('')
        setCreateAgentSkills('')
        setSelectedAgentId(created.agent.agent_id)
        await refreshAgentWorkspace()
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      } finally {
        setIsSubmitting(false)
      }
    },
    [
      createAgentId,
      createAgentName,
      createAgentSkills,
      isSubmitting,
      projectId,
      refreshAgentWorkspace,
      setApiError,
      setCreateAgentId,
      setCreateAgentName,
      setCreateAgentSkills,
      setIsSubmitting,
      setSelectedAgentId,
    ],
  )

  const handleDeleteAgent = useCallback(
    async (agentId: string) => {
      setApiError(null)
      try {
        await deleteAgent(projectId, agentId)
        await refreshAgentWorkspace()
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      }
    },
    [projectId, refreshAgentWorkspace, setApiError],
  )

  const handleOfficeClick = useCallback(
    async (numericId: number) => {
      const agentId = numericToIdRef.current.get(numericId)
      if (!agentId) {
        return
      }

      setSelectedAgentId(agentId)
      setActiveTab('pixel_home')
      setWorkspaceTab('agent')
      setWorkbenchPanel('chat')
      setDirectTarget(agentId === 'clems' ? 'clems' : 'selected_agent')
    },
    [numericToIdRef, setSelectedAgentId, setActiveTab, setWorkspaceTab, setWorkbenchPanel, setDirectTarget],
  )

  const handleOfficeClose = useCallback(
    (numericId: number) => {
      const agentId = numericToIdRef.current.get(numericId)
      if (!agentId) {
        return
      }
      void handleDeleteAgent(agentId)
    },
    [handleDeleteAgent, numericToIdRef],
  )

  const handleQuickAgent = useCallback(
    async (agentId: string) => {
      setApiError(null)
      setActiveTab('pixel_home')
      setWorkspaceTab('agent')
      setWorkbenchPanel('chat')
      try {
        if (!agentRecords.some((agent) => agent.agent_id === agentId)) {
          await createAgent(projectId, { agent_id: agentId })
          await refreshAgentWorkspace()
        }

        setSelectedAgentId(agentId)
        if (agentId === 'clems') {
          setDirectTarget('clems')
          await ensureAgentTerminal('clems')
        } else {
          setDirectTarget('selected_agent')
        }
      } catch (error) {
        setApiError(error instanceof Error ? error.message : String(error))
      }
    },
    [
      agentRecords,
      ensureAgentTerminal,
      projectId,
      refreshAgentWorkspace,
      setActiveTab,
      setApiError,
      setDirectTarget,
      setSelectedAgentId,
      setWorkbenchPanel,
      setWorkspaceTab,
    ],
  )

  return {
    handleSelectAgent,
    handleCreateAgent,
    handleDeleteAgent,
    handleOfficeClick,
    handleOfficeClose,
    handleQuickAgent,
  }
}
