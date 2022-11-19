import pytest

from idom.backend._common import traversal_safe_path


@pytest.mark.parametrize(
    "bad_path",
    [
        "../escaped",
        "ok/../../escaped",
        "ok/ok-again/../../ok-yet-again/../../../escaped",
    ],
)
def test_catch_unsafe_relative_path_traversal(tmp_path, bad_path):
    with pytest.raises(ValueError, match="Unsafe path"):
        traversal_safe_path(tmp_path, *bad_path.split("/"))
