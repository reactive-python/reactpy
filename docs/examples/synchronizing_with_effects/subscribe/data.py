"""A stand-in for any pub/sub system with subscribe/unsubscribe semantics."""


class Ticker:
    def __init__(self):
        self.topics = {}
        self.log = []

    def subscribe(self, topic, callback):
        self.log.append(f"subscribe {topic}")
        self.topics.setdefault(topic, []).append(callback)

        def unsubscribe():
            self.log.append(f"unsubscribe {topic}")
            self.topics[topic].remove(callback)

        return unsubscribe

    def publish(self, topic, message):
        for callback in list(self.topics.get(topic, [])):
            callback(message)

    def subscriber_count(self, topic):
        return len(self.topics.get(topic, []))


ticker = Ticker()
