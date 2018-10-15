from queue import Queue
from threading import Thread
from typing import Callable, Awaitable

poison = object()


class TaskQueue(object):

    def __init__(self, limit):
        def process_items():
            while True:
                callback = self._queue.get()
                if callback is poison:
                    break
                try:
                    result = callback
                    self.results.put(result)
                except:
                    pass
                finally:
                    self._queue.task_done()
        self._workers = [Thread(target=process_items) for _ in range(limit)]
        self._queue = Queue()
        self.results = Queue()

    def processing(self):
        return self._queue.empty()

    def enqueue(self, callback):
        self._queue.put(callback)

    def start(self):
        for worker in self._workers:
            worker.start()

    def stop(self):
        for i in range(len(self._workers)):
            self._queue.put(poison)
        while self._workers:
            self._workers.pop().join()
