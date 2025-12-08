const { app, BrowserWindow } = require("electron");
const path = require("path");

function createWindow() {
  const win = new BrowserWindow({
    width: 420,
    height: 820,
    backgroundColor: "#f8f9fb",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  const devUrl = process.env.VITE_DEV_SERVER;
  if (devUrl) {
    win.loadURL(devUrl);
  } else {
    const distPath = path.join(__dirname, "../frontend/dist/index.html");
    win.loadFile(distPath);
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

