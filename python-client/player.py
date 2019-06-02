import pafy
import youtube_dl
from omxplayer.player import OMXPlayer, OMXPlayerDeadError
from interval import *
import threading
import requests
import time
import datetime
import math
import logging
import enum

STATUS_URL = "http://blacker.caltech.edu:27036/status"
DOWNLOAD_DIR = "~/nearer_downloads/"

# helper functions for volume, time
def linear_to_mbels(val):
    return 2000 * math.log(val, 10)
def get_timestamp(seconds):
    hours = seconds // 3600
    seconds -= 3600 * hours
    minutes = seconds // 60
    seconds -= 60 * minutes
    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)

class PlayerStatus(enum.Enum):
    """
    Enum for possible player states. Note that pauses are not represented:
    the player is simply re-created at the proper time when resuming
    """
    STOPPED = 0
    LOADING_DATA = 1
    DOWNLOADING = 2
    PLAYING = 3
class Player:
    current_player = None # avoid overlapping songs
    status = PlayerStatus.STOPPED

    def __init__(self, id, start_time=0, done_callback=None):
        """
        make a Player (and start playing it)
        """
        Player.status = PlayerStatus.LOADING_DATA

        self.vid_data = VideoData(id)
        self.start_time = start_time
        self.done = done_callback

        if self.vid_data.unavailable:
            logging.info("{} seems to be unavailable".format(id))
            done_callback()
        elif self.vid_data.streamable:
            self.play()
        else:
            self.vid_data.set_download_callback(self.play) # TODO implement
            Player.status = PlayerStatus.DOWNLOADING

    def play(self):
        args = ["-o", "local"]
        if self.start_time != 0:
            args += ["--pos", get_timestamp(self.start_time)]
        # if current_volume != 1 and current_volume != 0:
        #     args += ["--vol", str(linear_to_mbels(current_volume))]
        args += ["--vol", str(linear_to_mbels(0.01))] # TODO testing during quiet hours

        if Player.current_player is not None:
            Player.current_player.stop()
        Player.current_player = self

        self.omx = OMXPlayer(self.vid_data.url, args=args)
        self.omx.exitEvent += lambda p, code: self.stop()

        if self.done:
            self.omx.exitEvent += lambda p, code: self.done()

        self.start_timestamp = time.time() - self.start_time

        if Player.current_volume == 0:
            self.omx.mute()

        logging.info("Started OMXPlayer for {} at {}".format(self.vid_data.id, self.start_time))
        Player.status = PlayerStatus.PLAYING

    def stop(self):
        Player.current_player = None
        if player.status == PlayerStatus.PLAYING:
            self.omx.quit() # mark player as dead before we block on quitting it
        else:
            pass # TODO stop in process of getting data, downloading, etc

    @classmethod
    def stop_current(self):
        if Player.current_player:
            Player.current_player.stop()

    def get_time():
        if Player.status == PlayerStatus.PLAYING:
            return time.time() - self.start_timestamp
        else:
            return 0
        # TODO: using player.position() seems cleaner but resulted in resumes
        # ~10 seconds off from the pauses

    current_volume = 0.5 # TODO should we allow this to depend on the player?
    @classmethod
    def set_volume(cls, vol):
        if vol == current_volume:
            return

        Player.current_volume = vol

        if Player.current_player and Player.current_player.status == PlayerStatus.PLAYING:
            if vol == 0:
                Player.current_player.omx.mute()
            else:
                Player.current_player.omx.unmute()
                Player.current_player.omx.set_volume(vol)

class VideoData:
    cache = {}
    data_loading_lock = threading.Lock()

    def load_data(self, id):
        VideoData.data_loading_lock.acquire()

        logging.info("refreshing video data for {}".format(id))
        self.id = id
        try:
            video = pafy.new(id)

            self.url = video.audiostreams[0].url # TODO actual fix here
            self.streamable = True
            self.title = video.title
            self.duration = video.duration
            self.thumbnail = video.bigthumb
            self.last_updated = datetime.datetime.now()
            self.unavailable = False

        except (OSError, ValueError) as _:
            self.unavailable = True
            # indicates that video is UNAVAILABLE (premium only, copyright blocked, etc)

        VideoData.cache[id] = self

        VideoData.data_loading_lock.release()

    @classmethod
    def cache_valid(cls, id):
        return \
            (id in VideoData.cache) and \
            (not VideoData.cache[id].unavailable) and \
            (datetime.datetime.now() - VideoData.cache[id].last_updated)

    # reduce between-song latency by loading the player URL ahead of time
    @classmethod
    def prep_queue(cls):
        f = requests.get(STATUS_URL)
        data = f.json()
        to_download = { item["vid"] for item in data["queue"] }

        for id in to_download:
            VideoData(id)

    def __init__(self, id):
        if VideoData.cache_valid(id):
            self.__dict__.update(VideoData.cache[id].__dict__)
            # copy from cached vid
        else:
            self.load_data(id)

queue_loader = SetInterval(VideoData.prep_queue, 30)
