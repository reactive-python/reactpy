import json
from pathlib import Path

from reactpy import component, hooks, html, run

HERE = Path(__file__)
DATA_PATH = HERE.parent / "data.json"
food_data = json.loads(DATA_PATH.read_text())


@component
def FilterableList():
    value, set_value = hooks.use_state("")
    return html.p(Search(value, set_value), html.hr(), Table(value, set_value))


@component
def Search(value, set_value):
    def handle_change(event):
        set_value(event["target"]["value"])

    return html.label(
        "Search by Food Name: ",
        html.input({"value": value, "on_change": handle_change}),
    )


@component
def Table(value, set_value):
    rows = []
    for row in food_data:
        name = html.td(row["name"])
        descr = html.td(row["description"])
        tr = html.tr(name, descr, value)
        if not value:
            rows.append(tr)
        elif value.lower() in row["name"].lower():
            rows.append(tr)
        headers = html.tr(html.td(html.b("name")), html.td(html.b("description")))
    table = html.table(html.thead(headers), html.tbody(rows))
    return table


run(FilterableList)
