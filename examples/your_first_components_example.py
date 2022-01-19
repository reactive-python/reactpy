from idom import component, html, run


@component
def Photo():
    return html.img(
        {
            "src": "https://picsum.photos/id/237/500/300",
            "style": {"width": "50%"},
            "alt": "Puppy",
        }
    )


run(Photo)