"""Transform the response during render, not in an Effect after it lands."""

from data import catalog

from reactpy import component, html, use_async_effect, use_state


# start
@component
def report_view(name):
    # Store the response *with the name it belongs to*, so a render for a new
    # report cannot display the old one's rows. The empty read is the
    # "loading" state -- derived, not a second state variable.
    loaded, set_loaded = use_state({"name": None, "data": {}})

    async def load():
        data = await catalog.fetch(name)
        set_loaded({"name": name, "data": data})

    use_async_effect(load, dependencies=[name])

    raw = loaded["data"] if loaded["name"] == name else {}

    if not raw:
        return html.p("loading...")

    # Right: the shape the page needs is computed here, from the data that
    # arrived. There is no second state variable to keep in step, so there is
    # nothing for an Effect to synchronise.
    rows = [{"label": key.title(), "value": value} for key, value in raw.items()]
    total = sum(row["value"] for row in rows)
    lines = [
        html.li({"key": row["label"]}, f"{row['label']}: {row['value']}")
        for row in rows
    ]

    return html.div(
        html.h2(f"{name}: {total} total"),
        html.ul(lines),
    )


@component
def app():
    name, set_name = use_state("orders")

    return html.div(
        html.button(
            {
                "onClick": lambda event: set_name(
                    "users" if name == "orders" else "orders"
                )
            },
            "Toggle report",
        ),
        # No `key` here on purpose: the derived read in report_view is what
        # keeps the old report off the screen, so nothing has to be remounted.
        report_view(name),
    )


# end
