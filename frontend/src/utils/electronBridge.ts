export interface ElectronBridge {
  openFileDialog?: (options?: any) => Promise<string[] | null>;
  openExternal?: (url: string) => Promise<void>;
  getAppVersion?: () => Promise<string>;
  platform?: string;
}

declare global {
  interface Window {
    electronAPI?: ElectronBridge;
  }
}

export const isElectron = (): boolean => {
  return typeof window !== 'undefined' && Boolean(window.electronAPI);
};

export const openNativeFileDialog = async (): Promise<string[] | null> => {
  if (isElectron() && window.electronAPI?.openFileDialog) {
    return await window.electronAPI.openFileDialog();
  }
  return null;
};

export const openExternalLink = async (url: string): Promise<void> => {
  if (isElectron() && window.electronAPI?.openExternal) {
    await window.electronAPI.openExternal(url);
  } else {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
};
