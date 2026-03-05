export type ChatMode = 'direct' | 'conceal_room'
export type ExecutionMode = 'chat' | 'scene'
export type DeliveryMode = 'ws' | 'http_fallback' | 'hybrid'
export type ApprovalStatus = 'pending' | 'approved' | 'rejected'
export type MessageVisibility = 'operator' | 'internal'

export interface AgentRecord {
  agent_id: string
  name: string
  engine: string
  platform: string
  level: number
  lead_id: string | null
  role: string
  skills: string[]
}

export interface TerminalSession {
  session_id: string
  agent_id: string
  pid: number
  state: string
  cwd: string
  created_at: string
  last_seen_at: string
}

export interface ChatMessage {
  message_id: string
  timestamp: string
  author: string
  text: string
  thread_id: string | null
  priority: string
  tags: string[]
  mentions: string[]
  visibility: MessageVisibility
  metadata: Record<string, unknown>
}

export interface ApprovalRequest {
  request_id: string
  run_id: string
  requester: string
  section_tag: string
  reason: string
  status: ApprovalStatus
  requested_at: string
  decided_by: string | null
  decided_at: string | null
  decision_note: string | null
}

export interface PixelAgentStatus {
  agent_id: string
  name: string
  level: number
  lead_id: string | null
  role: string
  terminal_state: string
  terminal_session_id: string | null
}

export interface PixelFeedResponse {
  project_id: string
  generated_at: string
  terminals_alive: number
  queue_depth: number
  ws_connected: boolean
  l0_count: number
  l1_count: number
  l2_count: number
  agents: PixelAgentStatus[]
}

export interface WsEventEnvelope {
  project_id: string
  timestamp: string
  type: string
  payload: Record<string, unknown>
}

export interface LiveTurnRequest {
  text: string
  chat_mode: ChatMode
  execution_mode?: ExecutionMode
  thread_id?: string | null
  mentions?: string[]
  context_ref?: Record<string, unknown> | null
  section_tag?: string | null
}

export interface LiveTurnResponse {
  run_id: string
  status: string
  messages: ChatMessage[]
  clems_summary: string
  delivery_mode: DeliveryMode
  approval_requests: ApprovalRequest[]
  spawned_agents_count: number
  model_usage: Record<string, unknown>
  error: string | null
}

const API_URL = import.meta.env.VITE_COCKPIT_CORE_URL ?? 'http://127.0.0.1:8787'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      'content-type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    let detail = ''
    try {
      const parsed = await response.json()
      detail = parsed?.error ? `: ${parsed.error}` : ''
    } catch {
      detail = ''
    }
    throw new Error(`Request failed (${response.status})${detail}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export function getApiUrl(): string {
  return API_URL
}

export async function getAgents(projectId: string): Promise<AgentRecord[]> {
  const payload = await request<{ agents: AgentRecord[] }>(`/v1/projects/${projectId}/agents`)
  return payload.agents
}

export async function createAgent(
  projectId: string,
  payload: { agent_id?: string; name?: string; role?: string; cwd?: string },
): Promise<{ agent: AgentRecord; terminal: TerminalSession }> {
  return request(`/v1/projects/${projectId}/agents`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function deleteAgent(projectId: string, agentId: string): Promise<void> {
  await request(`/v1/projects/${projectId}/agents/${agentId}`, {
    method: 'DELETE',
  })
}

export async function openTerminal(
  projectId: string,
  agentId: string,
  cwd?: string,
): Promise<TerminalSession> {
  const payload = await request<{ session: TerminalSession }>(
    `/v1/projects/${projectId}/agents/${agentId}/terminal/open`,
    {
      method: 'POST',
      body: JSON.stringify({ cwd }),
    },
  )
  return payload.session
}

export async function sendTerminalInput(
  projectId: string,
  agentId: string,
  text: string,
): Promise<TerminalSession> {
  const payload = await request<{ session: TerminalSession }>(
    `/v1/projects/${projectId}/agents/${agentId}/terminal/send`,
    {
      method: 'POST',
      body: JSON.stringify({ text }),
    },
  )
  return payload.session
}

export async function restartTerminal(
  projectId: string,
  agentId: string,
  cwd?: string,
): Promise<TerminalSession> {
  const payload = await request<{ session: TerminalSession }>(
    `/v1/projects/${projectId}/agents/${agentId}/terminal/restart`,
    {
      method: 'POST',
      body: JSON.stringify({ cwd }),
    },
  )
  return payload.session
}

export async function liveTurn(projectId: string, payload: LiveTurnRequest): Promise<LiveTurnResponse> {
  return request(`/v1/projects/${projectId}/chat/live-turn`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getApprovals(
  projectId: string,
  status?: ApprovalStatus,
): Promise<{ project_id: string; approvals: ApprovalRequest[] }> {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : ''
  return request(`/v1/projects/${projectId}/chat/approvals${suffix}`)
}

export async function approveApproval(
  projectId: string,
  requestId: string,
  payload: { decided_by?: string; note?: string },
): Promise<{ ok: boolean; approval: ApprovalRequest; spawned_agents_count: number; spawned_agents: string[] }> {
  return request(`/v1/projects/${projectId}/chat/approvals/${requestId}/approve`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function rejectApproval(
  projectId: string,
  requestId: string,
  payload: { decided_by?: string; note?: string },
): Promise<{ ok: boolean; approval: ApprovalRequest }> {
  return request(`/v1/projects/${projectId}/chat/approvals/${requestId}/reject`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getPixelFeed(projectId: string): Promise<PixelFeedResponse> {
  return request(`/v1/projects/${projectId}/pixel-feed`)
}

export async function getChat(
  projectId: string,
  limit = 300,
  visibility: 'operator' | 'all' = 'operator',
): Promise<{ project_id: string; messages: ChatMessage[] }> {
  const payload = await request<{ project_id: string; messages: ChatMessage[] }>(
    `/v1/projects/${projectId}/chat?limit=${limit}&visibility=${visibility}`,
  )
  return {
    project_id: payload.project_id,
    messages: payload.messages
      .filter((row): row is ChatMessage => {
        return Boolean(
          row &&
            typeof row.message_id === 'string' &&
            typeof row.text === 'string' &&
            (row.visibility === 'operator' || row.visibility === 'internal' || row.visibility === undefined),
        )
      })
      .map((row) => ({
        ...row,
        visibility: row.visibility ?? 'operator',
      })),
  }
}

export async function resetChat(
  projectId: string,
): Promise<{
  ok: boolean
  messages_cleared: number
  approvals_cleared: number
  runtime_rows_deleted: number
}> {
  return request(`/v1/projects/${projectId}/chat/reset`, {
    method: 'POST',
  })
}

export async function getLayout(projectId: string): Promise<Record<string, unknown>> {
  return request(`/v1/projects/${projectId}/layout`)
}

export async function putLayout(projectId: string, layout: Record<string, unknown>): Promise<void> {
  await request(`/v1/projects/${projectId}/layout`, {
    method: 'PUT',
    body: JSON.stringify(layout),
  })
}

export function connectEvents(
  projectId: string,
  onEvent: (event: WsEventEnvelope) => void,
  onStatus?: (connected: boolean) => void,
): () => void {
  const url = new URL(`/v1/projects/${projectId}/events`, API_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'

  let closed = false
  let ws: WebSocket | null = null
  let retryTimer: number | null = null

  const connect = () => {
    if (closed) {
      return
    }

    ws = new WebSocket(url.toString())
    ws.addEventListener('open', () => {
      onStatus?.(true)
    })

    ws.addEventListener('message', (event) => {
      try {
        const parsed = JSON.parse(String(event.data)) as WsEventEnvelope
        onEvent(parsed)
      } catch {
        // ignore malformed frames
      }
    })

    ws.addEventListener('close', () => {
      onStatus?.(false)
      if (closed) {
        return
      }
      retryTimer = window.setTimeout(connect, 1200)
    })

    ws.addEventListener('error', () => {
      onStatus?.(false)
      ws?.close()
    })
  }

  connect()

  return () => {
    closed = true
    onStatus?.(false)
    if (retryTimer !== null) {
      window.clearTimeout(retryTimer)
    }
    ws?.close()
  }
}
