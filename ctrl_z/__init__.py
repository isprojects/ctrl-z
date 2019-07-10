from pkg_resources import get_distribution

from ._cli import cli  # noqa
from .backup import Backup, configure_logging  # noqa

__version__ = get_distribution("CTRL-Z").version

__all__ = ["Backup", "cli"]
