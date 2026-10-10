"""The same tree as nested objects, the shape this section argues against."""

INITIAL_PLAN = {
    "id": 0,
    "title": "(Root)",
    "childPlaces": [
        {
            "id": 1,
            "title": "Earth",
            "childPlaces": [
                {
                    "id": 2,
                    "title": "Africa",
                    "childPlaces": [
                        {"id": 3, "title": "Botswana", "childPlaces": []},
                        {"id": 4, "title": "Egypt", "childPlaces": []},
                        {"id": 5, "title": "Kenya", "childPlaces": []},
                    ],
                },
                {
                    "id": 10,
                    "title": "Americas",
                    "childPlaces": [
                        {"id": 11, "title": "Argentina", "childPlaces": []},
                        {"id": 12, "title": "Brazil", "childPlaces": []},
                        {"id": 13, "title": "Barbados", "childPlaces": []},
                    ],
                },
                {
                    "id": 21,
                    "title": "Asia",
                    "childPlaces": [
                        {"id": 22, "title": "Japan", "childPlaces": []},
                        {"id": 23, "title": "Nepal", "childPlaces": []},
                    ],
                },
            ],
        }
    ],
}
