import re

from pathlib import Path
from jsonschema import ValidationError

import pytest

import idom
from idom.client.build_config import (
    BuildConfig,
    find_build_config_entry_in_python_file,
    find_python_packages_build_config_entries,
    split_package_name_and_version,
    validate_config,
    derive_config_entry_info,
    ConfigEntryInfo,
)


HERE = Path(__file__).parent
MOCK_SITE_PACKAGES = HERE / "mock_site_packages"
MOCK_JS_PACKAGE = MOCK_SITE_PACKAGES / "some_js_pkg"


@pytest.fixture
def make_build_config(tmp_path):
    """A fixture for quickly constructing build configs"""

    def make(*config_entries):
        config = BuildConfig(tmp_path)
        config.update_entries(config_entries)
        config.save()
        return config

    return make


@pytest.fixture
def prefab_build_config(make_build_config):
    return make_build_config(
        {"source_name": "module_1", "js_dependencies": ["dep1", "dep2"]},
        {"source_name": "module_2", "js_dependencies": ["dep2", "dep3"]},
        {"source_name": "module_3", "js_package": str(MOCK_JS_PACKAGE)},
    )


@pytest.mark.parametrize(
    "value, expectation",
    [
        (
            {
                "version": "1.2.3",
                "entries": {"some_module": {}},
            },
            "'source_name' is a required property",
        ),
        (
            {
                "version": "1.2.3",
                "entries": {"some_module": {"source_name": None}},
            },
            "None is not of type 'string'",
        ),
        (
            {
                "version": "1.2.3",
                "entries": {"some_module": {"source_name": "$bad-symbols!"}},
            },
            r"'\$bad-symbols\!' does not match",
        ),
        (
            {
                "version": "1.2.3",
                "entries": {"some_module": {"source_name": "some_module"}},
            },
            None,
        ),
        (
            {
                "version": "1.2.3",
                "entries": {
                    "some_module": {
                        "source_name": "some_module",
                        "js_dependencies": None,
                    }
                },
            },
            "None is not of type 'array'",
        ),
        (
            {
                "version": "1.2.3",
                "entries": {
                    "some_module": {
                        "source_name": "some_module",
                        "js_dependencies": [],
                    }
                },
            },
            None,
        ),
        (
            {
                "version": "1.2.3",
                "entries": {
                    "some_module": {
                        "source_name": "some_module",
                        "js_dependencies": [None],
                    }
                },
            },
            "None is not of type 'string'",
        ),
        (
            {
                "version": "1.2.3",
                "entries": {
                    "some_module": {
                        "source_name": "some_module",
                        "js_dependencies": ["dep1", "dep2"],
                    }
                },
            },
            None,
        ),
    ],
)
def test_validate_config_schema(value, expectation):
    if expectation is None:
        validate_config(value)
    else:
        with pytest.raises(ValidationError, match=expectation):
            validate_config(value)


def test_derive_config_entry_info():
    assert derive_config_entry_info(
        {
            "source_name": "some_module",
            "js_dependencies": ["dep1", "dep2"],
        }
    ) == ConfigEntryInfo(
        js_dependency_aliases={
            "dep1": "dep1-some_module-261bad9",
            "dep2": "dep2-some_module-261bad9",
        },
        aliased_js_dependencies=[
            "dep1-some_module-261bad9@npm:dep1",
            "dep2-some_module-261bad9@npm:dep2",
        ],
        js_package_def=None,
    )


def test_find_build_config_entry_in_python_file(tmp_path):
    py_module_path = tmp_path / "a_test.py"
    with py_module_path.open("w") as f:
        f.write("idom_build_config = {'js_dependencies': ['some-js-package']}")
    actual_config = find_build_config_entry_in_python_file("a_test", py_module_path)
    assert actual_config == {
        "source_name": "a_test",
        "js_dependencies": ["some-js-package"],
    }


def test_build_config_file_load_absent_config(make_build_config):
    assert make_build_config().data == {
        "version": idom.__version__,
        "entries": {},
    }


def test_build_config_file_repr(make_build_config):
    config = make_build_config()
    config.update_entries(
        [{"source_name": "a_test", "js_dependencies": ["a-different-package"]}]
    )
    assert str(config) == f"BuildConfig({config.data})"


def test_build_config_file_add_config_entry_and_save(make_build_config):
    config = make_build_config()
    config.update_entries(
        [{"source_name": "a_test", "js_dependencies": ["some-js-package"]}]
    )
    config.save()

    assert make_build_config().data["entries"] == {
        "a_test": {"source_name": "a_test", "js_dependencies": ["some-js-package"]}
    }
    assert make_build_config().has_entry("a_test")


def test_find_python_packages_build_config_entries():
    mock_site_pkgs_path = str(MOCK_SITE_PACKAGES.absolute())
    configs, errors = find_python_packages_build_config_entries([mock_site_pkgs_path])

    assert configs == [
        {
            "source_name": "has_good_config",
            "js_dependencies": ["some-js-package"],
        },
        {
            "source_name": "has_js_package",
            "js_package": str(MOCK_JS_PACKAGE.absolute().resolve()),
        },
    ]

    for error_msg, expected_msg in zip(
        sorted([str(e.__cause__) for e in errors]),
        ["1 is not of type 'string'", r"js_package.*? is not allowed"],
    ):
        assert re.search(expected_msg, error_msg)


@pytest.mark.parametrize(
    "package_specifier,expected_name_and_version",
    [
        ("package", ("package", "")),
        ("package@1.2.3", ("package", "1.2.3")),
        ("@scope/pkg", ("@scope/pkg", "")),
        ("@scope/pkg@1.2.3", ("@scope/pkg", "1.2.3")),
        ("alias@npm:package", ("alias", "npm:package")),
        ("alias@npm:package@1.2.3", ("alias", "npm:package@1.2.3")),
        ("alias@npm:@scope/pkg@1.2.3", ("alias", "npm:@scope/pkg@1.2.3")),
        ("@alias/pkg@npm:@scope/pkg@1.2.3", ("@alias/pkg", "npm:@scope/pkg@1.2.3")),
    ],
)
def test_split_package_name_and_version(package_specifier, expected_name_and_version):
    assert (
        split_package_name_and_version(package_specifier) == expected_name_and_version
    )


def test_build_config_all_js_dependencies(prefab_build_config):
    assert prefab_build_config.all_js_dependencies() == [
        "dep1-module_1-5001a4b@npm:dep1",
        "dep2-module_1-5001a4b@npm:dep2",
        "dep2-module_2-46d6db8@npm:dep2",
        "dep3-module_2-46d6db8@npm:dep3",
        str(MOCK_JS_PACKAGE.absolute()),
    ]


def test_build_config_all_js_dependency_names(prefab_build_config):
    assert prefab_build_config.all_js_dependency_names() == [
        "dep1-module_1-5001a4b",
        "dep2-module_1-5001a4b",
        "dep2-module_2-46d6db8",
        "dep3-module_2-46d6db8",
        "some_js_pkg",
    ]


@pytest.mark.parametrize(
    "given_dep, resolved_dep",
    [
        ("module_1:dep1", "dep1-module_1-5001a4b"),
        ("module_1:dep2", "dep2-module_1-5001a4b"),
        ("module_2:dep2", "dep2-module_2-46d6db8"),
        ("module_2:dep3", "dep3-module_2-46d6db8"),
        ("module_1:missing_dep", None),
        ("module_3:some_js_pkg", "some_js_pkg"),
        ("module_3:missing_dep", None),
        ("missing_module:some_dep", None),
    ],
)
def test_resolve_js_dependency_name(prefab_build_config, given_dep, resolved_dep):
    assert (
        prefab_build_config.resolve_js_dependency_name(*given_dep.split(":"))
        == resolved_dep
    )


def test_non_existant_js_package_path(make_build_config):
    config = make_build_config()
    with pytest.raises(ValueError, match=r"does not exist"):
        config.update_entries(
            [{"source_name": "tests", "js_package": "path/does/not/exist"}]
        )
