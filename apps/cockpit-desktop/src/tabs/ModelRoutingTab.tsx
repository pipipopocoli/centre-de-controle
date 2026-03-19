import { memo, useMemo } from 'react'
import { useCockpitStore } from '../store/index.js'
import type { RosterAgentView } from '../types.js'
import { modelLabel, isUnavailableModel } from '../lib/formatters.js'
import {
  CLEMS_MODEL_OPTIONS,
  L1_MODEL_OPTIONS,
  L2_MODEL_OPTIONS,
  VOICE_STT_OPTIONS,
} from '../lib/appConstants.js'

export interface ModelRoutingTabProps {
  handleSaveLlmProfile: () => Promise<void>
}

export const ModelRoutingTab = memo(function ModelRoutingTab({
  handleSaveLlmProfile,
}: ModelRoutingTabProps) {
  const feed = useCockpitStore((state) => state.feed)
  const agentRecords = useCockpitStore((state) => state.agentRecords)
  const llmProfile = useCockpitStore((state) => state.llmProfile)
  const profileDraft = useCockpitStore((state) => state.profileDraft)
  const setProfileDraft = useCockpitStore((state) => state.setProfileDraft)
  const isSavingProfile = useCockpitStore((state) => state.isSavingProfile)

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

  const l1Agents = useMemo(() => {
    const fromFeed = rosterAgents.filter((agent) => agent.level === 1).map((agent) => agent.agent_id)
    const fromProfile = profileDraft ? Object.keys(profileDraft.l1_models ?? {}) : []
    return [...new Set([...fromFeed, ...fromProfile])].sort()
  }, [profileDraft, rosterAgents])

  const profileDirty = useMemo(() => {
    if (!llmProfile || !profileDraft) return false
    return JSON.stringify(llmProfile) !== JSON.stringify(profileDraft)
  }, [llmProfile, profileDraft])

  if (!profileDraft) return null

  return (
    <section className="secondary-tab panel">
      <div className="secondary-header">
        <h2>Model Routing</h2>
        <span className="hint">role-based OpenRouter routing with project persistence</span>
      </div>
      <div className="routing-layout">
        <section className="secondary-card">
          <h3>Clems (L0)</h3>
          <div className="option-grid">
            {CLEMS_MODEL_OPTIONS.map((option) => (
                <button
                  key={option.id}
                  className={`route-option ${profileDraft.clems_model === option.id ? 'active' : ''}`}
                  type="button"
                  onClick={() =>
                  setProfileDraft((previous) =>
                    previous ? { ...previous, clems_model: option.id, clems_catalog: CLEMS_MODEL_OPTIONS.map((item) => item.id) } : previous,
                  )
                }
              >
                <strong>{option.label}</strong>
                <span>{option.note}</span>
              </button>
            ))}
          </div>
        </section>
        <section className="secondary-card">
          <h3>L1 models</h3>
          <div className="routing-agent-list">
            {l1Agents.map((agentId) => (
              <label key={agentId} className="routing-agent-row">
                <span>@{agentId}</span>
                <select
                  value={profileDraft.l1_models[agentId] ?? 'moonshotai/kimi-k2.5'}
                  onChange={(event) =>
                    setProfileDraft((previous) =>
                      previous
                        ? {
                            ...previous,
                            l1_catalog: L1_MODEL_OPTIONS.map((item) => item.id),
                            l1_models: {
                              ...previous.l1_models,
                              [agentId]: event.target.value,
                            },
                          }
                        : previous,
                    )
                  }
                >
                  {L1_MODEL_OPTIONS.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
        </section>
        <section className="secondary-card">
          <h3>L2 surgical pool</h3>
          <label className="routing-primary">
            <span>Primary model</span>
            <select
              value={profileDraft.l2_default_model}
              onChange={(event) =>
                setProfileDraft((previous) =>
                  previous
                    ? {
                        ...previous,
                        l2_default_model: event.target.value,
                        l2_pool: previous.l2_pool.includes(event.target.value)
                          ? previous.l2_pool
                          : [event.target.value, ...previous.l2_pool],
                      }
                    : previous,
                )
              }
            >
              {L2_MODEL_OPTIONS.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <div className="routing-pool">
            {L2_MODEL_OPTIONS.map((option) => {
              const active = profileDraft.l2_pool.includes(option.id)
              return (
                <button
                  key={option.id}
                  className={`route-option compact ${active ? 'active' : ''}`}
                  type="button"
                  onClick={() =>
                    setProfileDraft((previous) => {
                      if (!previous) {
                        return previous
                      }
                      const nextPool = active
                        ? previous.l2_pool.filter((item) => item !== option.id)
                        : [...previous.l2_pool, option.id]
                      const normalizedPool = nextPool.length === 0 ? [previous.l2_default_model] : nextPool
                      return {
                        ...previous,
                        l2_pool: normalizedPool,
                        l2_default_model: normalizedPool.includes(previous.l2_default_model)
                          ? previous.l2_default_model
                          : normalizedPool[0],
                      }
                    })
                  }
                >
                  <strong>{option.label}</strong>
                  <span>{option.note}</span>
                </button>
              )
            })}
          </div>
          <ul className="data-list">
            <li>
              <span>Selection mode</span>
              <strong>{profileDraft.l2_selection_mode}</strong>
            </li>
            <li>
              <span>Stream enabled</span>
              <strong>{profileDraft.stream_enabled ? 'yes' : 'no'}</strong>
            </li>
          </ul>
        </section>
        <section className="secondary-card">
          <h3>Voice STT</h3>
          <label className="routing-primary">
            <span>Voice transcription model</span>
            <select
              value={profileDraft.voice_stt_model}
              onChange={(event) =>
                setProfileDraft((previous) =>
                  previous ? { ...previous, voice_stt_model: event.target.value } : previous,
                )
              }
            >
              {[...VOICE_STT_OPTIONS, profileDraft.voice_stt_model]
                .filter((value, index, values) => values.indexOf(value) === index)
                .map((modelId) => (
                  <option key={modelId} value={modelId}>
                    {modelId}
                  </option>
                ))}
            </select>
          </label>
          <p className="small-copy">
            Voice is OpenRouter-only. The desktop recorder sends audio to the local Rust backend, which transcribes with this model and injects text into the composer.
          </p>
        </section>
        <section className="secondary-card">
          <h3>Current profile</h3>
          <ul className="data-list">
            <li>
              <span>Clems</span>
              <strong>{modelLabel(profileDraft.clems_model)}</strong>
            </li>
            <li>
              <span>Voice STT</span>
              <strong>{profileDraft.voice_stt_model}</strong>
            </li>
            <li>
              <span>L2 primary</span>
              <strong>{modelLabel(profileDraft.l2_default_model)}</strong>
            </li>
            <li>
              <span>Unavailable refs</span>
              <strong>
                {[profileDraft.clems_model, ...Object.values(profileDraft.l1_models), ...profileDraft.l2_pool].some(
                  (modelId) => isUnavailableModel(modelId),
                )
                  ? 'review'
                  : 'none'}
              </strong>
            </li>
            <li>
              <span>Draft</span>
              <strong>{profileDirty ? 'unsaved changes' : 'saved'}</strong>
            </li>
          </ul>
          <div className="todo-editor-actions">
            <button className="send-btn" onClick={() => void handleSaveLlmProfile()} disabled={isSavingProfile}>
              {isSavingProfile ? 'Saving...' : 'Save model routing'}
            </button>
          </div>
        </section>
      </div>
    </section>
  )
})
