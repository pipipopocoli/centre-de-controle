export async function openOsTerminal(agentId: string, cwd?: string): Promise<void> {
  const tauri = (window as unknown as { __TAURI__?: unknown }).__TAURI__
  if (!tauri) {
    return
  }

  const mod = await import('@tauri-apps/api/core')
  await mod.invoke('open_os_terminal', { agentId, cwd })
}
