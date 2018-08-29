import threading

# source: https://stackoverflow.com/questions/2697039/python-equivalent-of-setinterval
def set_interval(func, sec, args=(), wait=True, daemon=True):
    if not wait:
        func(*args)
    def func_wrapper():
        set_interval(func, sec)
        func(*args)
    t = threading.Timer(sec, func_wrapper)
    t.setDaemon(daemon)
    t.start()
    return t
