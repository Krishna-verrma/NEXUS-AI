import { app, BrowserWindow } from 'electron';
import path from 'path';
import { registerIpcHandlers } from './ipc/handlers';

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 1024,
    minHeight: 700,
    title: 'Nexus AI — Intelligent Desktop Operating Layer',
    backgroundColor: '#080B11',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });

  registerIpcHandlers(mainWindow);

  // Load frontend dev server or built production bundle
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  const devUrl = 'http://localhost:5173';
  const prodPath = path.join(__dirname, '../../frontend/dist/index.html');

  if (isDev) {
    mainWindow.loadURL(devUrl).catch(() => {
      // Fallback to local production build if dev server is not active
      mainWindow?.loadFile(prodPath).catch(() => {
        console.log('[Nexus Electron] Awaiting frontend dev server at http://localhost:5173...');
      });
    });
  } else {
    mainWindow.loadFile(prodPath);
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
