"""
Usage:
    broadcaster = Broadcaster()

    # add a listener to the event
    broadcaster.on_change += my_func

    # remove listener from the event
    broadcaster.on_change -= my_func

    # fire event
    broadcaster.on_change.fire()
"""


class Broadcaster:
    def __init__(self):
        self.on_change = EventHook()


class EventHook(object):

    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __sub__(self, handler):
        self.__handlers.remove(handler)

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def fire(self, *args, **kwargs):
        results = []

        if 'handler_key' in kwargs:
            handler_idx = kwargs.pop('handler_key')
            if handler_idx < 0 or handler_idx > len(self.__handlers) - 1:
                return

            handler = self.__handlers[handler_idx]
            results.append(handler(*args, **kwargs))
        else:
            for handler in self.__handlers:
                results.append(handler(*args, **kwargs))

        return results

    def clear_object_handlers(self, in_object):
        for handler in self.__handlers:
            if handler.im_self == in_object:
                # noinspection PyMethodFirstArgAssignment
                self -= handler
