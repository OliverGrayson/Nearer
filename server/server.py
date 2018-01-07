from queue import Queue
from flask import Flask, request, abort
from flask_socketio import SocketIO, emit
from threading import Thread, Lock
import json

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

def playNext():
    global thread
    global playing
    global playtime
    if running and not queue.empty():
        playing = queue.get(True)
        playtime = 0

        emitPlay()

        return True
    else:
        return False

def emitPlay(data=None):
    if data == None:
        global playing
        global playtime
        data = dict({ 'video': str(playing), 'start': playtime })
    print('Emitting play request:', data)
    socketio.emit('play', data)

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

@app.route('/resume')
def resumeQueue():
    global running
    running = True
    emitPlay()
    return json.dumps({ "message": "Success!", "queue": list(queue.queue)})

@app.route('/skip')
def skip():
    socketio.emit('skip')
    return json.dumps({ "message": "Success!", "queue": list(queue.queue)})

@socketio.on('done')
def done():
    playNext()

@socketio.on('connect_event')
def connection(msg):
    print('Client response:', msg)

@socketio.on('connect')
def connect():
    print('Client connected.')
    emit('server_connect')

if __name__ == '__main__':
    socketio.run(app, debug=True)
