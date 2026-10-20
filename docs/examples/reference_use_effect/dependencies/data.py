"""A stand-in for any external system with subscribe/unsubscribe semantics."""


class Ticker:
    def __init__(self):
        self.topics = {}

    def subscribe(self, topic, callback):
        self.topics.setdefault(topic, []).append(callback)

        def unsubscribe():
            self.topics[topic].remove(callback)

        return unsubscribe

    def publish(self, topic, message):
        for callback in list(self.topics.get(topic, [])):
            callback(message)

    def count(self):
        return sum(len(v) for v in self.topics.values())


ticker = Ticker()
