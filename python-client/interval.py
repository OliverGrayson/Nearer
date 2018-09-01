import time, threading

# source: https://stackoverflow.com/questions/2697039/python-equivalent-of-setinterval/48709380#48709380
StartTime=time.time()
class SetInterval:
    def __init__(self,action,interval) :
        self.interval=interval
        self.action=action
        self.stopEvent=threading.Event()
        self.restart()

    def __setInterval(self) :
        nextTime=time.time()+self.interval
        while not self.stopEvent.wait(nextTime-time.time()) :
            nextTime+=self.interval
            self.action()

    def cancel(self) :
        self.stopEvent.set()

    def restart(self):
        thread=threading.Thread(target=self.__setInterval)
        thread.start()
