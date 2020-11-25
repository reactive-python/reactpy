from pathlib import Path
from jsonschema import ValidationError

import pytest

import idom
from idom.client.build_config import (
    BuildConfig,
    find_build_config_item_in_python_file,
    find_python_packages_build_config_items,
    split_package_name_and_version,
    validate_config,
    derive_config_properties,
)


@pytest.fixture
def make_build_config(tmp_path):
    """A fixture for quickly constructing build configs"""

    def make(*config_items):
        config = BuildConfig(tmp_path)
        if config_items:
            with config.transaction():
                config.update_config_items(config_items)
        return config

    return make


@pytest.mark.parametrize(
    "value, expectation",
    [
        (
            {
                "version": "1.2.3",
                "by_source": {"some_module": {"source_name": None}},
            },
            "None is not of type 'string'",
        ),
        (
            {
                "version": "1.2.3",
                "by_source": {"some_module": {"source_name": "$bad-symbols!"}},
            },
            r"'\$bad-symbols\!' does not match",
        ),
        (
            {
                "version": "1.2.3",
                "by_source": {"some_module": {"source_name": "some_module"}},
            },
            None,
        ),
        (
            {
                "version": "1.2.3",
                "by_source": {
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
                "by_source": {
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
                "by_source": {
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
                "by_source": {
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


def test_derive_config_properties():
    assert derive_config_properties(
        {
            "version": "1.2.3",
            "by_source": {
                "some_module": {
                    "source_name": "some_module",
                    "js_dependencies": ["dep1", "dep2"],
                }
            },
        }
    ) == {
        "aliased_js_dependencies_by_source": {
            "some_module": [
                "dep1-some_module-261bad9@npm:dep1",
                "dep2-some_module-261bad9@npm:dep2",
            ]
        },
        "js_dependency_aliases_by_source": {
            "some_module": {
                "dep1": "dep1-some_module-261bad9",
                "dep2": "dep2-some_module-261bad9",
            }
        },
    }


def test_find_build_config_item_in_python_file(tmp_path):
    py_module_path = tmp_path / "a_test.py"
    with py_module_path.open("w") as f:
        f.write("idom_build_config = {'js_dependencies': ['some-js-package']}")
    actual_config = find_build_config_item_in_python_file("a_test", py_module_path)
    assert actual_config == {
        "source_name": "a_test",
        "js_dependencies": ["some-js-package"],
    }


def test_build_config_file_load_absent_config(make_build_config):
    assert make_build_config().config == {
        "version": idom.__version__,
        "by_source": {},
    }


def test_build_config_file_repr(make_build_config):
    with make_build_config().transaction() as config_file:
        config_file.update_config_items(
            [{"source_name": "a_test", "js_dependencies": ["a-different-package"]}]
        )

        assert str(config_file) == f"BuildConfig({config_file.config})"


def test_build_config_file_add_config_item(make_build_config):
    with make_build_config().transaction() as config_file:
        config_file.update_config_items(
            [{"source_name": "a_test", "js_dependencies": ["some-js-package"]}]
        )

    assert make_build_config().config["by_source"] == {
        "a_test": {"source_name": "a_test", "js_dependencies": ["some-js-package"]}
    }


@pytest.mark.parametrize("method", ["update_config_items"])
def test_some_build_config_file_methods_require_transaction(make_build_config, method):
    config_file = make_build_config()
    with pytest.raises(RuntimeError, match="must be used in a transaction"):
        getattr(config_file, method)()


@pytest.mark.parametrize(
    "method",
    [
        "get_js_dependency_alias",
        "all_aliased_js_dependencies",
        "all_js_dependency_aliases",
    ],
)
def test_some_build_config_file_methods_blocked_in_transaction(
    make_build_config, method
):
    config_file = make_build_config()
    with pytest.raises(RuntimeError, match="cannot be used in a transaction"):
        with config_file.transaction():
            getattr(config_file, method)()


def test_find_python_packages_build_config_items():
    mock_site_pkgs_path = str((Path(__file__).parent / "mock_site_packages").absolute())
    configs, errors = find_python_packages_build_config_items([mock_site_pkgs_path])
    assert configs == [
        {
            "source_name": "has_good_config",
            "js_dependencies": ["some-js-package"],
        }
    ]

    assert len(errors) == 1

    with pytest.raises(
        RuntimeError,
        match="Failed to load build config for module 'has_bad_config'",
    ):
        raise errors[0]

    with pytest.raises(ValidationError, match="1 is not of type 'string'"):
        raise errors[0].__cause__


def test_build_config_file_transaction_rollback(make_build_config):
    with pytest.raises(Exception):
        with make_build_config().transaction() as config_file:
            config_file.update_config_items(
                [
                    {
                        "source_name": "a_test",
                        "js_dependencies": ["some-js-package"],
                    }
                ]
            )
            raise Exception()

    assert make_build_config().config == {
        "version": idom.__version__,
        "by_source": {},
    }


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


def test_build_config_get_js_dependency_alias(make_build_config):
    config = make_build_config(
        {"source_name": "module_1", "js_dependencies": ["dep1", "dep2"]},
        {"source_name": "module_2", "js_dependencies": ["dep2", "dep3"]},
    )
    assert config.get_js_dependency_alias("module_1", "dep1") == "dep1-module_1-5001a4b"
    assert config.get_js_dependency_alias("module_1", "dep2") == "dep2-module_1-5001a4b"
    assert config.get_js_dependency_alias("module_2", "dep2") == "dep2-module_2-46d6db8"
    assert config.get_js_dependency_alias("module_2", "dep3") == "dep3-module_2-46d6db8"


def test_build_config_all_aliased_js_dependencies(make_build_config):
    config = make_build_config(
        {"source_name": "module_1", "js_dependencies": ["dep1", "dep2"]},
        {"source_name": "module_2", "js_dependencies": ["dep2", "dep3"]},
    )
    assert config.all_aliased_js_dependencies() == [
        "dep1-module_1-5001a4b@npm:dep1",
        "dep2-module_1-5001a4b@npm:dep2",
        "dep2-module_2-46d6db8@npm:dep2",
        "dep3-module_2-46d6db8@npm:dep3",
    ]


def test_build_config_all_js_dependency_aliases(make_build_config):
    config = make_build_config(
        {"source_name": "module_1", "js_dependencies": ["dep1", "dep2"]},
        {"source_name": "module_2", "js_dependencies": ["dep2", "dep3"]},
    )
    assert config.all_js_dependency_aliases() == [
        "dep1-module_1-5001a4b",
        "dep2-module_1-5001a4b",
        "dep2-module_2-46d6db8",
        "dep3-module_2-46d6db8",
    ]
