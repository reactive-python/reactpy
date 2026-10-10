"""The same tree flattened into one dict keyed by id."""

PLACES = {
    0: {"id": 0, "title": "(Root)", "childIds": [1]},
    1: {"id": 1, "title": "Earth", "childIds": [2, 10, 21]},
    2: {"id": 2, "title": "Africa", "childIds": [3, 4, 5]},
    3: {"id": 3, "title": "Botswana", "childIds": []},
    4: {"id": 4, "title": "Egypt", "childIds": []},
    5: {"id": 5, "title": "Kenya", "childIds": []},
    10: {"id": 10, "title": "Americas", "childIds": [11, 12, 13]},
    11: {"id": 11, "title": "Argentina", "childIds": []},
    12: {"id": 12, "title": "Brazil", "childIds": []},
    13: {"id": 13, "title": "Barbados", "childIds": []},
    21: {"id": 21, "title": "Asia", "childIds": [22, 23]},
    22: {"id": 22, "title": "Japan", "childIds": []},
    23: {"id": 23, "title": "Nepal", "childIds": []},
}
