people = [
    {
        "id": 0,  # used as the key
        "name": "Creola Katherine Johnson",
        "profession": "mathematician",
        "accomplishment": "spaceflight calculations",
        "image_id": "MK3eW3A",
    },
    {
        "id": 1,  # used as the key
        "name": "Mario José Molina-Pasquel Henríquez",
        "profession": "chemist",
        "accomplishment": "discovery of Arctic ozone hole",
        "image_id": "mynHUSa",
    },
    {
        "id": 2,  # used as the key
        "name": "Mohammad Abdus Salam",
        "profession": "physicist",
        "accomplishment": "electromagnetism theory",
        "image_id": "bE7W1ji",
    },
    {
        "id": 3,  # used as the key
        "name": "Percy Lavon Julian",
        "profession": "chemist",
        "accomplishment": "pioneering cortisone drugs, steroids and birth control pills",
        "image_id": "IOjWm71",
    },
    {
        "id": 4,  # used as the key
        "name": "Subrahmanyan Chandrasekhar",
        "profession": "astrophysicist",
        "accomplishment": "white dwarf star mass calculations",
        "image_id": "lrWQx8l",
    },
]


def get_image_url(person):
    return f"../../assets/images/demos/{person['image_id']}s.jpg"
