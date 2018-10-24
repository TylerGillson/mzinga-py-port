import asyncio


class TaskQueue(object):

    def __init__(self):
        self.tasks = []
        self.loop = asyncio.get_event_loop()

    def enqueue(self, callback, *args, **kwargs):
        self.tasks.append(asyncio.ensure_future(callback(*args, **kwargs)))

    def run(self, loop=None):
        if loop:
            asyncio.set_event_loop(loop)
        try:
            done, _ = self.loop.run_until_complete(asyncio.wait(self.tasks))
            results = [fut.result() for fut in done]
            return results
        except Exception as ex:
            return ["Async Error:" + str(ex)]

    def stop(self):
        for task in self.tasks:
            task.cancel()
        self.loop.stop()
