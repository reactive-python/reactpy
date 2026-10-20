from reactpy import component, html, use_debug_value, use_state

# start


@component
def report():
    rows, set_rows = use_state([{"name": "ada", "score": 91}])

    # Pass a function when turning the message into text is not free. ReactPy
    # memoizes it like any other hook, so it re-runs only when what it reads
    # changes -- and not at all on renders that would not have logged anything.
    def describe():
        best = max(rows, key=lambda row: row["score"])
        return f"{len(rows)} rows, best={best['name']}:{best['score']}"

    use_debug_value(describe)

    async def add_row(event=None):
        set_rows([*rows, {"name": f"row {len(rows)}", "score": len(rows) * 7}])

    return html.div(
        html.h1(f"{len(rows)} rows"),
        html.button({"onClick": add_row}, "Add row"),
    )
