import pytest

import idom
from idom.client.manage import (
    add_web_module,
    build,
    restore,
    web_module_exists,
    web_module_exports,
    web_module_path,
)
from tests.general_utils import assert_same_items


@pytest.fixture(scope="module")
def victory():
    return idom.install("victory@35.4.0")


def test_clean_build():
    restore()
    build(["jquery"])
    assert web_module_exists("jquery")
    build([], clean_build=True)
    assert not web_module_exists("jquery")


def test_add_web_module_source_must_exist(tmp_path):
    with pytest.raises(FileNotFoundError, match="Package source file does not exist"):
        add_web_module("test", tmp_path / "file-does-not-exist.js")


def test_web_module_path_must_exist():
    with pytest.raises(ValueError, match="does not exist at path"):
        web_module_path("this-does-not-exist", must_exist=True)
    assert not web_module_path("this-does-not-exist", must_exist=False).exists()


def test_web_module_exports(victory):
    assert_same_items(
        web_module_exports("victory"),
        [
            "Area",
            "Axis",
            "Background",
            "Bar",
            "Border",
            "Box",
            "BrushHelpers",
            "Candle",
            "Circle",
            "ClipPath",
            "Collection",
            "CursorHelpers",
            "Curve",
            "Data",
            "DefaultTransitions",
            "Domain",
            "ErrorBar",
            "Events",
            "Flyout",
            "Helpers",
            "LabelHelpers",
            "Line",
            "LineSegment",
            "Log",
            "Path",
            "Point",
            "Portal",
            "PropTypes",
            "RawZoomHelpers",
            "Rect",
            "Scale",
            "Selection",
            "SelectionHelpers",
            "Slice",
            "Style",
            "TSpan",
            "Text",
            "TextSize",
            "Transitions",
            "VictoryAnimation",
            "VictoryArea",
            "VictoryAxis",
            "VictoryBar",
            "VictoryBoxPlot",
            "VictoryBrushContainer",
            "VictoryBrushLine",
            "VictoryCandlestick",
            "VictoryChart",
            "VictoryClipContainer",
            "VictoryContainer",
            "VictoryCursorContainer",
            "VictoryErrorBar",
            "VictoryGroup",
            "VictoryHistogram",
            "VictoryLabel",
            "VictoryLegend",
            "VictoryLine",
            "VictoryPie",
            "VictoryPolarAxis",
            "VictoryPortal",
            "VictoryScatter",
            "VictorySelectionContainer",
            "VictorySharedEvents",
            "VictoryStack",
            "VictoryTheme",
            "VictoryTooltip",
            "VictoryTransition",
            "VictoryVoronoi",
            "VictoryVoronoiContainer",
            "VictoryZoomContainer",
            "Voronoi",
            "VoronoiHelpers",
            "Whisker",
            "Wrapper",
            "ZoomHelpers",
            "addEvents",
            "brushContainerMixin",
            "combineContainerMixins",
            "createContainer",
            "cursorContainerMixin",
            "makeCreateContainerFunction",
            "selectionContainerMixin",
            "voronoiContainerMixin",
            "zoomContainerMixin",
        ],
    )
