# Nexus AI — Desktop Integration & Security

Electron provides a native Windows desktop container without compromising browser sandbox isolation.

## Security Architecture
- `nodeIntegration: false`: Renderer has zero access to Node.js built-ins (`fs`, `child_process`).
- `contextIsolation: true`: Renderer and preload run in isolated contexts.
- `sandbox: true`: Chromium process sandboxing enabled.
- Typed `window.nexusDesktopAPI`:
  - `minimizeWindow()`
  - `maximizeWindow()`
  - `closeWindow()`
  - `getSystemInfo()`
  - `showNotification(title, body)`
  - `openExternal(url)`
  - `checkBackendHealth()`

## IPC Channel Whitelist
Only explicitly declared channels in `desktop/electron/ipc/handlers.ts` receive message events from the renderer.
