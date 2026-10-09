"""A stand-in for a third-party object with imperative setters and a teardown."""

engines = []


class ReportEngine:
    def __init__(self, name):
        self.name = name
        self.page_size = "letter"
        self.alive = True
        self.log = [f"created {name}"]
        engines.append(self)

    def set_page_size(self, size):
        self.page_size = size
        self.log.append(f"set_page_size {size}")

    def destroy(self):
        self.alive = False
        self.log.append(f"destroyed {self.name}")
