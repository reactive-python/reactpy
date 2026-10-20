"""Effect order: children first, siblings in reverse, parent last."""

from reactpy import component, html, use_effect


# start
@component
def leaf(name):
    @use_effect
    def first():
        print(f"{name}: first effect")

    @use_effect
    def second():
        print(f"{name}: second effect")

    return html.p(name)


@component
def panel():
    @use_effect
    def parent_effect():
        print("panel: my own effect")

    # Two children: the SECOND one's effects run first.
    return html.div(leaf("alpha"), leaf("beta"))


@component
def app():
    return html.div(
        html.h1("Watch the server console"),
        panel(),
    )
