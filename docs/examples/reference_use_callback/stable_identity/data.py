"""A stand-in for any registry that lives outside ReactPy.

This is the shape of code where a callback's identity actually matters: the
registry is ordinary Python, so nothing deduplicates it for you -- it stores
handlers by identity, and a *new* function object on each render means a new
entry each render.
"""


class Bus:
    def __init__(self):
        self.handlers = []
        self.handled = []

    def subscribe(self, handler):
        # `in` on a list of plain functions compares by identity, which is
        # exactly what a new `def` per render changes.
        if handler not in self.handlers:
            self.handlers.append(handler)

    def publish(self, message):
        for handler in list(self.handlers):
            handler(message)


bus = Bus()
