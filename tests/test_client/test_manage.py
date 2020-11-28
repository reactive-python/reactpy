import pytest


from idom.client.manage import web_module_url, build, restore


@pytest.fixture(scope="module", autouse=True)
def _setup_build_for_tests():
    build([{"source_name": "tests", "js_dependencies": ["jquery"]}])
    try:
        yield
    finally:
        restore()


def test_web_module_url():
    assert web_module_url("tests", "path/does/not/exist.js") is None
    assert web_module_url("tests", "jquery") == "../web_modules/jquery-tests-56e1841.js"
