const { contextBridge, ipcRenderer } = require('electron');

// Secure context bridge exposing safe IPC APIs to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),
  getAppVersion: () => ipcRenderer.invoke('app:getVersion'),
  openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
  platform: process.platform,
});
