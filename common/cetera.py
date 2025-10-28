import signal

def signal_stop(func):
    def stop(signum, frame):
        func()
    signal.signal(signal.SIGINT, stop)

