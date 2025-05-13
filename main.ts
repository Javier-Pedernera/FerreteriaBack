import { app, BrowserWindow } from 'electron';
import * as path from 'path';
import { spawn } from 'child_process';

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
    },
  });

  // Durante el desarrollo, cargar Vite (puerto 3000)
  mainWindow.loadURL('http://localhost:3000');  // Asegúrate de que Vite esté corriendo en este puerto

  if (mainWindow !== null) {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(() => {
  // Levantar Flask en segundo plano
  const python = path.join(__dirname, 'backend', 'venv', 'Scripts', 'python.exe'); // Cambia esto si usas otro sistema operativo
  const flaskApp = path.join(__dirname, 'backend', 'run.py'); // Ruta a tu archivo run.py del backend
  const process = spawn(python, [flaskApp]);

  process.on('error', (err) => {
    console.error('Error al iniciar Flask:', err);
  });

  process.on('exit', (code) => {
    console.log(`Flask detenido con el código ${code}`);
  });

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
