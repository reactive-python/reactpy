from idom import component, html, run, use_state


@component
def Grid():
    line_size = 5
    selected_indices, set_selected_indices = use_state(set())

    def make_handle_click(index):
        def handle_click(event):
            set_selected_indices(selected_indices | {index})

        return handle_click

    return html.div(
        [
            html.div(
                key=index,
                on_click=make_handle_click(index),
                style={
                    "height": "30px",
                    "width": "30px",
                    "backgroundColor": "black"
                    if index in selected_indices
                    else "white",
                    "outline": "1px solid grey",
                    "cursor": "pointer",
                },
            )
            for index in range(line_size)
        ],
        style={"display": "flex", "flex-direction": "row"},
    )


run(Grid)
