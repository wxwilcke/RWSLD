#!/usr/bin/python3

from itertools import cycle
from threading import Thread
from time import sleep
from sys import stdout

class ProgressIndicator:
    def __init__(self, end="\r", update_rate=0.2):
        self.run = False
        self.end = end
        self.update_rate = update_rate

    def _animate(self):
        for c in cycle(['|', '/', '-', '\\']):
            if not self.run:
                break
            stdout.write('\r' + c)
            stdout.flush()
            sleep(self.update_rate)

    def start(self):
        self.run = True

        thread = Thread(target=self._animate)
        thread.start()

    def stop(self):
        self.run = False

        stdout.write(self.end)
        stdout.flush
