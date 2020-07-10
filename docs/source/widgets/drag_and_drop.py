import idom


@idom.element
async def DragDropBoxes(number_of_boxes=3):
    shared_current_index = idom.hooks.Shared(0)

    boxes = [Holder(i, shared_current_index) for i in range(number_of_boxes)]

    style = idom.html.style(
        [
            """
    .holder {
    height: 150px;
    width: 150px;
    margin: 20px;
    display: inline-block;
    }
    .holder-filled {
    border: solid 10px black;
    background-color: black;
    }
    .holder-hover {
    border: dotted 5px black;
    }
    .holder-empty {
    border: solid 5px black;
    background-color: white;
    }
    """
        ]
    )

    return idom.html.div(style, boxes)


@idom.element
async def Holder(index, shared_current_index):
    current_index, set_current_index = idom.hooks.use_state(shared_current_index)

    hovered, set_hovered = idom.hooks.use_state(False)

    if current_index == index:
        state = "filled"
    elif hovered:
        state = "hover"
    else:
        state = "empty"

    @idom.event(prevent_default=True, stop_propagation=True)
    async def on_hover(event):
        if not hovered:
            set_hovered(True)

    async def on_start(event):
        set_hovered(True)
        set_current_index(None)

    async def on_leave(event):
        if hovered:
            set_hovered(False)

    async def on_drop(event):
        set_current_index(index)

    return idom.html.div(
        {
            "draggable": (state == "filled"),
            "onDragStart": on_start,
            "onDragOver": on_hover,
            "onDragLeave": on_leave,
            "onDrop": on_drop,
            "class": f"holder-{state} holder",
        }
    )


display(DragDropBoxes)
