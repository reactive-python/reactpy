import pytest

from idom.client.manage import (
    web_module_url,
    web_module_exports,
    web_module_exists,
    build,
    restore,
)

from tests.general_utils import assert_same_items


@pytest.fixture(scope="module", autouse=True)
def _setup_build_for_tests():
    build([{"source_name": "tests", "js_dependencies": ["victory@35.4.0"]}])
    try:
        yield
    finally:
        restore()


def test_web_module_url():
    assert (
        web_module_url("tests", "victory") == "../web_modules/victory-tests-24fa38b.js"
    )


def test_web_module_exists():
    assert not web_module_exists("tests", "does/not/exist")
    assert web_module_exists("tests", "victory")


def test_web_module_exports():
    assert_same_items(
        web_module_exports("tests", "victory"),
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
