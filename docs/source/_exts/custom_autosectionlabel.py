"""Mostly copied from sphinx.ext.autosectionlabel

See Sphinx BSD license:
https://github.com/sphinx-doc/sphinx/blob/f9968594206e538f13fa1c27c065027f10d4ea27/LICENSE
"""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Any, cast

from docutils import nodes
from docutils.nodes import Node
from sphinx.application import Sphinx
from sphinx.domains.std import StandardDomain
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.nodes import clean_astext

logger = logging.getLogger(__name__)


def get_node_depth(node: Node) -> int:
    i = 0
    cur_node = node
    while cur_node.parent != node.document:
        cur_node = cur_node.parent
        i += 1
    return i


def register_sections_as_label(app: Sphinx, document: Node) -> None:
    docname = app.env.docname

    for pattern in app.config.autosectionlabel_skip_docs:
        if fnmatch(docname, pattern):
            return None

    domain = cast(StandardDomain, app.env.get_domain("std"))
    for node in document.traverse(nodes.section):
        if (
            app.config.autosectionlabel_maxdepth
            and get_node_depth(node) >= app.config.autosectionlabel_maxdepth
        ):
            continue
        labelid = node["ids"][0]

        title = cast(nodes.title, node[0])
        ref_name = getattr(title, "rawsource", title.astext())
        if app.config.autosectionlabel_prefix_document:
            name = nodes.fully_normalize_name(docname + ":" + ref_name)
        else:
            name = nodes.fully_normalize_name(ref_name)
        sectname = clean_astext(title)

        if name in domain.labels:
            logger.warning(
                __("duplicate label %s, other instance in %s"),
                name,
                app.env.doc2path(domain.labels[name][0]),
                location=node,
                type="autosectionlabel",
                subtype=docname,
            )

        domain.anonlabels[name] = docname, labelid
        domain.labels[name] = docname, labelid, sectname


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value("autosectionlabel_prefix_document", False, "env")
    app.add_config_value("autosectionlabel_maxdepth", None, "env")
    app.add_config_value("autosectionlabel_skip_docs", [], "env")
    app.connect("doctree-read", register_sections_as_label)

    return {
        "version": "builtin",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
