from queue import Queue
from flask import Flask, request, abort
from flask_socketio import SocketIO, emit
from threading import Lock
import json
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=None)

# Play Queue State Variables
queue = Queue()
playing = None
running = True
client_playing = False
playtime = 0

thread = None
thread_lock = Lock()

local = re.compile('192.168.[0-9].[0-9]{3}')
caltech = re.compile('131.215.[0-9]{1,3}.[0-9]{1,3}')

@app.before_request
def limit_remote_addr():
    if caltech.fullmatch(request.remote_addr) == None and \
       local.fullmatch(request.remote_addr) == None and \
       request.remote_addr != '127.0.0.1':
        abort(403)  # Forbidden

def playNext():
    global thread
    global playing
    global playtime

    if running and not queue.empty():
        playing = queue.get(True)
        print(playing)
        playtime = 0

        socketio.emit('status', getStatus())
        emitPlay()
        
        return True
    else:
        socketio.emit('status', getStatus())
        return False

def emitPlay(data=None):
    if data == None:
        global playing
        global playtime
        data = dict({ 'video': str(playing), 'start': playtime })
    if data != None:
        print('Emitting play request:', data)
        socketio.emit('play', data)

def getStatus():
    status = ''
    if running and playing:
        status = 'Playing'
    elif running:
        status = 'Queue Empty'
    else:
        status = 'Paused'

    return dict({
        'queue': list(queue.queue),
        'current': playing,
        'status': status
    })

@app.route('/add')
def addToQueue():
    vid = request.args.get('vid', '')
    if vid == '':
        abort(400)
    else:
        queue.put(vid, True)
        if queue.qsize() == 1 and playing == None:
            playNext()
        return json.dumps({ "message": "Success!", "queue": list(queue.queue)})

@app.route('/pause')
def pauseQueue():
    global running
    print('Pause requested.')
    running = False;

    socketio.emit('pause');

    return json.dumps({ "message": "Success!", "queue": list(queue.queue)})

@socketio.on('paused')
def paused(timestamp):
    global playtime
    try:
        playtime = int(timestamp)
    except ValueError:
        playtime = 0
        print('Invalid timestamp', timestamp)
    socketio.emit('status', getStatus())

@app.route('/resume')
def resumeQueue():
    global running
    print('Resume requested.')
    running = True

    emitPlay()
    socketio.emit('status', getStatus())

    return json.dumps({ "message": "Success!", "queue": list(queue.queue)})

@app.route('/skip')
def skip():
    print('Skip requested.')
    socketio.emit('skip')
    return json.dumps({ "message": "Success!", "queue": list(queue.queue)})

@socketio.on('done')
def done():
    print('Client done playing.')
    if running:
        global playing
        playing = None
    socketio.emit('status', getStatus())
    playNext()

@socketio.on('cl_ping')
def pong():
    emit('sv_pong')

@socketio.on('connect_event')
def connection(msg):
    print('Client response:', msg)

@socketio.on('connect')
def connect():
    print('Client connected.')

    emit('server_connect')
    emit('status', getStatus())

    if playing or not queue.empty():
        emitPlay()

if __name__ == '__main__':
    socketio.run(app, debug=True)
