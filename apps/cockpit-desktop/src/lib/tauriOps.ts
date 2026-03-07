export async function openOsTerminal(agentId: string, cwd?: string): Promise<void> {
  const mod = await import('@tauri-apps/api/core')
  await mod.invoke('open_os_terminal', { agentId, cwd })
}

export async function pickProjectFolder(): Promise<string | null> {
  try {
    const mod = await import('@tauri-apps/api/core')
    const picked = await mod.invoke<string | null>('pick_project_folder')
    if (typeof picked === 'string' && picked.trim()) {
      return picked
    }
  } catch {
    // fallback to the dialog plugin below
  }

  try {
    const dialog = await import('@tauri-apps/plugin-dialog')
    const picked = await dialog.open({
      directory: true,
      multiple: false,
      title: 'Select a project folder for Cockpit',
    })
    if (typeof picked === 'string' && picked.trim()) {
      return picked
    }
  } catch {
    // fallback to the local Tauri command below
  }

  return null
}
