from data import sculptures

from reactpy import component, html, use_state


# start
@component
def gallery():
    index, set_index = use_state(0)
    sculpture = sculptures[index]
    return html.section(
        html.button(
            {"onClick": lambda event: set_index(index + 1)},
            "Next",
        ),
        html.h3(f"({index + 1} of {len(sculptures)})"),
        html.img({"src": sculpture["url"], "alt": sculpture["alt"]}),
    )


@component
def page():
    # Two separate mounts of the same component. Each call site is a different
    # position in the tree, so each gallery keeps its own index.
    return html.div(gallery(), gallery())
