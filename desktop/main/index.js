const { app, BrowserWindow, ipcMain, dialog, shell, Notification } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const http = require('http');

const fs = require('fs');

let mainWindow = null;
let backendProcess = null;
const BACKEND_PORT = 8000;
const IS_DEV = process.env.NODE_ENV === 'development' || !(app && app.isPackaged);

process.on('uncaughtException', (err) => {
  console.error('[Electron Uncaught Exception]', err);
  if (err && err.code === 'ENOENT') {
    console.warn('[Electron] Handled ENOENT spawn error gracefully.');
    return;
  }
});

function checkBackendHealth(timeoutMs = 1000) {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/api/health`, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(timeoutMs, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function resolveBackendEnvironment() {
  const rootDir = path.resolve(__dirname, '../..');
  const userWorkspace = 'C:\\Users\\Krishna Verma\\.gemini\\antigravity\\scratch\\nexus-ai';

  // Candidate pairs of [pythonExecutable, backendDirectory]
  const candidatePairs = [
    // 1. Packaged extraResources in production
    [
      path.join(process.resourcesPath, 'backend', 'venv', 'Scripts', 'python.exe'),
      path.join(process.resourcesPath, 'backend')
    ],
    // 2. Local relative dev environment
    [
      path.join(rootDir, 'backend', 'venv', 'Scripts', 'python.exe'),
      path.join(rootDir, 'backend')
    ],
    // 3. User workspace repository
    [
      path.join(userWorkspace, 'backend', 'venv', 'Scripts', 'python.exe'),
      path.join(userWorkspace, 'backend')
    ],
    // 4. System Python 3.14 with backend directories
    [
      'C:\\Python314\\python.exe',
      path.join(process.resourcesPath, 'backend')
    ],
    [
      'C:\\Python314\\python.exe',
      path.join(rootDir, 'backend')
    ],
    [
      'C:\\Python314\\python.exe',
      path.join(userWorkspace, 'backend')
    ]
  ];

  for (const [pyPath, bDir] of candidatePairs) {
    if (fs.existsSync(pyPath) && fs.existsSync(bDir)) {
      console.log(`[Electron] Found valid Python backend pair: ${pyPath} -> ${bDir}`);
      return { pythonPath: pyPath, backendDir: bDir };
    }
  }

  // Fallback: search system PATH safely via where.exe
  if (process.platform === 'win32') {
    try {
      const output = execSync('where.exe python', { encoding: 'utf-8' });
      const paths = output.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
      for (const p of paths) {
        if (fs.existsSync(p) && !p.toLowerCase().includes('windowsapps')) {
          const fallbackDirs = [
            path.join(process.resourcesPath, 'backend'),
            path.join(rootDir, 'backend'),
            path.join(userWorkspace, 'backend')
          ];
          for (const fd of fallbackDirs) {
            if (fs.existsSync(fd)) {
              console.log(`[Electron] Discovered system Python: ${p} with dir: ${fd}`);
              return { pythonPath: p, backendDir: fd };
            }
          }
        }
      }
    } catch (err) {
      console.warn('[Electron] Could not query where.exe python:', err.message);
    }
  }

  return null;
}

async function startBackend() {
  // Check if backend is already alive before attempting to spawn
  const alreadyRunning = await checkBackendHealth(800);
  if (alreadyRunning) {
    console.log(`[Electron] Backend is already running on port ${BACKEND_PORT}. Attaching to existing instance.`);
    return;
  }

  const envInfo = resolveBackendEnvironment();
  if (!envInfo) {
    console.warn('[Electron] No valid Python backend environment could be resolved.');
    return;
  }

  const { pythonPath, backendDir } = envInfo;
  console.log(`[Electron] Launching Python backend: ${pythonPath} in ${backendDir}`);

  try {
    backendProcess = spawn(
      pythonPath,
      ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)],
      {
        cwd: backendDir,
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true,
        env: {
          ...process.env,
          PYTHONPATH: backendDir,
          PYTHONUNBUFFERED: '1'
        }
      }
    );

    // CRITICAL: Prevent unhandled spawn error crashes (e.g. ENOENT)
    backendProcess.on('error', (err) => {
      console.error('[Electron] Backend process spawn error:', err.message);
      backendProcess = null;
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`[FastAPI stdout] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`[FastAPI stderr] ${data.toString().trim()}`);
    });

    backendProcess.on('exit', (code) => {
      console.log(`[FastAPI] Backend exited with code ${code}`);
      backendProcess = null;
    });
  } catch (err) {
    console.error('[Electron] Failed to spawn backend:', err.message);
  }
}

function stopBackend() {
  if (reminderInterval) {
    clearInterval(reminderInterval);
    reminderInterval = null;
  }
  if (backendProcess && backendProcess.pid) {
    console.log(`[Electron] Stopping backend PID: ${backendProcess.pid}`);
    try {
      if (process.platform === 'win32') {
        execSync(`taskkill /pid ${backendProcess.pid} /T /F`);
      } else {
        backendProcess.kill('SIGTERM');
      }
    } catch (e) {
      console.warn('Error killing backend process:', e.message);
    }
    backendProcess = null;
  }
}

function waitForBackend(callback, retries = 25) {
  checkBackendHealth(500).then((healthy) => {
    if (healthy) {
      console.log('[Electron] Backend healthcheck passed.');
      callback(true);
    } else if (retries > 0) {
      setTimeout(() => waitForBackend(callback, retries - 1), 400);
    } else {
      console.warn('[Electron] Backend healthcheck timed out. Proceeding to load UI.');
      callback(false);
    }
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 880,
    minWidth: 1080,
    minHeight: 700,
    backgroundColor: '#07090e',
    title: 'NEXUS AI | Multi-Agent Command Center',
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
    show: false,
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  if (IS_DEV && process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    const distPath = path.join(__dirname, '../../frontend/dist/index.html');
    mainWindow.loadFile(distPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Register IPC Handlers
ipcMain.handle('dialog:openFile', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'All Supported Files', extensions: ['csv', 'xlsx', 'json', 'pdf', 'docx', 'txt', 'py', 'sql', 'cpp', 'java', 'js', 'ts'] },
      { name: 'Tabular Data', extensions: ['csv', 'xlsx', 'json'] },
      { name: 'Documents', extensions: ['pdf', 'docx', 'txt', 'md'] },
      { name: 'Code Files', extensions: ['py', 'sql', 'cpp', 'java', 'js', 'ts'] }
    ]
  });
  return result.canceled ? null : result.filePaths;
});

ipcMain.handle('app:getVersion', () => {
  return app.getVersion();
});

ipcMain.handle('shell:openExternal', async (_, url) => {
  if (url.startsWith('http://') || url.startsWith('https://')) {
    await shell.openExternal(url);
  }
});

// Native Windows Meeting Reminder Service
const alertedMeetings = new Set();
let reminderInterval = null;

function startReminderService() {
  if (reminderInterval) clearInterval(reminderInterval);

  reminderInterval = setInterval(() => {
    const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/api/calendar/today`, (res) => {
      let raw = '';
      res.on('data', chunk => { raw += chunk; });
      res.on('end', () => {
        try {
          const data = JSON.parse(raw);
          const next = data.next_meeting;
          if (next && next.starts_in_minutes !== undefined) {
            // Alert when meeting starts in <= 15 minutes
            if (next.starts_in_minutes >= 0 && next.starts_in_minutes <= 15 && !alertedMeetings.has(next.id)) {
              alertedMeetings.add(next.id);
              if (Notification.isSupported()) {
                const timePart = next.start_time.slice(11, 16);
                const notif = new Notification({
                  title: `Upcoming Meeting (${next.starts_in_minutes}m): ${next.title}`,
                  body: `Starts at ${timePart} • ${next.location || 'Virtual Conference'}\nClick to join call.`,
                  silent: false
                });

                notif.on('click', () => {
                  if (next.join_url) {
                    shell.openExternal(next.join_url);
                  } else if (mainWindow) {
                    if (mainWindow.isMinimized()) mainWindow.restore();
                    mainWindow.show();
                    mainWindow.focus();
                  }
                });

                notif.show();
              }
            }
          }
        } catch (e) {}
      });
    });
    req.on('error', () => {});
    req.setTimeout(2500, () => req.destroy());
  }, 30000);
}

// App Lifecycle
app.whenReady().then(() => {
  startBackend();
  waitForBackend(() => {
    createWindow();
    startReminderService();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
