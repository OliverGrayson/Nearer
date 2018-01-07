from flask import Flask, request
from flask_socketio import SocketIO, emit

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

@app.route('/', methods=['POST'])
def index():
    vid = request.form['vid']
    print(vid)
    socketio.emit('play', vid);
    return "{}"

@socketio.on('connect')
def connect():
    print('Client connected.')

if __name__ == '__main__':
    socketio.run(app, debug=True)
