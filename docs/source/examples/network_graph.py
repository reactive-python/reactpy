import random

import idom


react_cytoscapejs = idom.web.module_from_template(
    # we need to use this template because react-cytoscapejs uses a default export
    "react",
    "react-cytoscapejs",
    exports_default=True,
    fallback="⌛",
)
Cytoscape = idom.web.export(react_cytoscapejs, "default")


@idom.component
def RandomNetworkGraph():
    return Cytoscape(
        {
            "style": {"width": "100%", "height": "200px"},
            "elements": random_network(20),
            "layout": {"name": "cose"},
        }
    )


def random_network(number_of_nodes):
    conns = []
    nodes = [{"data": {"id": 0, "label": 0}}]

    for src_node_id in range(1, number_of_nodes + 1):
        tgt_node = random.choice(nodes)
        src_node = {"data": {"id": src_node_id, "label": src_node_id}}

        new_conn = {"data": {"source": src_node_id, "target": tgt_node["data"]["id"]}}

        nodes.append(src_node)
        conns.append(new_conn)

    return nodes + conns


idom.run(RandomNetworkGraph)
