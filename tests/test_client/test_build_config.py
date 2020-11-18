from pathlib import Path

import pytest

from idom.client.build_config import (
    BuildConfigItem,
    BuildConfigFile,
    to_build_config_item,
    find_build_config_item_in_python_file,
    find_python_packages_build_config_items,
)


def test_to_build_config_item():
    config = BuildConfigItem(source_name="a_test", js_dependencies=["some-js-package"])
    assert to_build_config_item(config) is config

    assert to_build_config_item(config.to_dict()) == config

    with pytest.raises(ValueError, match="Expected a BuildConfigItem or dict"):
        to_build_config_item("not-a-build-config")


@pytest.mark.parametrize(
    "value, error_message",
    [
        (
            {"source_name": None, "js_dependencies": []},
            "must be a string",
        ),
        (
            {"source_name": "some_module", "js_dependencies": None},
            "must be a list",
        ),
        (
            {"source_name": "some_module", "js_dependencies": [None]},
            r"items of .*? must be strings",
        ),
        (
            "not-a-dict",
            "Expected build config to be a dict",
        ),
    ],
)
def test_build_config_validate_bad_values(value, error_message):
    with pytest.raises(ValueError, match=error_message):
        BuildConfigItem.from_dict(value)


def test_build_config_item_idenfitier():
    assert (
        BuildConfigItem(
            source_name="some_module", js_dependencies=["d", "e", "f"]
        ).js_dependency_alias_suffix
        == "some_module-465887b"
    )


def test_build_config_item_aliased_js_dependencies():
    assert BuildConfigItem(
        source_name="some_module", js_dependencies=["dep1", "dep2"]
    ).js_dependencies == [
        "dep1-some_module-261bad9@npm:dep1",
        "dep2-some_module-261bad9@npm:dep2",
    ]


def test_find_build_config_item_in_python_file(tmp_path):
    py_module_path = tmp_path / "a_test.py"
    with py_module_path.open("w") as f:
        f.write("idom_build_config = {'js_dependencies': ['some-js-package']}")
    actual_config = find_build_config_item_in_python_file("a_test", py_module_path)
    expected_config = BuildConfigItem(
        source_name="a_test", js_dependencies=["some-js-package"]
    )
    assert actual_config == expected_config


def test_build_config_file_load_absent_config(tmp_path):
    assert BuildConfigFile(tmp_path).configs == {}


def test_build_config_file_repr(tmp_path):
    with BuildConfigFile(tmp_path).transaction() as config_file:
        config_file.add(
            [{"source_name": "a_test", "js_dependencies": ["a-different-package"]}]
        )

        assert str(config_file) == f"BuildConfigFile({config_file.to_dicts()})"


def test_build_config_file_add_config_item(tmp_path):
    with BuildConfigFile(tmp_path).transaction() as config_file:
        config_file.add(
            [{"source_name": "a_test", "js_dependencies": ["a-different-package"]}]
        )
        with pytest.raises(ValueError, match="already exists"):
            config_file.add(
                [{"source_name": "a_test", "js_dependencies": ["some-js-package"]}],
                ignore_existing=False,
            )
        config_file.add(
            [{"source_name": "a_test", "js_dependencies": ["some-js-package"]}],
            ignore_existing=True,
        )

    with BuildConfigFile(tmp_path).transaction() as config_file:
        ...

    assert BuildConfigFile(tmp_path).configs == {
        "a_test": BuildConfigItem(
            source_name="a_test", js_dependencies=["some-js-package"]
        )
    }


def test_build_config_file_remove_config_item(tmp_path):
    with BuildConfigFile(tmp_path).transaction() as config_file:
        config_file.add(
            [
                {
                    "source_name": "first_test",
                    "js_dependencies": ["first-js-package"],
                },
                {
                    "source_name": "second_test",
                    "js_dependencies": ["second-js-package"],
                },
            ]
        )

    with BuildConfigFile(tmp_path).transaction() as config_file:
        config_file.remove("first_test")
        config_file.remove("does_not_exist", ignore_missing=True)

    assert BuildConfigFile(tmp_path).configs == {
        "second_test": BuildConfigItem(
            source_name="second_test",
            js_dependencies=["second-js-package"],
        )
    }


def test_build_config_files_to_dicts(tmp_path):
    with BuildConfigFile(tmp_path).transaction() as config_file:
        config_file.add(
            [
                {
                    "source_name": "first_test",
                    "js_dependencies": ["first-js-package"],
                },
                {
                    "source_name": "second_test",
                    "js_dependencies": ["second-js-package"],
                },
            ]
        )

    assert BuildConfigFile(tmp_path).to_dicts() == {
        "first_test": {
            "source_name": "first_test",
            "js_dependencies": ["first-js-package"],
        },
        "second_test": {
            "source_name": "second_test",
            "js_dependencies": ["second-js-package"],
        },
    }


def test_build_config_file_clear_config_item(tmp_path):
    with BuildConfigFile(tmp_path).transaction() as config_file:
        config_file.add(
            [
                {
                    "source_name": "first_test",
                    "js_dependencies": ["first-js-package"],
                },
                {
                    "source_name": "second_test",
                    "js_dependencies": ["second-js-package"],
                },
            ]
        )

    with BuildConfigFile(tmp_path).transaction() as config_file:
        config_file.clear()

    assert BuildConfigFile(tmp_path).configs == {}


@pytest.mark.parametrize("method", ["add", "remove", "clear"])
def test_some_build_config_file_methods_require_transaction(tmp_path, method):
    config_file = BuildConfigFile(tmp_path)
    with pytest.raises(
        RuntimeError,
        match="Cannot modify BuildConfigFile without transaction",
    ):
        getattr(config_file, method)()


def test_find_python_packages_build_config_items():
    mock_site_pkgs_path = str((Path(__file__).parent / "mock_site_packages").absolute())
    configs, errors = find_python_packages_build_config_items([mock_site_pkgs_path])
    assert configs == [
        BuildConfigItem(
            source_name="has_good_config", js_dependencies=["some-js-package"]
        )
    ]

    assert len(errors) == 1

    with pytest.raises(
        RuntimeError,
        match="Failed to load build config for module 'has_bad_config'",
    ):
        raise errors[0]

    with pytest.raises(
        ValueError,
        match="items of 'js_dependencies' must be strings, not 1",
    ):
        raise errors[0].__cause__


def test_build_config_file_transaction_rollback(tmp_path):
    with BuildConfigFile(tmp_path).transaction() as config_file:
        config_file.add(
            [
                {
                    "source_name": "a_test",
                    "js_dependencies": ["some-js-package"],
                }
            ]
        )

    with pytest.raises(Exception):
        with BuildConfigFile(tmp_path).transaction() as config_file:
            config_file.remove("a_test")
            raise Exception()

    assert BuildConfigFile(tmp_path).configs == {
        "a_test": BuildConfigItem(
            source_name="a_test", js_dependencies=["some-js-package"]
        )
    }


def test_build_config_item_repr():
    assert (
        str(BuildConfigItem(source_name="a_test", js_dependencies=["some-js-package"]))
        == "BuildConfigItem(source_name='a_test', js_dependencies=['some-js-package'])"
    )
