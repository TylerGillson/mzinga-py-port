import asyncio


class TaskQueue(object):

    def __init__(self):
        self.tasks = []
        self.loop = asyncio.get_event_loop()

    def enqueue(self, callback, *args, **kwargs):
        self.tasks.append(
            asyncio.ensure_future(callback(*args, **kwargs))
        )

    def run(self):
        done, _ = self.loop.run_until_complete(asyncio.wait(self.tasks))
        results = [fut.result() for fut in done]
        return results

    async def stop(self, max_time):
        asyncio.sleep(max_time)
        self.loop.stop()
