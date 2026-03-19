import { memo } from 'react'
import {
  useCockpitStore,
  useDirectChatMessages,
  useConciergeChatMessages,
  useInternalConciergeMessages,
} from '../store/index.js'
import type { HealthzResponse } from '../lib/cockpitClient'
import type { FallbackDiagnostic } from '../types.js'

export interface PilotageTabProps {
  composerLabel: string
  fallbackDiagnostics: FallbackDiagnostic[]
  backendHealth: HealthzResponse | null
  eventLog: Array<{ type: string; timestamp: string }>
}

export const PilotageTab = memo(function PilotageTab({
  composerLabel,
  fallbackDiagnostics,
  backendHealth,
  eventLog,
}: PilotageTabProps) {
  const directChatMessages = useDirectChatMessages()
  const conciergeChatMessages = useConciergeChatMessages()
  const internalConciergeMessages = useInternalConciergeMessages()
  const approvals = useCockpitStore((state) => state.approvals)

  const openRouterHealth = backendHealth?.openrouter ?? null
  const latestDirect = directChatMessages.slice(-8).reverse()
  const latestInternal = internalConciergeMessages.slice(-8).reverse()
  const latestEvents = eventLog.slice(0, 20)

  return (
    <section className="secondary-tab panel">
      <div className="secondary-header">
        <h2>Pilotage</h2>
        <span className="hint">live operations stream and execution health</span>
      </div>
      <div className="secondary-grid">
        <article>
          <h3>Operator messages</h3>
          <p>{directChatMessages.length}</p>
        </article>
        <article>
          <h3>Room messages</h3>
          <p>{conciergeChatMessages.length}</p>
        </article>
        <article>
          <h3>Approvals pending</h3>
          <p>{approvals.length}</p>
        </article>
        <article>
          <h3>Delivery mode</h3>
          <p>{composerLabel}</p>
        </article>
      </div>
      <div className="secondary-columns">
        <section className="secondary-card">
          <h3>OpenRouter</h3>
          <ul className="data-list">
            <li>
              <span>Status</span>
              <strong>{openRouterHealth?.status ?? 'unknown'}</strong>
            </li>
            <li>
              <span>Base URL</span>
              <strong>{openRouterHealth?.base_url || 'missing'}</strong>
            </li>
            <li>
              <span>API key</span>
              <strong>{openRouterHealth?.api_key_present ? 'present' : 'missing'}</strong>
            </li>
            <li>
              <span>Last OK</span>
              <strong>{openRouterHealth?.last_ok_at ? new Date(openRouterHealth.last_ok_at).toLocaleTimeString() : 'never'}</strong>
            </li>
            <li>
              <span>Last error</span>
              <strong>{openRouterHealth?.last_error || 'none'}</strong>
            </li>
            <li>
              <span>Error kind</span>
              <strong>{openRouterHealth?.last_error_kind || 'none'}</strong>
            </li>
            <li>
              <span>HTTP status</span>
              <strong>{openRouterHealth?.last_http_status ?? 'none'}</strong>
            </li>
            <li>
              <span>Request ID</span>
              <strong>{openRouterHealth?.last_request_id || 'none'}</strong>
            </li>
            <li>
              <span>Body preview</span>
              <strong>{openRouterHealth?.last_body_preview || 'none'}</strong>
            </li>
          </ul>
        </section>
        <section className="secondary-card">
          <h3>Latest operator chat</h3>
          <div className="events-log">
            {latestDirect.length === 0 ? (
              <p>No direct messages yet.</p>
            ) : (
              latestDirect.map((message) => (
                <p key={message.message_id}>
                  <strong>@{message.author}</strong> {message.text}
                </p>
              ))
            )}
          </div>
        </section>
        <section className="secondary-card">
          <h3>Latest internal + events</h3>
          <div className="events-log">
            {fallbackDiagnostics.slice(0, 6).map((diagnostic) => (
              <p key={diagnostic.id}>
                <strong>fallback</strong> [{diagnostic.chatMode}] {diagnostic.error} - {new Date(diagnostic.timestamp).toLocaleTimeString()}
              </p>
            ))}
            {latestInternal.slice(0, 6).map((message) => (
              <p key={message.message_id}>
                <strong>@{message.author}</strong> [{message.visibility}] {message.text}
              </p>
            ))}
            {latestEvents.slice(0, 10).map((event, index) => (
              <p key={`${event.timestamp}-${index}`}>
                <strong>{event.type}</strong> {new Date(event.timestamp).toLocaleTimeString()}
              </p>
            ))}
            {fallbackDiagnostics.length === 0 && latestInternal.length === 0 && latestEvents.length === 0 ? <p>No diagnostics yet.</p> : null}
          </div>
        </section>
      </div>
    </section>
  )
})
