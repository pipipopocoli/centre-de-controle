export async function openOsTerminal(agentId: string, cwd?: string): Promise<void> {
  const tauri = (window as unknown as { __TAURI__?: unknown }).__TAURI__
  if (!tauri) {
    return
  }

  const mod = await import('@tauri-apps/api/core')
  await mod.invoke('open_os_terminal', { agentId, cwd })
}

export async function pickProjectFolder(): Promise<string | null> {
  const tauri = (window as unknown as { __TAURI__?: unknown }).__TAURI__
  if (!tauri) {
    throw new Error('native folder picker unavailable outside Cockpit desktop')
  }

  const mod = await import('@tauri-apps/api/core')
  return await mod.invoke<string | null>('pick_project_folder')
}
