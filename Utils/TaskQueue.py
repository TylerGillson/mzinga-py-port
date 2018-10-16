from queue import Queue
from threading import Thread

poison = object()


class TaskQueue(object):

    def __init__(self, limit):
        def process_items():
            while True:
                callback, args, kwargs = self._queue.get()

                if callback is poison:
                    break
                try:
                    result = callback(*args, **kwargs)
                    self.results.put(result)
                except Exception as ex:
                    print(ex)
                    pass
                finally:
                    self._queue.task_done()
        self._workers = [Thread(target=process_items) for _ in range(limit)]
        self._queue = Queue()
        self.results = Queue()

    def processing(self):
        return self._queue.empty()

    def enqueue(self, callback, *args, **kwargs):
        self._queue.put((callback, args, kwargs))

    def start(self):
        for w in self._workers:
            w.start()

    def stop(self):
        for i in range(len(self._workers)):
            self._queue.put((poison, poison, poison))
        while self._workers:
            self._workers.pop().join()
