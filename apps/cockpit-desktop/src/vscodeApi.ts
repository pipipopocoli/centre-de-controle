export type OfficeBridgeMessage = {
  type: string
  [key: string]: unknown
}

declare global {
  interface Window {
    acquireVsCodeApi?: () => { postMessage: (msg: unknown) => void }
  }
}

const fallback = {
  postMessage(msg: unknown) {
    window.dispatchEvent(
      new CustomEvent<OfficeBridgeMessage>('cockpit-office-message', {
        detail: (msg as OfficeBridgeMessage) ?? { type: 'unknown' },
      }),
    )
  },
}

export const vscode = window.acquireVsCodeApi ? window.acquireVsCodeApi() : fallback
