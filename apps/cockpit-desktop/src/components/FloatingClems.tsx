import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useCockpitStore, useDirectChatMessages } from '../store/index.js'
import { liveTurn } from '../lib/cockpitClient.js'
import type { ChatMessage } from '../lib/cockpitClient.js'

export function FloatingClems() {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const projectId = useCockpitStore((s) => s.projectId)
  const activeTab = useCockpitStore((s) => s.activeTab)
  const workbenchPanel = useCockpitStore((s) => s.workbenchPanel)
  const composerStatus = useCockpitStore((s) => s.composerStatus)
  const mergeChatMessages = useCockpitStore((s) => s.mergeChatMessages)

  const directChatMessages = useDirectChatMessages()

  // Last 40 direct messages (clems is the default direct target)
  const clemsMessages = useMemo(
    () => directChatMessages.slice(-40),
    [directChatMessages],
  )

  // Track unread messages when panel is closed
  const [lastSeenCount, setLastSeenCount] = useState(0)
  const hasUnread = !isOpen && clemsMessages.length > lastSeenCount

  // When opening, mark messages as seen
  useEffect(() => {
    if (isOpen) {
      setLastSeenCount(clemsMessages.length)
    }
  }, [isOpen, clemsMessages.length])

  // Auto-scroll to bottom when messages change and panel is open
  useEffect(() => {
    if (isOpen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [isOpen, clemsMessages.length])

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  // Hide when pixel_home chat workbench is already showing
  const shouldHide = activeTab === 'pixel_home' && workbenchPanel === 'chat'

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen((prev) => !prev)
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isOpen])

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || isSending) return

    setIsSending(true)
    setInput('')

    try {
      const response = await liveTurn(projectId, {
        text,
        chat_mode: 'direct',
        execution_mode: 'chat',
        target_agent_id: 'clems',
        mentions: ['clems'],
      })
      if (response.messages?.length) {
        mergeChatMessages(response.messages)
      }
    } catch {
      // Silently fail - the message may still arrive via WebSocket
    } finally {
      setIsSending(false)
    }
  }, [input, isSending, projectId, mergeChatMessages])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  const statusLabel =
    composerStatus === 'live'
      ? 'LIVE'
      : composerStatus === 'http_fallback'
        ? 'HTTP'
        : 'Reconnecting'

  const statusClass =
    composerStatus === 'live'
      ? 'ok'
      : composerStatus === 'http_fallback'
        ? 'warn'
        : 'err'

  if (shouldHide) return null

  return (
    <div className="floating-clems">
      {isOpen && (
        <div className="floating-chat-panel">
          <div className="floating-chat-header">
            <div className="floating-chat-header-left">
              <span className="floating-chat-avatar">CL</span>
              <span className="floating-chat-title">@clems</span>
              <span className={`floating-chat-status ${statusClass}`}>{statusLabel}</span>
            </div>
            <button
              className="floating-chat-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat panel"
            >
              &times;
            </button>
          </div>

          <div className="floating-chat-messages">
            {clemsMessages.length === 0 ? (
              <div className="floating-chat-empty">
                <p>No messages yet.</p>
                <p>Send a message to @clems to get started.</p>
              </div>
            ) : (
              clemsMessages.map((msg: ChatMessage) => (
                <div
                  key={msg.message_id}
                  className={`floating-chat-msg ${msg.author === 'operator' ? 'outgoing' : 'incoming'}`}
                >
                  <span className="floating-chat-sender">
                    {msg.author === 'operator' ? 'you' : msg.author}
                  </span>
                  <p className="floating-chat-text">{msg.text}</p>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="floating-chat-input">
            <input
              ref={inputRef}
              type="text"
              placeholder={isSending ? 'Sending...' : 'Message @clems...'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isSending}
            />
            <button
              className="floating-chat-send"
              onClick={handleSend}
              disabled={!input.trim() || isSending}
              aria-label="Send message"
            >
              {isSending ? '...' : 'Send'}
            </button>
          </div>
        </div>
      )}

      <button
        className={`floating-clems-bubble ${hasUnread ? 'has-unread' : ''}`}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? 'Close Clems chat' : 'Open Clems chat'}
        title="Cmd+K"
      >
        {isOpen ? '\u00D7' : 'CL'}
      </button>
    </div>
  )
}
