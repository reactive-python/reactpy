"""The dataset the filter example runs over, plus a call counter."""

# Every todo the list could show. Large enough that filtering is worth
# measuring, small enough to keep the rendered page readable.
todos = [
    {"id": 1, "text": "Write the effect-free draft", "completed": True},
    {"id": 2, "text": "Port the remaining hooks", "completed": False},
    {"id": 3, "text": "Measure render counts", "completed": False},
    {"id": 4, "text": "Delete the redundant state", "completed": False},
    {"id": 5, "text": "Write clean-ups for every subscription", "completed": False},
    {"id": 6, "text": "Replace the derived Effects", "completed": False},
    {"id": 7, "text": "Move handlers out of Effects", "completed": True},
    {"id": 8, "text": "Review the state shape", "completed": True},
    {
        "id": 9,
        "text": "Add a regression test for the stale closure",
        "completed": False,
    },
    {"id": 10, "text": "Ship it", "completed": False},
]

# The filter function appends to this on every run, so the docs can state how
# often it actually executes.
filter_runs = []
