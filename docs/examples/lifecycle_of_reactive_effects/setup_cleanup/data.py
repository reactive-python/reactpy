"""A connection pool the setup/cleanup example can report on."""


class Server:
    def __init__(self):
        self.log = []
        self.open_count = 0

    def connect(self, room):
        self.open_count += 1
        self.log.append(f"connect {room}")

        def close():
            self.open_count -= 1
            self.log.append(f"close {room}")

        return close


server = Server()
