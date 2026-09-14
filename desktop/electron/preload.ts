import { contextBridge, ipcRenderer } from 'electron';

export interface NexusDesktopAPI {
  minimizeWindow: () => Promise<void>;
  maximizeWindow: () => Promise<void>;
  closeWindow: () => Promise<void>;
  getSystemInfo: () => Promise<{
    platform: string;
    release: string;
    arch: string;
    totalMemGb: number;
    freeMemGb: number;
    cpus: number;
    hostname: string;
  }>;
  showNotification: (title: string, body: string) => Promise<boolean>;
  openExternal: (url: string) => Promise<boolean>;
  checkBackendHealth: () => Promise<boolean>;
}

const desktopAPI: NexusDesktopAPI = {
  minimizeWindow: () => ipcRenderer.invoke('window:minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window:maximize'),
  closeWindow: () => ipcRenderer.invoke('window:close'),
  getSystemInfo: () => ipcRenderer.invoke('system:get-info'),
  showNotification: (title: string, body: string) => ipcRenderer.invoke('desktop:notify', title, body),
  openExternal: (url: string) => ipcRenderer.invoke('shell:open-external', url),
  checkBackendHealth: () => ipcRenderer.invoke('backend:check-health'),
};

contextBridge.exposeInMainWorld('nexusDesktopAPI', desktopAPI);
