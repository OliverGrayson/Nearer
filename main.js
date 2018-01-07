const electron = require('electron');
// Module to control application life.
const { app, BrowserWindow } = electron;

const path = require('path');
const url = require('url');

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
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
  mainWindow.webContents.openDevTools();

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

// Make WebSockets connection to server.
const socket = io('http://localhost:5000');

function playVideo(vid, time) {
  play = player.play(vid, time);

  play.on('info', () => {
    const info = player.getInfo();
    console.log(info);
    mainWindow.webContents.send('vid-info', info);
  });

  play.on('play', () => {
    socket.emit('playing');
  });

  play.on('close', () => {
    socket.emit('done');
  });
}

socket.on('connect', () => {
  console.log('Connected to server.');
  socket.emit('connect_event', { data: 'Successful connection to server.' });
});

socket.on('server_connect', () => {
  console.log('Server connection successful.');
});

socket.on('play', (req) => {
  console.log('Play request:', req);
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
