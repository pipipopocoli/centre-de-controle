import { useCallback, useEffect, useRef } from 'react'
import { useCockpitStore } from '../store/index.js'
import { connectEvents, getChat } from '../lib/cockpitClient'
import type { ChatMessage } from '../lib/cockpitClient'
import type { ComposerStatus } from '../types.js'

/**
 * Manages WebSocket/SSE event connection, fallback polling, and related refs.
 */
export function useWebSocket({
  refreshApprovals,
  refreshPixelFeed,
  refreshAgentWorkspace,
  refreshProjectSummary,
  refreshTasks,
}: {
  refreshApprovals: () => Promise<void>
  refreshPixelFeed: () => Promise<void>
  refreshAgentWorkspace: () => Promise<{ nextFeed: unknown; nextAgents: unknown }>
  refreshProjectSummary: () => Promise<unknown>
  refreshTasks: () => Promise<void>
}) {
  const projectId = useCockpitStore((s) => s.projectId)
  const setWsConnected = useCockpitStore((s) => s.setWsConnected)
  const setComposerStatus = useCockpitStore((s) => s.setComposerStatus)
  const setEventLog = useCockpitStore((s) => s.setEventLog)
  const setLastEventAt = useCockpitStore((s) => s.setLastEventAt)
  const mergeChatMessages = useCockpitStore((s) => s.mergeChatMessages)
  const setChatMessages = useCockpitStore((s) => s.setChatMessages)
  const setApprovals = useCockpitStore((s) => s.setApprovals)
  const setUiNotice = useCockpitStore((s) => s.setUiNotice)

  const wsConnectedRef = useRef(false)
  const fallbackPollingRef = useRef(false)
  const fallbackPollTimerRef = useRef<number | null>(null)
  const fallbackStopTimerRef = useRef<number | null>(null)

  const stopFallbackPolling = useCallback(
    (nextStatus?: ComposerStatus) => {
      fallbackPollingRef.current = false
      if (fallbackPollTimerRef.current !== null) {
        window.clearInterval(fallbackPollTimerRef.current)
        fallbackPollTimerRef.current = null
      }
      if (fallbackStopTimerRef.current !== null) {
        window.clearTimeout(fallbackStopTimerRef.current)
        fallbackStopTimerRef.current = null
      }
      if (nextStatus) {
        setComposerStatus(nextStatus)
      }
    },
    [setComposerStatus],
  )

  const startFallbackPolling = useCallback(() => {
    if (fallbackPollingRef.current) {
      return
    }

    fallbackPollingRef.current = true
    setComposerStatus('http_fallback')

    const poll = async () => {
      try {
        const history = await getChat(projectId, 300, 'operator')
        mergeChatMessages(history.messages)
      } catch {
        // no-op: keep trying during fallback window
      }

      if (wsConnectedRef.current) {
        stopFallbackPolling('live')
        void refreshApprovals()
      }
    }

    void poll()

    fallbackPollTimerRef.current = window.setInterval(() => {
      void poll()
    }, 1500)

    fallbackStopTimerRef.current = window.setTimeout(() => {
      if (wsConnectedRef.current) {
        stopFallbackPolling('live')
      } else {
        stopFallbackPolling('reconnecting')
      }
    }, 20_000)
  }, [mergeChatMessages, projectId, refreshApprovals, setComposerStatus, stopFallbackPolling])

  // WebSocket/SSE event connection
  useEffect(() => {
    const disconnect = connectEvents(
      projectId,
      (event) => {
        setEventLog((previous) => [event, ...previous].slice(0, 160))
        setLastEventAt(event.timestamp)

        if (event.type === 'chat.message.created') {
          const message = event.payload.message as ChatMessage | undefined
          if (message?.message_id) {
            mergeChatMessages([message])
          }
          return
        }

        if (event.type === 'chat.reset.completed') {
          setChatMessages([])
          setApprovals([])
          setUiNotice('chat reset complete')
          return
        }

        if (event.type === 'approval.requested' || event.type === 'approval.updated') {
          void refreshApprovals()
          return
        }

        if (event.type === 'task.created' || event.type === 'task.updated') {
          void refreshTasks()
          void refreshProjectSummary()
          return
        }

        if (event.type === 'agent.terminal.status') {
          const state = String(event.payload.state ?? '')
          if (state !== 'output') {
            void refreshPixelFeed()
          }
          return
        }

        if (
          event.type === 'agent.created' ||
          event.type === 'agent.updated'
        ) {
          void refreshAgentWorkspace()
          return
        }

        if (
          event.type === 'pixel.updated' ||
          event.type === 'layout.updated' ||
          event.type === 'agent.spawn.completed'
        ) {
          void refreshPixelFeed()
        }

        if (event.type === 'project.settings.updated' || event.type === 'roadmap.updated') {
          void refreshProjectSummary()
        }
      },
      (connected) => {
        wsConnectedRef.current = connected
        setWsConnected(connected)
        if (connected) {
          setComposerStatus('live')
          stopFallbackPolling('live')
          void refreshApprovals()
        } else if (!fallbackPollingRef.current) {
          setComposerStatus('reconnecting')
        }
      },
    )

    return () => {
      disconnect()
      stopFallbackPolling()
    }
  }, [
    projectId,
    mergeChatMessages,
    setChatMessages,
    setApprovals,
    setUiNotice,
    setEventLog,
    setLastEventAt,
    setWsConnected,
    setComposerStatus,
    refreshAgentWorkspace,
    refreshApprovals,
    refreshPixelFeed,
    refreshProjectSummary,
    refreshTasks,
    stopFallbackPolling,
  ])

  return {
    wsConnectedRef,
    fallbackPollingRef,
    fallbackPollTimerRef,
    fallbackStopTimerRef,
    stopFallbackPolling,
    startFallbackPolling,
  }
}
