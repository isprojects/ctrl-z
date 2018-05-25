import logging

import yaml

from .retention import RetentionPolicy

logger = logging.getLogger(__name__)


class Config:
    __slots__ = [
        'restore',
        'base_dir',
        'logging',
        'database',
        'retention_policy',
        'report',
        'files',
        'pg_dump_binary',
        'pg_restore_binary',
    ]

    def __init__(self, **kwargs):
        self.restore = kwargs.pop('restore', False)

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.retention_policy = RetentionPolicy(**self.retention_policy)
        self.set_base_dir()

    def __repr__(self):
        params = [
            "%s=%r" % (slot, getattr(self, slot))
            for slot in self.__slots__
        ]
        return "Config(%s)" % " ".join(params)

    @classmethod
    def from_file(cls, config_file: str, **overrides):
        logger.debug("Loading config from %s", config_file)
        logger.debug("Applying config overrides: %r", overrides)
        with open(config_file, 'r') as _config:
            config = yaml.safe_load(_config)
        config.update(overrides)
        return cls(**config)

    def set_base_dir(self):
        if self.restore:  # should be set via overrides
            return

        self.base_dir = self.retention_policy.get_base_dir(self.base_dir)
