from pathlib import Path
from typing import Text, Any, List

import pytest

from security_notifier.config import Config, ClashingFieldException


def check_nested_item(cfg: Config, keys: List[Text], expected_value: Any):
    ptr = cfg._data
    for i in keys:
        ptr = ptr[i]
    assert ptr == expected_value, "Leaf has not been set to the correct value"


def test_config_file_doesnt_exist(tmp_path: Path):
    cfg_file = tmp_path / "test_config.toml"
    assert not Path(cfg_file).is_file(), "Temporary file should not yet exist"
    Config.instance(cfg_file)
    assert Path(cfg_file).is_file(), "Temporary file should now exist"
    file_contents = Path(cfg_file).read_text()
    assert file_contents == "", "File contents should be empty"


@pytest.mark.parametrize(
    "key, value, expected_content",
    (
            (
                    "string_field",
                    "a string that will be stored in the file",
                    'string_field = "a string that will be stored in the file"'
            ),
            (
                    "int_field",
                    5,
                    'int_field = 5'
            ),
    )
)
def test_set_new_field(tmp_path: Path, key: Text, value: Any, expected_content: Text):
    cfg_file = tmp_path / "test_config.toml"
    cfg = Config.instance(cfg_file)

    file_contents = Path(cfg_file).read_text()
    assert file_contents == "", "File contents should be empty"

    cfg.set(key, value)
    file_contents = Path(cfg_file).read_text()
    assert file_contents.strip() == expected_content


@pytest.mark.parametrize(
    "key, value, expected_nesting",
    (
            (
                    "string_field",
                    "a string that will be stored in the file",
                    ["string_field"]
            ),
            (
                    "container.inner.int_field",
                    5,
                    ["container", "inner", "int_field"]
            ),
            (
                    "container.string_field",
                    "a string that will be stored in the file",
                    ["container", "string_field"]
            ),
            (
                    "container.inner.int_field",
                    5,
                    ["container", "inner", "int_field"]
            ),
    )
)
def test_set_nested_field(tmp_path: Path, key: Text, value: Any, expected_nesting: List[Text]):
    cfg_file = tmp_path / "test_config.toml"
    cfg = Config.instance(cfg_file)

    file_contents = Path(cfg_file).read_text()
    assert file_contents == "", "File contents should be empty"

    cfg.set(key, value)

    # Test setter is correct
    check_nested_item(cfg, expected_nesting, value)

    # Test serialisation / deserialisation - when setting, the file will have been saved. If we create a new config
    # object from the same file, it should pass the nested item test.
    new_cfg = Config(cfg_file)
    check_nested_item(new_cfg, expected_nesting, value)


def test_set_clashing_nested_field(tmp_path: Path):
    cfg_file = tmp_path / "test_config.toml"
    cfg = Config.instance(cfg_file)

    file_contents = Path(cfg_file).read_text()
    assert file_contents == "", "File contents should be empty"

    cfg.set("container.inner", 7)
    assert cfg._data["container"]["inner"] == 7, "Initial set has failed"

    with pytest.raises(ClashingFieldException):
        cfg.set("container.inner.inner2", 7)

    assert cfg._data["container"]["inner"] == 7, "Overwrite set has corrupted the config"

    cfg.set("container.inner.inner2", 7, force=True)
    assert cfg._data["container"]["inner"]["inner2"] == 7, "Forced overwrite set has failed"

    new_cfg = Config(cfg_file)
    check_nested_item(new_cfg, ["container", "inner", "inner2"], 7)


def test_get_nested_item(tmp_path: Path):
    _test_list = ["a", "b", "c"]
    _test_dict = {
        "a": 0,
        "b": 1,
        "c": 2
    }

    cfg_file = tmp_path / "test_config.toml"
    cfg = Config.instance(cfg_file)
    cfg._data = {
        "container": {
            "inner_list": _test_list,
            "inner_nested": _test_dict
        },
        "top_level": 4
    }
    cfg.save()

    # Test top level getter access
    assert cfg.get("top_level") == 4, "Top level value was incorrect"

    # Now test list retrieval
    retrieved_list = cfg.get("container.inner_list")
    assert isinstance(retrieved_list, list), "Failed to retrieve the list"
    assert len(retrieved_list) == len(_test_list), "List is the wrong length"
    assert all([x == y for x, y in zip(retrieved_list, _test_list)]), "Not all list values matched"

    # Test nested dicts in the config
    retrieved_dict = cfg.get('container.inner_nested')
    assert all([k in retrieved_dict for k in _test_dict]), "Nested dict keys differed"
    assert all([retrieved_dict[k] == v for k, v in _test_dict.items()]), "Nested dict values differed"

    with pytest.raises(KeyError):
        cfg.get("This key doesn't exist")

    assert cfg.get("This key doesn't exist", default_val=42) == 42

