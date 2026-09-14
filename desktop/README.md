# Nexus AI — Desktop Layer (Electron)

Secure Windows Electron shell bridging the Nexus AI frontend to desktop capabilities.

## Architecture
- `electron/main.ts`: Application window lifecycle, security policies (`nodeIntegration: false`, `contextIsolation: true`, `sandbox: true`).
- `electron/preload.ts`: Exposes `window.nexusDesktopAPI` via `contextBridge`.
- `electron/ipc/handlers.ts`: Handlers for window controls, OS vitals, desktop notifications, and shell navigation.

## Running Independently
```bash
cd desktop
npm install
npm run build
npm start
```
Loads `http://localhost:5173` (development) or `frontend/dist/index.html` (production bundle).
