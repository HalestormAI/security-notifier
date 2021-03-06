from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Text, Dict, Optional, Union

import toml

from .log_helper import get_logger

logger = get_logger(__name__)

TextPath = Union[Text, Path]


class ConfigNotInitialisedException(Exception):
    pass


class ClashingFieldException(Exception):
    pass


class MissingConfigEntryException(Exception):
    pass


class InvalidNestedIndexException(Exception):
    pass


class DefaultValue:
    """We need to be able to differentiate between the user passing None as a default config value, and the user not
    providing a default value (in which case we will error about missing keys)."""

    def __init__(self, value):
        self.value = value


class Config:
    DEFAULT_CONFIG_PATH: TextPath = Path(__file__).parent.parent / "config.toml"
    LOG_LEVEL = logging.DEBUG

    _instance: Dict[TextPath, Config] = {}

    def __init__(self, file_path: TextPath):
        self._data: Optional[Dict[Text, Any]] = None
        self._file_path: TextPath = file_path

        self.load()

    def get(self, key: Text, default_val: Union[Optional[Any], DefaultValue] = DefaultValue(None)) -> Any:
        if self._data is None:
            raise ConfigNotInitialisedException("Config has not been initialised - have you called `load()`?")

        keys = key.split(".")

        try:
            ptr = self._data
            for i in keys:
                if not isinstance(ptr, dict):
                    raise InvalidNestedIndexException(f"Trying to get field {i} from config item that is not a dict.")
                ptr = ptr[i]

            return ptr
        except KeyError as err:
            if not isinstance(default_val, DefaultValue):
                return default_val
            raise MissingConfigEntryException(f"Couldn't find key {key} in config.")

    def set(self, key: Text, value: Any, force: bool = False):
        if self._data is None:
            raise ConfigNotInitialisedException("Config has not been initialised - have you called `load()`?")

        def is_leaf(idx, pieces):
            return idx == len(pieces) - 1

        ptr = self._data
        processed_keys = []
        key_pieces = key.split(".")

        for idx, p in enumerate(key_pieces):
            processed_keys.append(p)
            current_key = ".".join(processed_keys)

            if is_leaf(idx, key_pieces):
                logger.debug(f"Setting {current_key} to {value}")
                ptr[p] = value
                break

            if p in ptr and not isinstance(ptr[p], dict) and not force:
                raise ClashingFieldException(
                    f"Field '{current_key}' exists, but is a leaf-node. To overwrite it with this dict, "
                    f"use the 'force' parameter")

            elif (p in ptr and not isinstance(ptr[p], dict)) or p not in ptr:
                ptr[p] = {}

            ptr = ptr[p]

        self.save()

    def load(self):
        if not Path(self._file_path).is_file():
            logger.warning("Config file does not exist - creating an empty file.")
            self._data = {}
            self.save()
            return

        with open(self._file_path, "r") as fh:
            self._data = toml.load(fh)

    def save(self):
        if self._data is None:
            logger.warning("No data to save - has the config been loaded yet?")
            return

        with open(self._file_path, "w") as fh:
            toml.dump(self._data, fh)

    def __str__(self) -> Text:
        return str(self._data)

    def toml(self) -> Text:
        return toml.dumps(self._data)

    @staticmethod
    def instance(file_path: Optional[TextPath] = None) -> Config:
        if file_path is None:
            file_path = Config.DEFAULT_CONFIG_PATH

        if file_path not in Config._instance:
            Config._instance[file_path] = Config(file_path)

        return Config._instance[file_path]
