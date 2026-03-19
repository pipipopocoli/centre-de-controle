import { useCallback, useEffect, useRef } from 'react'
import {
  useCockpitStore,
  selectActiveChatMode,
} from '../store/index.js'
import {
  liveTurn,
  resetChat,
  transcribeVoice,
} from '../lib/cockpitClient'
import type { ChatMode, VoiceTranscribeResponse } from '../lib/cockpitClient'
import type { DirectTargetMode, RosterAgentView } from '../types.js'
import {
  preferredVoiceRecorder,
  blobToBase64,
  messageChatMode,
  isSyntheticDirectReply,
} from '../lib/formatters.js'

/**
 * Chat send, reset, voice recording, scroll refs and effects.
 */
export function useChatActions({
  refreshApprovals,
  startFallbackPolling,
  wsConnectedRef,
  selectedAgent,
  roomDispatchContext,
  visibleDirectMessages,
  visibleConciergeMessages,
  externalMediaRecorderRef,
  externalMediaStreamRef,
  externalRoomStickToBottomRef,
}: {
  refreshApprovals: () => Promise<void>
  startFallbackPolling: () => void
  wsConnectedRef: React.RefObject<boolean>
  selectedAgent: RosterAgentView | null
  roomDispatchContext: Record<string, unknown>
  visibleDirectMessages: unknown[]
  visibleConciergeMessages: unknown[]
  externalMediaRecorderRef?: React.RefObject<MediaRecorder | null>
  externalMediaStreamRef?: React.RefObject<MediaStream | null>
  externalRoomStickToBottomRef?: React.RefObject<boolean>
}) {
  const projectId = useCockpitStore((s) => s.projectId)
  const directChatInput = useCockpitStore((s) => s.directChatInput)
  const roomChatInput = useCockpitStore((s) => s.roomChatInput)
  const executionMode = useCockpitStore((s) => s.executionMode)
  const directTarget = useCockpitStore((s) => s.directTarget)
  const isSendingChat = useCockpitStore((s) => s.isSendingChat)
  const activeTab = useCockpitStore((s) => s.activeTab)
  const workbenchPanel = useCockpitStore((s) => s.workbenchPanel)
  const directSendPhase = useCockpitStore((s) => s.directSendPhase)
  const isRecordingVoice = useCockpitStore((s) => s.isRecordingVoice)
  const isTranscribingVoice = useCockpitStore((s) => s.isTranscribingVoice)
  const takeoverResult = useCockpitStore((s) => s.takeoverResult)
  const activeChatMode = useCockpitStore(selectActiveChatMode)

  const setDirectChatInput = useCockpitStore((s) => s.setDirectChatInput)
  const setRoomChatInput = useCockpitStore((s) => s.setRoomChatInput)
  const setDirectTarget = useCockpitStore((s) => s.setDirectTarget)
  const setDirectSendPhase = useCockpitStore((s) => s.setDirectSendPhase)
  const setIsSendingChat = useCockpitStore((s) => s.setIsSendingChat)
  const setApiError = useCockpitStore((s) => s.setApiError)
  const setUiNotice = useCockpitStore((s) => s.setUiNotice)
  const setComposerStatus = useCockpitStore((s) => s.setComposerStatus)
  const setFallbackDiagnostics = useCockpitStore((s) => s.setFallbackDiagnostics)
  const mergeChatMessages = useCockpitStore((s) => s.mergeChatMessages)
  const setChatMessages = useCockpitStore((s) => s.setChatMessages)
  const setApprovals = useCockpitStore((s) => s.setApprovals)
  const setIsRecordingVoice = useCockpitStore((s) => s.setIsRecordingVoice)
  const setIsTranscribingVoice = useCockpitStore((s) => s.setIsTranscribingVoice)

  // Voice-related refs (use external if provided, otherwise create internal)
  const internalMediaRecorderRef = useRef<MediaRecorder | null>(null)
  const internalMediaStreamRef = useRef<MediaStream | null>(null)
  const mediaRecorderRef = externalMediaRecorderRef ?? internalMediaRecorderRef
  const mediaStreamRef = externalMediaStreamRef ?? internalMediaStreamRef
  const voiceChunksRef = useRef<Blob[]>([])
  const voiceFormatRef = useRef('ogg')

  // Chat scroll refs
  const directChatLogRef = useRef<HTMLDivElement>(null)
  const roomChatLogRef = useRef<HTMLDivElement>(null)
  const directStickToBottomRef = useRef(true)
  const internalRoomStickToBottomRef = useRef(true)
  const roomStickToBottomRef = externalRoomStickToBottomRef ?? internalRoomStickToBottomRef
  const directRetryTimerRef = useRef<number | null>(null)

  // Direct chat scroll effect
  useEffect(() => {
    if (!directChatLogRef.current || !directStickToBottomRef.current) {
      return
    }
    directChatLogRef.current.scrollTop = directChatLogRef.current.scrollHeight
  }, [visibleDirectMessages.length, workbenchPanel, activeTab, directSendPhase])

  // Room chat scroll effect
  useEffect(() => {
    if (!roomChatLogRef.current || !roomStickToBottomRef.current) {
      return
    }
    roomChatLogRef.current.scrollTop = roomChatLogRef.current.scrollHeight
  }, [visibleConciergeMessages.length, activeTab, takeoverResult?.run_id, roomStickToBottomRef])

  // Cleanup direct retry timer on unmount
  useEffect(() => {
    return () => {
      if (directRetryTimerRef.current !== null) {
        window.clearTimeout(directRetryTimerRef.current)
      }
    }
  }, [])

  const handleSendChat = useCallback(async ({
    targetMode = directTarget,
    chatMode = activeChatMode,
    contextRef = null,
  }: {
    targetMode?: DirectTargetMode
    chatMode?: ChatMode
    contextRef?: Record<string, unknown> | null
  } = {}) => {
    const activeInput = chatMode === 'conceal_room' ? roomChatInput : directChatInput
    const text = activeInput.trim()
    if (!text || isSendingChat) {
      return
    }

    if (chatMode === 'conceal_room') {
      roomStickToBottomRef.current = true
    } else {
      directStickToBottomRef.current = true
    }

    let resolvedTargetMode = targetMode
    let targetAgentId =
      chatMode === 'direct' && resolvedTargetMode === 'selected_agent'
        ? (selectedAgent?.chat_targetable ? selectedAgent.agent_id : null)
        : null

    if (chatMode === 'direct' && resolvedTargetMode === 'selected_agent' && !targetAgentId) {
      resolvedTargetMode = 'clems'
      targetAgentId = null
      setDirectTarget('clems')
      setUiNotice('selected agent not chat-ready. direct chat stays on @clems.')
    }

    if (chatMode === 'conceal_room') {
      setRoomChatInput('')
    } else {
      setDirectChatInput('')
      setDirectSendPhase('thinking')
      if (directRetryTimerRef.current !== null) {
        window.clearTimeout(directRetryTimerRef.current)
      }
      directRetryTimerRef.current = window.setTimeout(() => {
        setDirectSendPhase((previous) => (previous === 'thinking' ? 'retrying' : previous))
      }, 10000)
    }
    setApiError(null)
    setUiNotice(null)
    setIsSendingChat(true)
    if (chatMode === 'direct') {
      setDirectTarget(resolvedTargetMode)
    }

    let keepDirectDegradedState = false

    try {
      const response = await liveTurn(projectId, {
        text,
        chat_mode: chatMode,
        execution_mode: executionMode,
        target_agent_id: targetAgentId,
        mentions: chatMode === 'conceal_room' ? ['clems'] : undefined,
        context_ref: chatMode === 'conceal_room' ? (contextRef ?? roomDispatchContext) : contextRef,
      })

      mergeChatMessages(response.messages)
      if (response.approval_requests.length > 0) {
        void refreshApprovals()
      }

      if (response.error) {
        const hasVisibleReply = response.messages.some(
          (message) =>
            message.visibility !== 'internal' &&
            message.author !== 'operator' &&
            messageChatMode(message) === chatMode &&
            (chatMode !== 'direct' || !isSyntheticDirectReply(message)),
        )

        setFallbackDiagnostics((previous) => [
          {
            id: `${Date.now()}-${chatMode}`,
            timestamp: new Date().toISOString(),
            chatMode,
            error: response.error ?? 'unknown_chat_error',
          },
          ...previous,
        ].slice(0, 12))

        if (response.error === 'some_llm_calls_failed_using_fallback' && hasVisibleReply) {
          // Keep the main chat surface quiet when a visible reply already exists.
        } else if (chatMode === 'direct' && !hasVisibleReply) {
          setDirectChatInput(text)
          setDirectSendPhase('degraded')
          keepDirectDegradedState = true
          setUiNotice('OpenRouter degraded, direct reply unavailable. Retry or switch to Le Conseil.')
        } else {
          setUiNotice(`degraded mode: ${response.error}`)
        }
      }

      if (!wsConnectedRef.current || response.delivery_mode !== 'ws') {
        startFallbackPolling()
      } else {
        setComposerStatus('live')
      }
    } catch (error) {
      if (chatMode === 'conceal_room') {
        setRoomChatInput(text)
      } else {
        setDirectChatInput(text)
      }
      setApiError(error instanceof Error ? error.message : String(error))
      setUiNotice('send failed. draft restored.')
    } finally {
      if (directRetryTimerRef.current !== null) {
        window.clearTimeout(directRetryTimerRef.current)
        directRetryTimerRef.current = null
      }
      if (chatMode === 'direct' && !keepDirectDegradedState) {
        setDirectSendPhase(null)
      }
      setIsSendingChat(false)
    }
  }, [
    activeChatMode,
    directChatInput,
    directTarget,
    executionMode,
    isSendingChat,
    mergeChatMessages,
    projectId,
    refreshApprovals,
    roomChatInput,
    roomDispatchContext,
    selectedAgent,
    startFallbackPolling,
    setApiError,
    setComposerStatus,
    setDirectChatInput,
    setDirectSendPhase,
    setDirectTarget,
    setFallbackDiagnostics,
    setIsSendingChat,
    setRoomChatInput,
    setUiNotice,
    wsConnectedRef,
    roomStickToBottomRef,
  ])

  const handleResetChat = useCallback(async () => {
    if (!window.confirm('Reset chat now? This clears global chat and approvals history.')) {
      return
    }

    setApiError(null)
    setUiNotice(null)
    try {
      await resetChat(projectId)
      setChatMessages([])
      setApprovals([])
      setUiNotice('chat reset complete')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : String(error))
    }
  }, [projectId, setApiError, setApprovals, setChatMessages, setUiNotice])

  const handleToggleVoiceRecording = useCallback(async () => {
    if (isTranscribingVoice) {
      return
    }

    if (isRecordingVoice) {
      mediaRecorderRef.current?.stop()
      setIsRecordingVoice(false)
      return
    }

    const preferred = preferredVoiceRecorder()
    if (!preferred) {
      setApiError('voice capture unsupported in this webview')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream
      voiceChunksRef.current = []
      voiceFormatRef.current = preferred.format

      const recorder = new MediaRecorder(stream, { mimeType: preferred.mimeType })
      mediaRecorderRef.current = recorder
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          voiceChunksRef.current.push(event.data)
        }
      }
      recorder.onstop = () => {
        const chunks = [...voiceChunksRef.current]
        voiceChunksRef.current = []
        mediaRecorderRef.current = null
        if (mediaStreamRef.current) {
          for (const track of mediaStreamRef.current.getTracks()) {
            track.stop()
          }
          mediaStreamRef.current = null
        }

        if (chunks.length === 0) {
          return
        }

        void (async () => {
          setIsTranscribingVoice(true)
          setApiError(null)
          try {
            const blob = new Blob(chunks, { type: preferred.mimeType })
            const audioBase64 = await blobToBase64(blob)
            const response: VoiceTranscribeResponse = await transcribeVoice(projectId, {
              audio_base64: audioBase64,
              format: voiceFormatRef.current,
            })
            if (response.status !== 'ok') {
              throw new Error(response.error || 'voice transcription failed')
            }
            const appendTranscript = activeTab === 'concierge_room' ? setRoomChatInput : setDirectChatInput
            appendTranscript((previous) => {
              const prefix = previous.trim()
              if (!prefix) {
                return response.text
              }
              return `${prefix}\n${response.text}`
            })
            setUiNotice(`voice transcribed via ${response.model}`)
          } catch (error) {
            setApiError(error instanceof Error ? error.message : String(error))
          } finally {
            setIsTranscribingVoice(false)
          }
        })()
      }
      recorder.start()
      setIsRecordingVoice(true)
      setUiNotice('recording voice message')
    } catch (error) {
      if (mediaStreamRef.current) {
        for (const track of mediaStreamRef.current.getTracks()) {
          track.stop()
        }
        mediaStreamRef.current = null
      }
      setApiError(error instanceof Error ? error.message : String(error))
    }
  }, [
    activeTab,
    isRecordingVoice,
    isTranscribingVoice,
    projectId,
    setApiError,
    setDirectChatInput,
    setIsRecordingVoice,
    setIsTranscribingVoice,
    setRoomChatInput,
    setUiNotice,
    mediaRecorderRef,
    mediaStreamRef,
  ])

  return {
    handleSendChat,
    handleResetChat,
    handleToggleVoiceRecording,
    mediaRecorderRef,
    mediaStreamRef,
    voiceChunksRef,
    voiceFormatRef,
    directChatLogRef,
    roomChatLogRef,
    directStickToBottomRef,
    roomStickToBottomRef,
    directRetryTimerRef,
  }
}
