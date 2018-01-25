const electron = require('electron');
// Module to control application life.
const { app, BrowserWindow, ipcMain } = electron;

const path = require('path');
const url = require('url');

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 800,
    height: 215,
    resizable: false,
  });

  mainWindow.setMenu(null);

  // and load the index.html of the app.
  mainWindow.loadURL(url.format({
    pathname: path.join(__dirname, 'index.html'),
    protocol: 'file:',
    slashes: true,
  }));

  // Open the DevTools.
  // mainWindow.webContents.openDevTools();

  // Emitted when the window is closed.
  mainWindow.on('closed', () => {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    mainWindow = null;
  });
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow);

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  // On OS X it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createWindow();
  }
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.

const player = require('./player'); // Video player.
const io = require('socket.io-client'); // SocketIO client.

let play;
let socket;
let pingSent;
let pingTimes = [];

function playVideo(vid, time) {
  let interval;
  play = player.play(vid, time);

  if (play) {
    play.on('info', () => {
      const info = player.getInfo();
      console.log(info);
      mainWindow.webContents.send('vid-info', info);
    });

    play.on('play', () => {
      socket.emit('playing');
      interval = setInterval(() => {
        mainWindow.webContents.send('vid-update', {
          time_millis: player.getTime(),
        });
      }, 1000);
    });

    play.on('close', () => {
      mainWindow.webContents.send('vid-done');
      socket.emit('done');
      clearInterval(interval);
    });
  }
}

// Make WebSockets connection to server.
socket = io('http://localhost:5000', {
  reconnection: true,
  reconnectionDelay: 500,
  reconnectionAttempts: 10,
});

setInterval(() => {
  pingSent = Date.now();
  socket.emit('cl_ping');
}, 1000);

socket.on('sv_pong', () => {
  const latency = Date.now() - pingSent;
  pingTimes.push(latency);
  pingTimes = pingTimes.slice(-30); // keep last 30 samples
  const avg = pingTimes.reduce((a, b) => a + b, 0.0) / pingTimes.length;
  mainWindow.webContents.send('ping', Math.round(avg * 10) / 10);
});

socket.on('connect', () => {
  console.log('Connected to server.');
  mainWindow.webContents.send('connected');
  socket.emit('connect_event', { data: 'Successful connection to server.' });
});

socket.on('disconnect', () => {
  mainWindow.webContents.send('disconnected');
});

socket.on('status', (status) => {
  mainWindow.webContents.send('status', status);
});

socket.on('play', (req) => {
  console.log(`Play request: ${req}`);
  playVideo(`https://youtube.com/watch?v=${req.video}`, req.start);
});

socket.on('skip', () => {
  if (play) {
    player.stop();
  }
});

socket.on('pause', () => {
  socket.emit('paused', player.getTime());
  if (play) {
    player.stop();
  }
});

ipcMain.on('reconnect', () => {
  socket.connect();
});
