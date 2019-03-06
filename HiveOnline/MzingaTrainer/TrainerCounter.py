import multiprocessing


class TrainerCounter(object):
    def __init__(self, init_completed=0, init_remaining=0):
        self.completed = multiprocessing.Value('i', init_completed)
        self.remaining = multiprocessing.Value('i', init_remaining)
        self.lock = multiprocessing.Lock()

    def update(self):
        with self.lock:
            self.completed.value += 1
            self.remaining.value -= 1

    @property
    def values(self):
        return self.completed.value, self.remaining.value
