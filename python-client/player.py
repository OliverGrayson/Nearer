import pafy
from omxplayer.player import OMXPlayer, OMXPlayerDeadError
from interval import *
import requests
import time
import math

STATUS_URL = "http://blacker.caltech.edu:27036/status"

player = None
player_start_time = None
player_stop_time = 0
current_vid_data = None

current_volume = 0.5
def linear_to_mbels(val):
    return 2000 * math.log(val, 10)
def set_volume(vol):
    global current_volume
    if vol == current_volume:
        return

    current_volume = vol

    if player:
        if vol == 0:
            player.mute()
        else:
            player.unmute()
            player.set_volume(vol)


vid_data_cache = {}
def get_vid_data(id):
    if id not in vid_data_cache:
        try:
            video = pafy.new("https://youtube.com/watch?v=" + id)
            vid_data_cache[id] = (video.getbestaudio().url, video.title, video.duration, video.bigthumb, id)
        except OSError:
            vid_data_cache[id] = None # indicates that video is UNAVAILABLE (premium only, copyright blocked, etc)
    return vid_data_cache[id]

# reduce between-song latency by loading the player URL ahead of time
def prep_queue():
    f = requests.get(STATUS_URL)
    data = f.json()
    to_download = { item["vid"] for item in data["queue"] }
    if data.get("current") is not None:
        to_download.add(data["current"]["vid"])
    for id in to_download:
        get_vid_data(id) # ensure we have a player url for everybody in the queue
queue_loader = SetInterval(prep_queue, 10)

def get_timestamp(seconds):
    hours = seconds // 3600
    seconds -= 3600 * hours
    minutes = seconds // 60
    seconds -= 60 * minutes
    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)

def play(id, start_time=0):
    global current_vid_data
    current_vid_data = get_vid_data(id)
    if current_vid_data is None:
        player = True
        return

    play_url = current_vid_data[0]

    args = ["-o", "local"]
    if start_time != 0:
        args += ["--pos", get_timestamp(start_time)]
    if current_volume != 1 and current_volume != 0:
        args += ["--vol", str(linear_to_mbels(current_volume))]

    global player
    global player_start_time
    if player is None:
        player = OMXPlayer(play_url, args=args)
        player_start_time = time.time() - start_time

        if current_volume == 0:
            player.mute()

        print("Started OMXPlayer for {} at {}".format(id, start_time))

def stop():
    global player
    global player_stop_time
    global current_vid_data

    if player is not None:
        try:
            player_stop_time = get_time()
        except OMXPlayerDeadError:
            player_stop_time = 0

        tmp = player
        player = None
        current_vid_data = None
        tmp.quit() # mark player as dead before we block on quitting it

def stop_if_done():
    global player
    if player is None:
        return False
    elif player is True:
        player = False
        return True # we're skipping a bad song
    elif player._process is None or player._process.poll() is not None:
        # TODO: this seems to be the how OMXPlayer internally detects whether a
        # player is done, but a try-catech may work better
        stop()
        return True
    return False

def get_time():
    if player is None:
        return player_stop_time
    else:
        return time.time() - player_start_time
        # TODO: using player.position() seems cleaner but resulted in resumes
        # ~10 seconds off from the pauses
