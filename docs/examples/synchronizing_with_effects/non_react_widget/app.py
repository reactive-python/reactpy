"""Keep a non-ReactPy object in sync with state, and destroy it on unmount."""

from data import ReportEngine

from reactpy import Ref, component, html, use_effect, use_ref, use_state


# start
@component
def report(name):
    page_size, set_page_size = use_state("letter")
    # The engine lives in a ref: it has to survive renders, and changing it
    # must not itself trigger a render.
    engine_box: Ref[ReportEngine | None] = use_ref(None)

    def create_engine():
        engine = ReportEngine(name)
        engine_box.current = engine

        def destroy():
            engine.destroy()
            engine_box.current = None

        return destroy

    use_effect(create_engine, dependencies=[name])

    def apply_page_size():
        if engine_box.current is not None:
            engine_box.current.set_page_size(page_size)

    use_effect(apply_page_size, dependencies=[page_size])

    async def handle_page_size_click(event):
        set_page_size("a4" if page_size == "letter" else "letter")

    return html.div(
        html.h2(name),
        html.p(f"page size: {page_size}"),
        html.button(
            {"onClick": handle_page_size_click},
            "Toggle page size",
        ),
    )
