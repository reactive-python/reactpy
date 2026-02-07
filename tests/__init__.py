import pytest

from reactpy.testing import GITHUB_ACTIONS

pytestmark = [pytest.mark.flaky(reruns=10 if GITHUB_ACTIONS else 1)]
