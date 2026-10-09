"""A stand-in for the server connection an Effect opens and closes."""


class ChatServer:
    def __init__(self):
        self.log = []
        self.open_count = 0

    def connect(self, room):
        """Return the function that closes this particular connection."""
        self.open_count += 1
        self.log.append(f"connect {room}")

        def close():
            self.open_count -= 1
            self.log.append(f"close {room}")

        return close


chat_server = ChatServer()
