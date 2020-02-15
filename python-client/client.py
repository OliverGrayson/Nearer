from tkinter import *
from PIL import ImageTk, Image
from urllib.request import urlopen
from io import BytesIO
from socketIO_client import SocketIO
import time
from interval import *
import player
import logging
import config

logging.basicConfig(filename=config.home_dir + "/nearer.log", filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logging.info("Nearer client started")


SERVER, PORT = 'blacker.caltech.edu', 27036

def server_action(action):
    urlopen("http://{}:{}/{}".format(SERVER, PORT, action))

server_action('pause') # client doesn't start playing, it misses the first "play" emission for some reason

root=Tk()
root.title("Nearer")
root.geometry("800x480")
root.resizable(0, 0)

# make sure nothing gets too close (within 15px) to the edge
main_box = Frame(root)
main_box.grid(row=0, column=0, padx=15, pady=15)

def load_tk_image(path, max_width=None, max_height=None):
    if path.find("://") != -1:
        image_byt = urlopen(path).read()
        img = Image.open(BytesIO(image_byt))
    else:
        img = Image.open(path)

    if (max_height or max_width): # resizing requested
        old_width = img.width
        old_height = img.height
        wh_ratio = old_width / old_height

        if max_width and max_height:
            desired_wh_ratio = max_width / max_height
            if desired_wh_ratio >= wh_ratio:
                max_height = None # picture is WIDE (so use max_width)
            else:
                max_width = None # picture is TALL (so use max_height)
        if max_width:
            width = max_width
            height = width / wh_ratio
        else:
            height = max_height
            width = height * wh_ratio
        height = int(old_height * max_width / old_width)
        img = img.resize((width, height))

    img = ImageTk.PhotoImage(img)
    return img

LABEL_FONT = "Helvetica 18 bold"
INFO_FONT = "Helvetica 18"
MINOR_INFO_FONT = "Helvetica 12"
BUTTON_FONT = "Helvetica 22"
MINOR_BUTTON_FONT = "Helvetica 12"
CONNECTION_STATUS_FONT = "Helvetica 36"

CONTROL_BUTTON_WIDTH = 10
CONTROL_BUTTON_PADDING = 2
THUMB_WIDTH_PX = 300

DEFAULT_VOLUME = 40
player.Player.set_volume(DEFAULT_VOLUME/100)

Label(main_box, text="Title:", font=LABEL_FONT).grid(row=0, column=0, sticky=E)
Label(main_box, text="Progress:", font=LABEL_FONT).grid(row=1, column=0, sticky=E)
Label(main_box, text="Status:", font=LABEL_FONT).grid(row=2, column=0, sticky=E)
Label(main_box, text="Connection:", font=LABEL_FONT).grid(row=3, column=0, sticky=E)
Label(main_box).grid(row=5, pady=15)
Label(main_box, text="Controls:", font=LABEL_FONT).grid(row=6, column=0, sticky=E, pady=20)
Label(main_box, text="Volume:", font=LABEL_FONT).grid(row=7, column=0, sticky=E, pady=20)

title_display = Label(main_box, text="No Song Playing", font=INFO_FONT, width=23, anchor="w")
progress_display = Label(main_box, text="N/A", font=INFO_FONT)
status_display = Label(main_box, text="Unknown", font=INFO_FONT)
connection_frame = Frame(main_box)
connection_status = Label(connection_frame, text="☒", font=CONNECTION_STATUS_FONT, foreground="#aa0000")
reconnect_button = Button(connection_frame, text="↻ Reconnect", font=MINOR_BUTTON_FONT)
ping_display = Label(main_box, text="Ping: ?", font=MINOR_INFO_FONT)
controls_frame = Frame(main_box)
resume_button = Button(controls_frame, text="Resume", command=lambda: server_action('resume'), font=BUTTON_FONT, width=CONTROL_BUTTON_WIDTH)
skip_button = Button(controls_frame, text="Skip", command=lambda: server_action('skip'), font=BUTTON_FONT, width=CONTROL_BUTTON_WIDTH)
pause_button = Button(controls_frame, text="Pause", command=lambda: server_action('pause'), font=BUTTON_FONT, width=CONTROL_BUTTON_WIDTH)
volume_slider = Scale(main_box, from_=0, to=100, orient=HORIZONTAL)
volume_slider.set(DEFAULT_VOLUME)
thumbnail_img = load_tk_image("http://via.placeholder.com/{}x{}?text=?".format(THUMB_WIDTH_PX, int(THUMB_WIDTH_PX*9/16)))
thumbnail = Label(main_box, image = thumbnail_img, anchor="e")

title_display.grid(row=0, column=1, sticky=W)
progress_display.grid(row=1, column=1, sticky=W)
status_display.grid(row=2, column=1, sticky=W)

connection_frame.grid(row=3, column=1, sticky=W)
connection_status.grid(row=0, column=0)
reconnect_button.grid(row=0, column=1, padx=10)

ping_display.grid(row=4, column=1, sticky=W)

thumbnail.grid(row=0, rowspan=5, column=2, sticky=E)

controls_frame.grid(row=6, column=1, columnspan=2, sticky=W)
resume_button.grid(row=0, column=0, padx=CONTROL_BUTTON_PADDING)
skip_button.grid(row=0, column=1, padx=CONTROL_BUTTON_PADDING)
pause_button.grid(row=0, column=2, padx=CONTROL_BUTTON_PADDING)

volume_slider.grid(row=7, column=1, columnspan=2, sticky=E+W)

# https://stackoverflow.com/questions/7290071/getting-every-child-widget-of-a-tkinter-window
def all_children(wid) :
    _list = wid.winfo_children()

    for item in _list :
        if item.winfo_children() :
            _list.extend(item.winfo_children())

    return _list
root.configure(background="#eeeeee")
for widget in all_children(root):
    if isinstance(widget, Button):
        widget.configure(padx=10, pady=10, background="#aaaaff", activebackground="#ccccff")
    else:
        widget.configure(background="#eeeeee")
# TODO set uniform background more cleanly


# The socket.on('connect') and .on('reconnect') handlers didn't work
# so this wraps all server-signal-handling methods in code to make sure
# we know that we're connected
connected = False
def indicates_connection(f):
    def _decorator(*args, **kwargs):
        global connected
        if not connected:
            connection_status.config(text="☑", foreground="#00aa00")
            connected = True
        return f(*args, **kwargs)
    return _decorator
def on_disconnect():
    global connected
    connected = False
    if not closed: # do not try to change data on closed window
        connection_status.config(text="☒", foreground="#aa0000")
    logging.info("disconnected")
def wait_for_connect(f):
    def _decorator(*args, **kwargs):
        while not connected:
            continue
        return f(*args, **kwargs)
    return _decorator

pingTimes = []
pingSent = 0
def ping():
    global pingSent
    pingSent = time.time()
    socket.emit('cl_ping')
@indicates_connection
def pong(*args):
    global pingTimes
    latency = time.time() - pingSent;
    pingTimes.append(latency);
    pingTimes = pingTimes[-30:]
    avg = sum(pingTimes)/len(pingTimes)

    ping_display.config(text="Ping: {}".format( round(avg,1) ))

@indicates_connection
def on_status(status):
    status = status.get("status", "Unknown")
    if status == "Playing": # might not actually be "playing" yet
        if player.Player.status == player.PlayerStatus.LOADING_DATA:
            status = "Loading song data..."
        elif player.Player.status == player.PlayerStatus.DOWNLOADING:
            status = "Downloading next song..."

    status_display.config(text=status)


def emit_done():
    logging.info("emitting 'done'")
    print("emitting 'done'")
    socket.emit("done")

@indicates_connection
def on_play(req):
    logging.info("Play requested for {} at {}".format( req["video"], req["start"] ))
    if player.Player.isPaused():
        player.Player.current_player.play()
    else:
        player.Player(req["video"], start_time=req["start"], done_callback=emit_done)

@indicates_connection
def on_pause(*args):
    if player.Player.status == player.PlayerStatus.PLAYING:
        t = player.Player.current_player.get_time()
    else:
        t = 0
    logging.info("Paused at {}".format(t))
    socket.emit('paused', t)
    #player.Player.stop_current()
    player.Player.pause_current()

@indicates_connection
def on_skip(*args):
    logging.info("Received skip request")
    player.Player.stop_current()

closed = False
close_event = threading.Event()
reconnect_requested = False

def connect(wait_for_connection):
    global socket

    socket = SocketIO(SERVER, PORT, wait_for_connection=wait_for_connection)
    socket.on('play', on_play)
    socket.on('pause', on_pause)
    socket.on('skip', on_skip)
    socket.on('status', on_status)
    socket.on('sv_pong', pong)
    socket.on('disconnect', on_disconnect)

def socket_update_loop():
    global reconnect_requested

    connect(True)
    pinger = SetInterval(ping, 10, wait=False)

    while not close_event.is_set():
        # perform all socket-related actions
        socket.wait(seconds=1)

        # reconnect if necessary
        if reconnect_requested:
            reconnect_requested = False

            on_disconnect()
            pinger.cancel()
            player.Player.stop_current()
            socket.disconnect()

            time.sleep(3)

            connect(True) # TODO socket.connect() causes an error in server.py
            pinger.restart(wait=False)

    pinger.cancel()

def update_volume(vol):
    player.Player.set_volume(int(vol) / 100)
def reconnect():
    global reconnect_requested
    reconnect_requested = True

volume_slider.config(command=update_volume)
reconnect_button.config(command=reconnect)

def gui_update_loop():
    last_id = None
    global thumbnail_img

    while not close_event.is_set():
        # GUI updates
        if player.Player.current_player:
            current_vid_data = player.Player.current_player.vid_data
            if current_vid_data.id != last_id:
                last_id = current_vid_data.id
                title_display.config(text=current_vid_data.title)

                thumbnail_img = load_tk_image(current_vid_data.thumbnail, max_width=THUMB_WIDTH_PX)
                thumbnail.config(image=thumbnail_img)

            status_display.config(text="Playing")
            current_progress = player.get_timestamp(int(player.Player.current_player.get_time()))
            duration = current_vid_data.duration
            progress_display.config(text="{} of {}".format(current_progress, duration))

        time.sleep(1)

socket_updater_thread = threading.Thread(target=socket_update_loop)
gui_updater_thread = threading.Thread(target=gui_update_loop)
socket_updater_thread.start()
gui_updater_thread.start()
logging.info("all threads initialized")

root.mainloop() # runs until window is closed

closed = True
close_event.set()
player.Player.stop_current()
socket.disconnect()
