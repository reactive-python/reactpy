import pytest

import idom
from idom.client.manage import (
    add_web_module,
    build,
    remove_web_module,
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


def test_cannot_add_web_module_if_already_exists(tmp_path):
    first_temp_file = tmp_path / "temp-1.js"
    second_temp_file = tmp_path / "temp-2.js"

    first_temp_file.write_text("console.log('hello!')")  # this won't get run
    second_temp_file.write_text("console.log('hello!')")  # this won't get run

    add_web_module("test", first_temp_file)
    with pytest.raises(FileExistsError):
        add_web_module("test", second_temp_file)

    remove_web_module("test")


def test_can_add_web_module_if_already_exists_and_source_is_same(tmp_path):
    temp_file = tmp_path / "temp.js"
    temp_file.write_text("console.log('hello!')")
    add_web_module("test", temp_file)
    add_web_module("test", temp_file)
    remove_web_module("test")


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
