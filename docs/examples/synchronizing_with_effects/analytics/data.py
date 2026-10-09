"""Collects the analytics events a component reports."""


class Analytics:
    def __init__(self):
        self.sent = []

    def log_visit(self, page):
        self.sent.append(page)


analytics = Analytics()
