const { app, BrowserWindow } = require("electron");
const path = require("path");

function createWindow() {
  const win = new BrowserWindow({
    width: 1123,
    height: 781,
    backgroundColor: "#f8f9fb",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
    show: false, // 先不显示，等加载完成后再显示
  });

  const devUrl = process.env.VITE_DEV_SERVER;
  if (devUrl) {
    // 确保 URL 格式正确
    const url = devUrl.startsWith("http") ? devUrl : `http://${devUrl}`;
    console.log("Loading dev server:", url);
    win.loadURL(url).catch((err) => {
      console.error("Failed to load URL:", err);
      win.webContents.once("did-fail-load", () => {
        console.error("页面加载失败，请确保前端开发服务器正在运行 (npm run dev in frontend/)");
      });
    });
  } else {
    const distPath = path.join(__dirname, "../frontend/dist/index.html");
    console.log("Loading production build:", distPath);
    win.loadFile(distPath).catch((err) => {
      console.error("Failed to load file:", err);
    });
  }

  // 移除默认菜单栏（File、Edit、View 等）
  win.setMenuBarVisibility(false);
  win.setMenu(null);

  // 页面加载完成后显示窗口
  win.once("ready-to-show", () => {
    win.show();
    console.log("Window is ready and shown");
  });

  // 监听页面加载错误
  win.webContents.on("did-fail-load", (event, errorCode, errorDescription) => {
    if (errorCode !== -3) { // -3 是正常导航，忽略
      console.error(`页面加载失败 (${errorCode}): ${errorDescription}`);
    }
  });

  // 打开开发者工具以便调试（可通过环境变量控制）
  if (devUrl && process.env.OPEN_DEVTOOLS !== "false") {
    win.webContents.openDevTools();
  }
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

