import time

class Event:
    def __init__(self):
        self._create_time = time.time()

    def handle(self, system):
        pass