from reactpy import component, html, use_state


# start
@component
def text_field():
    first_name, set_first_name = use_state("Ada")

    return html.div(
        html.input(
            {
                "value": first_name,
                "onChange": lambda event: set_first_name(event["target"]["value"]),
            }
        ),
        html.h1(f"Hello, {first_name}!"),
    )
