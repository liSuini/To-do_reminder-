// 待办助手 Electron 主进程：窗口生命周期 + Python 后端子进程管理
// 约定（架构设计 §4）：后端启动后把实际端口写入 backend.port，主进程轮询 /api/health 就绪后加载页面
const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const http = require("http");

// 打包形态（electron-builder 运行）时资源在 process.resourcesPath
const IS_PACKAGED = !!process.resourcesPath && !process.defaultApp;
const PYTHON_EXE = "D:\\developTools\\python\\python3.14.5\\python.exe";
const DEV_BACKEND = path.join(__dirname, "..", "backend", "start_dev.py");
const PACKAGED_BACKEND = path.join(process.resourcesPath || "", "backend", "todo_backend.exe");
const PORT_FILE = IS_PACKAGED
  ? path.join(process.resourcesPath, "backend", "backend.port")
  : path.join(__dirname, "..", "backend", "backend.port");

let backendProc = null;

function startBackend() {
  const [cmd, args] = IS_PACKAGED
    ? [PACKAGED_BACKEND, []]
    : [PYTHON_EXE, ["-X", "utf8", DEV_BACKEND]];
  backendProc = spawn(cmd, args, { windowsHide: true });
  backendProc.stdout.on("data", (d) => console.log("[backend]", String(d).trim()));
  backendProc.stderr.on("data", (d) => console.log("[backend-err]", String(d).trim()));
}

function waitHealthy(port, timeoutMs = 20000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const poll = () => {
      const req = http.get(`http://127.0.0.1:${port}/api/health`, (res) => {
        res.resume();
        if (res.statusCode === 200) resolve(port);
        else retry();
      });
      req.on("error", retry);
      req.setTimeout(1000, () => {
        req.destroy();
        retry();
      });
    };
    const retry = () => {
      if (Date.now() - start > timeoutMs) reject(new Error("后端健康检查超时"));
      else setTimeout(poll, 300);
    };
    poll();
  });
}

async function readPortWithRetry(spawnTimeMs) {
  // 等待「本次 spawn 之后」写入的端口文件，避免读到上一轮遗留的旧端口
  for (let i = 0; i < 66; i++) {
    if (fs.existsSync(PORT_FILE)) {
      const stat = fs.statSync(PORT_FILE);
      if (stat.mtimeMs >= spawnTimeMs - 2000) {
        const port = parseInt(fs.readFileSync(PORT_FILE, "utf-8").trim(), 10);
        if (port > 0) return port;
      }
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error("backend.port 文件未出现（或未更新）");
}

async function createWindow() {
  const spawnTime = Date.now();
  startBackend();
  const port = await readPortWithRetry(spawnTime);
  await waitHealthy(port);
  console.log("[main] backend ready on port", port);

  const win = new BrowserWindow({
    width: 1000,
    height: 700,
    minWidth: 720,
    minHeight: 520,
    title: "待办助手",
    autoHideMenuBar: true,
  });
  win.loadURL(`http://127.0.0.1:${port}`);
}

function killBackend() {
  // Windows: 强杀进程树，避免 uvicorn 子进程残留（ADR-0001 风险缓解）
  if (backendProc && backendProc.pid) {
    spawn("taskkill", ["/PID", String(backendProc.pid), "/T", "/F"], { windowsHide: true });
  }
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  killBackend();
  app.quit();
});

app.on("before-quit", killBackend);
