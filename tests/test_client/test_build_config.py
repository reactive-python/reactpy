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


def test_build_config_file_load_absent_config(tmp_path):
    assert BuildConfig(tmp_path).config == {
        "version": idom.__version__,
        "by_source": {},
    }


def test_build_config_file_repr(tmp_path):
    with BuildConfig(tmp_path).transaction() as config_file:
        config_file.update_config_items(
            [{"source_name": "a_test", "js_dependencies": ["a-different-package"]}]
        )

        assert str(config_file) == f"BuildConfig({config_file.config})"


def test_build_config_file_add_config_item(tmp_path):
    with BuildConfig(tmp_path).transaction() as config_file:
        config_file.update_config_items(
            [{"source_name": "a_test", "js_dependencies": ["some-js-package"]}]
        )

    assert BuildConfig(tmp_path).config["by_source"] == {
        "a_test": {"source_name": "a_test", "js_dependencies": ["some-js-package"]}
    }


@pytest.mark.parametrize("method", ["update_config_items"])
def test_some_build_config_file_methods_require_transaction(tmp_path, method):
    config_file = BuildConfig(tmp_path)
    with pytest.raises(
        RuntimeError,
        match="Cannot modify BuildConfig without transaction",
    ):
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


def test_build_config_file_transaction_rollback(tmp_path):
    with pytest.raises(Exception):
        with BuildConfig(tmp_path).transaction() as config_file:
            config_file.update_config_items(
                [
                    {
                        "source_name": "a_test",
                        "js_dependencies": ["some-js-package"],
                    }
                ]
            )
            raise Exception()

    assert BuildConfig(tmp_path).config == {
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
