friends = [
    {
        "id": 0,
        "name": "Creola Katherine Johnson",
        "image_id": "MK3eW3A",
    },
    {
        "id": 1,
        "name": "Mario José Molina-Pasquel Henríquez",
        "image_id": "mynHUSa",
    },
    {
        "id": 2,
        "name": "Mohammad Abdus Salam",
        "image_id": "bE7W1ji",
    },
]


def get_image_url(person):
    return f"https://i.imgur.com/{person['image_id']}.jpg"
