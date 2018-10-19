import asyncio


class TaskQueue(object):

    def __init__(self):
        self.tasks = []
        self.loop = asyncio.get_event_loop()

    def enqueue(self, callback, *args, **kwargs):
        self.tasks.append(asyncio.ensure_future(callback(*args, **kwargs)))

    def run(self):
        try:
            done, _ = self.loop.run_until_complete(asyncio.gather(self.tasks, return_exceptions=True))
            results = [fut.result() for fut in done]
            return results
        except Exception as ex:
            return ["Async Error:" + str(ex)]

    def stop(self):
        self.loop.stop()
