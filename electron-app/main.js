const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  win.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// Exemplo de integração: rodar um script Python e retornar o resultado
ipcMain.handle('run-python', async (event, args) => {
  return new Promise((resolve, reject) => {
    const py = spawn('python', [path.join(__dirname, '../gaia_genesis/main.py'), ...args]);
    let data = '';
    py.stdout.on('data', (chunk) => { data += chunk; });
    py.stderr.on('data', (err) => { data += err; });
    py.on('close', (code) => { resolve(data); });
    py.on('error', (err) => { reject(err); });
  });
});
