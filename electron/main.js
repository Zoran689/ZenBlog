const { app, BrowserWindow, Menu, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

let mainWindow = null;
let backendProcess = null;
const BACKEND_PORT = 8877;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;

// ── 判断是否打包环境 ──────────────────────────────────
const isPacked = app.isPackaged;
const APP_ROOT = isPacked
  ? path.dirname(app.getPath('exe'))
  : path.join(__dirname, '..');

// Python 可执行文件路径（打包后使用 PyInstaller 产物）
function getPythonPath() {
  if (!isPacked) return 'python3'; // 开发环境直接用系统 python

  const platform = process.platform;
  const distDir = path.join(process.resourcesPath, 'python-dist');

  if (platform === 'darwin') {
    // macOS: PyInstaller 单文件
    const macPath = path.join(distDir, 'zenblog_backend');
    if (fs.existsSync(macPath)) return macPath;
    // 或者 one-folder 模式
    const macFolder = path.join(distDir, 'zenblog_backend', 'zenblog_backend');
    if (fs.existsSync(macFolder)) return macFolder;
  } else if (platform === 'win32') {
    const winPath = path.join(distDir, 'zenblog_backend', 'zenblog_backend.exe');
    if (fs.existsSync(winPath)) return winPath;
  }

  // 兜底：尝试直接找 python-dist 下的可执行文件
  const fallback = path.join(distDir, 'zenblog_backend');
  if (fs.existsSync(fallback)) return fallback;
  if (fs.existsSync(fallback + '.exe')) return fallback + '.exe';

  return 'python3';
}

// ── 后端脚本路径 ──────────────────────────────────────
function getBackendScript() {
  if (isPacked) {
    // 打包后脚本在 resources/app 下
    return path.join(process.resourcesPath, 'app', 'zenblog_backend.py');
  }
  return path.join(__dirname, '..', 'zenblog_backend.py');
}

// ── 等待后端就绪 ──────────────────────────────────────
function waitForBackend(retries = 30, interval = 500) {
  return new Promise((resolve, reject) => {
    const check = (attempt) => {
      http.get(`${BACKEND_URL}/`, (res) => {
        resolve(true);
      }).on('error', () => {
        if (attempt >= retries) {
          reject(new Error('后端启动超时'));
        } else {
          setTimeout(() => check(attempt + 1), interval);
        }
      });
    };
    check(0);
  });
}

// ── 启动后端 Python 进程 ──────────────────────────────
function startBackend() {
  const pythonPath = getPythonPath();
  const scriptPath = getBackendScript();

  console.log(`[ZenBlog] 启动后端: ${pythonPath} ${scriptPath}`);
  console.log(`[ZenBlog] 工作目录: ${APP_ROOT}`);

  // 确保 data 目录存在
  const dataDir = path.join(APP_ROOT, 'data');
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  backendProcess = spawn(pythonPath, [scriptPath], {
    cwd: APP_ROOT,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
    },
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Backend ERR] ${data.toString().trim()}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`[Backend] 进程退出，code=${code}`);
    backendProcess = null;
  });

  backendProcess.on('error', (err) => {
    console.error(`[Backend] 启动失败:`, err.message);
    backendProcess = null;
  });
}

// ── 停止后端 ──────────────────────────────────────────
function stopBackend() {
  if (backendProcess) {
    console.log('[ZenBlog] 停止后端...');
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t']);
    } else {
      backendProcess.kill('SIGTERM');
      setTimeout(() => {
        if (backendProcess) {
          backendProcess.kill('SIGKILL');
        }
      }, 3000);
    }
    backendProcess = null;
  }
}

// ── 创建主窗口 ────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: 'ZenBlog',
    icon: path.join(APP_ROOT, 'logo.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    show: false,
  });

  // 加载后端页面
  mainWindow.loadURL(BACKEND_URL);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 构建菜单
  const menuTemplate = [
    {
      label: 'ZenBlog',
      submenu: [
        { role: 'about', label: '关于 ZenBlog' },
        { type: 'separator' },
        { role: 'quit', label: '退出' },
      ],
    },
    {
      label: '编辑',
      submenu: [
        { role: 'undo', label: '撤销' },
        { role: 'redo', label: '重做' },
        { type: 'separator' },
        { role: 'cut', label: '剪切' },
        { role: 'copy', label: '复制' },
        { role: 'paste', label: '粘贴' },
        { role: 'selectAll', label: '全选' },
      ],
    },
    {
      label: '视图',
      submenu: [
        { role: 'reload', label: '刷新' },
        { role: 'toggleDevTools', label: '开发者工具' },
        { type: 'separator' },
        { role: 'zoomIn', label: '放大' },
        { role: 'zoomOut', label: '缩小' },
        { role: 'resetZoom', label: '重置缩放' },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(menuTemplate);
  Menu.setApplicationMenu(menu);
}

// ── 应用生命周期 ──────────────────────────────────────
app.whenReady().then(async () => {
  // 启动后端
  startBackend();

  try {
    // 等待后端就绪
    await waitForBackend();
    console.log('[ZenBlog] 后端就绪');
  } catch (err) {
    console.error('[ZenBlog] 后端启动失败:', err.message);
    dialog.showErrorBox(
      '启动失败',
      `ZenBlog 后端服务启动失败，请确保已安装 Python 3 和依赖。\n\n错误: ${err.message}`
    );
    app.quit();
    return;
  }

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

app.on('before-quit', () => {
  stopBackend();
});

app.on('will-quit', () => {
  stopBackend();
});
