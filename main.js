const electron = require('electron');
// Module to control application life.
const { app, BrowserWindow, ipcMain } = electron;

const path = require('path');
const url = require('url');

/* Necessary intialization code for disposal. */
const player = require('./player'); // Video player.
const io = require('socket.io-client'); // SocketIO client.

// Make WebSockets connection to server.
const socket = io('http://localhost:5000', {
  reconnection: true,
  reconnectionDelay: 500,
  reconnectionAttempts: 10,
});

let pingSent;
const pingInterval = setInterval(() => {
  pingSent = Date.now();
  socket.emit('cl_ping');
}, 1000);

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;
let closed = false;

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
    // Stop pinging boi.
    clearInterval(pingInterval);

    // Stop the player and close the socket.
    closed = true;
    player.stop();
    socket.disconnect();


    // Dereference window object.
    mainWindow = null;

    // Quit the app.
    app.quit();
  });
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow);

// Nearer code.

let play;
let pingTimes = [];

function playVideo(vid, time) {
  let interval;
  play = player.play(vid, time);

  if (play) {
    play.on('info', () => {
      const info = player.getInfo();
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
      // This can be send after the window is closed.
      if (!closed) {
        mainWindow.webContents.send('vid-done');
      }
      socket.emit('done');
      clearInterval(interval);
    });
  }
}

socket.on('sv_pong', () => {
  const latency = Date.now() - pingSent;
  pingTimes.push(latency);
  pingTimes = pingTimes.slice(-30); // keep last 30 samples
  const avg = pingTimes.reduce((a, b) => a + b, 0.0) / pingTimes.length;
  // This can get called after the window is closed.
  if (!closed) {
    mainWindow.webContents.send('ping', Math.round(avg * 10) / 10);
  }
});

socket.on('connect', () => {
  mainWindow.webContents.send('connected');
  socket.emit('connect_event', { data: 'Successful connection to server.' });
});

socket.on('disconnect', () => {
  // This can get called after the window is closed.
  if (!closed) {
    mainWindow.webContents.send('disconnected');
  }
});

socket.on('status', (status) => {
  mainWindow.webContents.send('status', status);
});

socket.on('play', (req) => {
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
