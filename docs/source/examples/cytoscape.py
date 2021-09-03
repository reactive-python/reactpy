import idom


react_cytoscapejs = idom.web.module_from_template(
    # we need to use this template because react-cytoscapejs uses a default export
    "react-default",
    "react-cytoscapejs",
    fallback="⌛",
)
Cytoscape = idom.web.export(react_cytoscapejs, "default")


@idom.component
def CytoscapeGraph():
    return Cytoscape(
        {
            "style": {"width": "100%", "height": "200px"},
            "elements": [
                {
                    "data": {"id": "one", "label": "Node 1"},
                    "position": {"x": 100, "y": 100},
                },
                {
                    "data": {"id": "two", "label": "Node 2"},
                    "position": {"x": 200, "y": 100},
                },
                {
                    "data": {
                        "source": "one",
                        "target": "two",
                        "label": "Edge from Node1 to Node2",
                    }
                },
            ],
        }
    )


idom.run(CytoscapeGraph)
