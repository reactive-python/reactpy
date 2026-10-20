"""A plain publish/subscribe object: the external thing an Effect mirrors."""


class ServerClock:
    """Stands in for any external store: a value, plus subscribers."""

    def __init__(self):
        self._listeners = []
        self.ticks = 0

    def get(self):
        return self.ticks

    def subscribe(self, listener):
        self._listeners.append(listener)

        def unsubscribe():
            self._listeners.remove(listener)

        return unsubscribe

    def tick(self):
        """Called by whatever actually drives time: a timer, a socket, a queue."""
        self.ticks += 1
        for listener in list(self._listeners):
            listener()

    def listener_count(self):
        return len(self._listeners)


clock = ServerClock()
