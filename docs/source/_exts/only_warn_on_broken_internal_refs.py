from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging


logger = logging.getLogger(__name__)


def is_public_internal_ref_target(target: str) -> bool:
    return target.startswith("idom.") and not target.rsplit(".", 1)[-1].startswith("_")


class OnlyWarnOnBrokenInternalRefs(SphinxPostTransform):
    """
    Warns about broken cross-reference links, but only for idom.
    This is very similar to the sphinx option ``nitpicky=True`` (see
    :py:class:`sphinx.transforms.post_transforms.ReferencesResolver`), but there
    is no way to restrict that option to a specific package.
    """

    # this transform needs to happen before ReferencesResolver
    default_priority = 5

    def run(self) -> None:
        for node in self.document.traverse(addnodes.pending_xref):
            target = node["reftarget"]

            if is_public_internal_ref_target(target):
                # let the domain try to resolve the reference
                found_ref = self.env.domains[node["refdomain"]].resolve_xref(
                    self.env,
                    node.get("refdoc", self.env.docname),
                    self.app.builder,
                    node["reftype"],
                    target,
                    node,
                    nodes.TextElement("", ""),
                )

                # warn if resolve_xref did not return or raised
                if not found_ref:
                    logger.warning(
                        f"API link {target} is broken.", location=node, type="ref"
                    )


def setup(app: Sphinx) -> None:
    app.add_post_transform(OnlyWarnOnBrokenInternalRefs)
