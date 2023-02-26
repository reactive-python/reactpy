from reactpy import component, html, run


@component
def Photo():
    return html.img(
        {
            "src": "https://picsum.photos/id/274/500/300",
            "style": {"width": "30%"},
            "alt": "Ray Charles",
        }
    )


@component
def Gallery():
    return html.section(
        html.h1("Famous Musicians"),
        Photo(),
        Photo(),
        Photo(),
    )


run(Gallery)
