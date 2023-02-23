from reactpy import component, html, run, use_state


@component
def Grid():
    line_size = 5
    selected_indices, set_selected_indices = use_state({1, 2, 4})

    def make_handle_click(index):
        def handle_click(event):
            if index in selected_indices:
                set_selected_indices(selected_indices - {index})
            else:
                set_selected_indices(selected_indices | {index})

        return handle_click

    return html.div(
        {"style": {"display": "flex", "flex-direction": "row"}},
        [
            html.div(
                {
                    "on_click": make_handle_click(index),
                    "style": {
                        "height": "30px",
                        "width": "30px",
                        "background_color": "black"
                        if index in selected_indices
                        else "white",
                        "outline": "1px solid grey",
                        "cursor": "pointer",
                    },
                    "key": index,
                }
            )
            for index in range(line_size)
        ],
    )


run(Grid)
