"""A failing Effect is invisible in the page and invisible in the log."""

from reactpy import component, html, use_effect, use_state


# start
@component
def dashboard():
    refreshes, set_refreshes = use_state(0)

    def effect():
        # Suppose this reads a metric from a database and the query fails.
        #
        # The page does not change, the browser console stays clean, and no
        # error reaches the model. The ONLY trace is a traceback on the
        # server -- and, as written here, it does not even appear until the
        # component unmounts. Test your Effects; the UI will not report them.
        msg = "metric query failed"
        raise RuntimeError(msg)

    use_effect(effect, dependencies=[refreshes])

    return html.div(
        html.h1("Dashboard looks fine"),
        html.button({"onClick": lambda event: set_refreshes(refreshes + 1)}, "Refresh"),
    )
