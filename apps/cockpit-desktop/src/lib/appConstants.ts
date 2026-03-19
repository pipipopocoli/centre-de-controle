import type { TaskStatus } from './cockpitClient'

export const DEFAULT_PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID ?? 'cockpit'

export const STATUS_ORDER: TaskStatus[] = ['todo', 'in_progress', 'blocked', 'done']
export const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'Todo',
  in_progress: 'In Progress',
  blocked: 'Blocked',
  done: 'Done',
}

export const CLEMS_MODEL_OPTIONS = [
  { id: 'moonshotai/kimi-k2.5', label: 'Kimi K2.5', note: 'default L0' },
  { id: 'anthropic/claude-sonnet-4.6', label: 'Claude Sonnet 4.6', note: 'higher reasoning' },
  { id: 'anthropic/claude-opus-4.6', label: 'Claude Opus 4.6', note: 'max depth' },
] as const

export const L1_MODEL_OPTIONS = [
  { id: 'moonshotai/kimi-k2.5', label: 'Kimi K2.5', note: 'fast default' },
  { id: 'anthropic/claude-sonnet-4.6', label: 'Claude Sonnet 4.6', note: 'strong lead' },
  { id: 'anthropic/claude-opus-4.6', label: 'Claude Opus 4.6', note: 'max depth' },
  { id: 'openai/gpt-5.4', label: 'GPT-5.4', note: 'broad reasoning' },
  { id: 'google/gemini-3.1-pro-preview', label: 'Gemini 3.1 Pro Preview', note: 'wide context' },
  { id: 'x-ai/grok-4', label: 'Grok 4', note: 'current OpenRouter grok 4.x entry' },
] as const

export const L2_MODEL_OPTIONS = [
  { id: 'minimax/minimax-m2.5', label: 'MiniMax M2.5', note: 'surgical primary' },
  { id: 'moonshotai/kimi-k2.5', label: 'Kimi K2.5', note: 'precise fallback' },
  { id: 'deepseek/deepseek-chat-v3.1', label: 'DeepSeek Chat V3.1', note: 'bounded execution' },
] as const

export const PREFERRED_AGENT_ORDER = ['clems', 'victor', 'leo', 'nova', 'vulgarisation'] as const

export const QUICK_AGENT_PRESETS = [
  { agent_id: 'clems', label: 'Clems' },
  { agent_id: 'victor', label: 'Victor' },
  { agent_id: 'leo', label: 'Leo' },
  { agent_id: 'nova', label: 'Nova' },
  { agent_id: 'vulgarisation', label: 'Vulgarisation' },
] as const

export const VOICE_STT_OPTIONS = [
  'google/gemini-2.5-flash',
  'openai/gpt-4o-mini-transcribe',
] as const
