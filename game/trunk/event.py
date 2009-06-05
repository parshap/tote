# From: http://www.valuedlessons.com/2008/04/events-in-python.html

class Event:
    def __init__(self):
        self.handlers = set()
        self._to_remove = []
        self._is_firing = False

    def handle(self, handler):
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            if not self._is_firing:
                self.handlers.remove(handler)
            else:
                self._to_remove.append(handler)
        except TypeError:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        self._is_firing = True
        for handler in self.handlers:
            if handler in self._to_remove:
                continue
            if handler(*args, **kargs) is False:
                self._to_remove.append(handler)
        self._is_firing = False
        for handler in self._to_remove:
            self.unhandle(handler)
        self._to_remove = []

    def getHandlerCount(self):
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__  = getHandlerCount


class Scheduler(object):
    """ A generic class for scheduling events to occur in the future. """
    def __init__(self, delay):
        """
        Schedule the fired event to be fired delay time units in the future.
        The addtime(time) method must be called to add time units to the
        internal clock.
        """
        self._delay = delay
        self._clock = 0
        self.fired = Event()
        self.is_fired = False

    def addtime(self, time):
        """
        Add time to the Scheduler's internal clock. If the internal clock
        exceeds the delay the fired event will fire.
        """
        self._clock += time
        if self._clock >= self._delay:
            self.is_fired = True
            self.fired()