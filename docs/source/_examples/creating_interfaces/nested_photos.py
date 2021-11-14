from idom import component, html, run


@component
def Photo():
    return html.img(
        {
            "src": "https://i.pinimg.com/564x/d6/96/c4/d696c4d3db31609c1abb05c52f305ec1.jpg",
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
