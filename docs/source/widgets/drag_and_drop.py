import idom


@idom.element
async def DragDropBoxes(self):
    last_owner = idom.Var(None)
    last_hover = idom.Var(None)

    h1 = Holder("filled", last_owner, last_hover)
    h2 = Holder("empty", last_owner, last_hover)
    h3 = Holder("empty", last_owner, last_hover)

    last_owner.set(h1)

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

    return idom.html.div([style, h1, h2, h3])


@idom.element(state="last_owner, last_hover")
async def Holder(self, kind, last_owner, last_hover):
    @idom.event(prevent_default=True, stop_propagation=True)
    async def hover(event):
        if kind != "hover":
            self.update("hover")
            old = last_hover.set(self)
            if old is not None and old is not self:
                old.update("empty")

    async def start(event):
        last_hover.set(self)
        self.update("hover")

    async def end(event):
        last_owner.get().update("filled")

    async def leave(event):
        self.update("empty")

    async def dropped(event):
        if last_owner.get() is not self:
            old = last_owner.set(self)
            old.update("empty")
        self.update("filled")

    return idom.html.div(
        {
            "draggable": (kind == "filled"),
            "onDragStart": start,
            "onDragOver": hover,
            "onDragEnd": end,
            "onDragLeave": leave,
            "onDrop": dropped,
            "class": f"holder-{kind} holder",
        }
    )


display(DragDropBoxes)
