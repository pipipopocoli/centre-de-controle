export async function openOsTerminal(agentId: string, cwd?: string): Promise<void> {
  const mod = await import('@tauri-apps/api/core')
  await mod.invoke('open_os_terminal', { agentId, cwd })
}

export async function pickProjectFolder(): Promise<string | null> {
  const mod = await import('@tauri-apps/api/core')
  return await mod.invoke<string | null>('pick_project_folder')
}
