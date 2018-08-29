from tkinter import *
from PIL import ImageTk, Image
from urllib.request import urlopen
from io import BytesIO
from socketIO_client import SocketIO
from time import time
from interval import *
import player

SERVER, PORT = 'blacker.caltech.edu', 27036

root=Tk()
root.title("Nearer")
root.geometry("800x480") #x600") # for testing
#root.attributes('-fullscreen', True)
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
    old_width = img.width
    old_height = img.height
    wh_ratio = old_width / old_height

    assert (max_height or max_width)
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
def all_children(wid) :
    _list = wid.winfo_children()

    for item in _list :
        if item.winfo_children() :
            _list.extend(item.winfo_children())

    return _list

thumbnail_img = load_tk_image("http://via.placeholder.com/200x150?text=?", max_width=300)

thumbnail = Label(main_box, image = thumbnail_img, anchor="e")
thumbnail.grid(row=0, rowspan=5, column=2, sticky=E)

Label(main_box, text="Title:", font="Helvetica 24 bold").grid(row=0, column=0, sticky=E)
Label(main_box, text="Progress:", font="Helvetica 24 bold").grid(row=1, column=0, sticky=E)
Label(main_box, text="Status:", font="Helvetica 24 bold").grid(row=2, column=0, sticky=E)
Label(main_box, text="Connection:", font="Helvetica 24 bold").grid(row=3, column=0, sticky=E)
#Label(main_box, text="Ping:", font="Helvetica 24 bold").grid(row=4, column=0, sticky=E)
Label(main_box).grid(row=5, pady=15)
Label(main_box, text="Controls:", font="Helvetica 24 bold").grid(row=6, column=0, sticky=E, pady=20)
Label(main_box, text="Volume:", font="Helvetica 24 bold").grid(row=7, column=0, sticky=E, pady=20)

def server_action(action):
    urlopen("http://{}:{}/{}".format(SERVER, PORT, action))

title_display = Label(main_box, text="No Song Playing", font="Helvetica 24", width=20, anchor="w")
progress_display = Label(main_box, text="N/A of N/A", font="Helvetica 24")
status_display = Label(main_box, text="Unknown", font="Helvetica 24")
connection_frame = Frame(main_box)
connection_status = Label(connection_frame, text="☒", font="Helvetica 48", foreground="#aa0000")
reconnect_button = Button(connection_frame, text="↻ Reconnect", font="Helvetica 18") # TODO: reconnect button action
ping_display = Label(main_box, text="Ping: ?", font="Helvetica 18")
controls_frame = Frame(main_box)
resume_button = Button(controls_frame, text="Resume", command=lambda: server_action('resume'), font="Helvetica 28", width=11)
skip_button = Button(controls_frame, text="Skip", command=lambda: server_action('skip'), font="Helvetica 28", width=11)
pause_button = Button(controls_frame, text="Pause", command=lambda: server_action('pause'), font="Helvetica 28", width=11)
volume_slider = Scale(main_box, from_=0, to=100, orient=HORIZONTAL)

title_display.grid(row=0, column=1, sticky=W)
progress_display.grid(row=1, column=1, sticky=W)
status_display.grid(row=2, column=1, sticky=W)

connection_frame.grid(row=3, column=1, sticky=W)
connection_status.grid(row=0, column=0)
reconnect_button.grid(row=0, column=1, padx=10)

ping_display.grid(row=4, column=1, sticky=W)

controls_frame.grid(row=6, column=1, columnspan=2, sticky=W)
resume_button.grid(row=0, column=0, padx=2)
skip_button.grid(row=0, column=1, padx=2)
pause_button.grid(row=0, column=2, padx=2)

volume_slider.grid(row=7, column=1, columnspan=2, sticky=E+W)

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
    return callback
def on_disconnect():
    global connected
    connected = False
    connection_status.config(text="☒", foreground="#aa0000")
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
    pingSent = time()
    socket.emit('cl_ping')
@indicates_connection
def pong(*args):
    global pingTimes
    latency = time() - pingSent;
    pingTimes.append(latency);
    pingTimes = pingTimes[-30:]
    avg = sum(pingTimes)/len(pingTimes)

    ping_display.config(text="Ping: {}".format( round(avg,1) ))
set_interval(ping, 10)

@indicates_connection
def on_status(status):
    status_display.config(text=status.get("status", "Unknown"))

@indicates_connection
def on_play(req):
    print("Play requested for {} at {}".format( req["video"], req["start"] ))
    player.play(req["video"], req["start"])

@indicates_connection
def on_pause(*args):
    print("Paused at {}".format(player.get_time()))
    socket.emit('paused', player.get_time())
    player.stop()

@indicates_connection
def on_skip(*args):
    print("Received skip request")
    player.stop()
    socket.emit("done")


threads_running = True

# separate thread to notice if a player is done immediately
def player_update_loop():
    while threads_running:
        if player.stop_if_done():
            socket.emit("done")

@wait_for_connect
def gui_update_loop():
    last_id = None
    global thumbnail_img

    while threads_running:
        socket.wait(seconds=1) # should allow time to update frequently enough
        current_vid_data = player.current_vid_data

        if current_vid_data:
            if current_vid_data[0] != last_id:
                title_display.config(text=current_vid_data[1])

                thumbnail_img = load_tk_image(current_vid_data[3], max_width=300)
                thumbnail.config(image=thumbnail_img)

            current_progress = player.get_timestamp(player.get_time())
            duration = current_vid_data[2]
            progress_display.config(text="{} of {}".format(current_progress, duration))
        else:
            title_display.config(text="No Song Playing")

            thumbnail_img = load_tk_image("http://via.placeholder.com/200x150?text=?", max_width=300)
            thumbnail.config(image=thumbnail_img)

            progress_display.config(text="N/A of N/A")

thread1 = threading.Thread(target=gui_update_loop)
thread2 = threading.Thread(target=player_update_loop)
thread1.start()
thread2.start()

socket = SocketIO(SERVER, PORT)
socket.on('disconnect', on_disconnect)
socket.on('status', on_status)
socket.on('sv_pong', pong)
socket.on('play', on_play)
socket.on('pause', on_pause)
socket.on('skip', on_skip)

root.mainloop()

threads_running = False
player.stop()
