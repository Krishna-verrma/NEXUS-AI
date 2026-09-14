import { ipcMain, BrowserWindow, Notification, shell } from 'electron';
import os from 'os';
import http from 'http';

export function registerIpcHandlers(mainWindow: BrowserWindow) {
  // Window controls
  ipcMain.handle('window:minimize', () => {
    if (mainWindow) mainWindow.minimize();
  });

  ipcMain.handle('window:maximize', () => {
    if (mainWindow) {
      if (mainWindow.isMaximized()) {
        mainWindow.unmaximize();
      } else {
        mainWindow.maximize();
      }
    }
  });

  ipcMain.handle('window:close', () => {
    if (mainWindow) mainWindow.close();
  });

  // OS Info
  ipcMain.handle('system:get-info', () => {
    return {
      platform: os.platform(),
      release: os.release(),
      arch: os.arch(),
      totalMemGb: Math.round(os.totalmem() / (1024 ** 3)),
      freeMemGb: Math.round(os.freemem() / (1024 ** 3)),
      cpus: os.cpus().length,
      hostname: os.hostname(),
    };
  });

  // Desktop Notification
  ipcMain.handle('desktop:notify', (_event, title: string, body: string) => {
    if (Notification.isSupported()) {
      new Notification({ title, body }).show();
      return true;
    }
    return false;
  });

  // Open External Link safely in default browser
  ipcMain.handle('shell:open-external', async (_event, url: string) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      await shell.openExternal(url);
      return true;
    }
    return false;
  });

  // Check Backend Health
  ipcMain.handle('backend:check-health', () => {
    return new Promise((resolve) => {
      const req = http.get('http://127.0.0.1:8000/api/system/health', (res) => {
        resolve(res.statusCode === 200);
      });
      req.on('error', () => resolve(false));
      req.setTimeout(1500, () => {
        req.destroy();
        resolve(false);
      });
    });
  });
}
