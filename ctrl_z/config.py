import logging
import os

import yaml

from .retention import RetentionPolicy

logger = logging.getLogger(__name__)


DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.default.yml")


class Config:
    __slots__ = [
        "restore",
        "base_dir",
        "logging",
        "database",
        "retention_policy",
        "report",
        "files",
        "pg_dump_binary",
        "pg_restore_binary",
        "dropdb_binary",
        "createdb_binary",
    ]

    def __init__(self, **kwargs):
        self.restore = kwargs.pop("restore", False)

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.retention_policy = RetentionPolicy(**self.retention_policy)
        self.set_base_dir()

    def __repr__(self):
        params = ["%s=%r" % (slot, getattr(self, slot)) for slot in self.__slots__]
        return "Config(%s)" % " ".join(params)

    @classmethod
    def from_file(cls, config_file: str, **overrides):
        logger.debug("Loading config from %s", config_file)
        logger.debug("Applying config overrides: %r", overrides)
        with open(config_file, "r") as _config:
            config = yaml.safe_load(_config)
        config.update(overrides)
        return cls(**config)

    def write_to(self, path: str):
        as_dict = {key: getattr(self, key) for key in self.__slots__}
        if not self.restore:
            as_dict["base_dir"] = os.path.dirname(as_dict["base_dir"])
        as_dict["retention_policy"] = as_dict["retention_policy"].serialize()
        with open(path, "w") as stream:
            yaml.dump(as_dict, stream=stream)

    def set_base_dir(self):
        if self.restore:  # should be set via overrides
            return

        self.base_dir = self.retention_policy.get_base_dir(self.base_dir)
