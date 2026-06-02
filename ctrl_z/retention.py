import logging
import os
import re
import shutil
from datetime import date, datetime, timezone
from itertools import chain
from typing import Union

from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, WEEKLY, rrule

logger = logging.getLogger(__name__)


class RetentionPolicy:
    __slots__ = ["day_of_week", "days_to_keep", "weeks_to_keep"]

    DATE_FORMAT = "%Y-%m-%d-%H-%M-%S"

    BACKUP_DIR_PATTERN = re.compile(r"^20.*-(daily|weekly)$")

    def __init__(self, **config):
        for key, value in config.items():
            setattr(self, key, value)

    def serialize(self):
        return {key: getattr(self, key) for key in self.__slots__}

    def is_backup_dir(self, dir_name: str) -> bool:
        """
        Test if a directory name fits the pattern of backup folder names.

        The pattern is YYYY-MM-DD-suffix, where suffix is either 'daily' or 'weekly'.
        """
        if self.BACKUP_DIR_PATTERN.match(dir_name):
            return True
        return False

    def get_suffix(self, dt: Union[date, datetime]) -> str:
        return "weekly" if dt.weekday() == self.day_of_week else "daily"

    def get_base_dir(self, base: str) -> str:
        """
        Figure out the folder name for the current backup.

        :param str base: the base directory where all the date-stamped backups
            are kept.
        """
        now = datetime.now(timezone.utc)
        datestamp = now.strftime(self.DATE_FORMAT)
        suffix = self.get_suffix(now)
        return os.path.join(base, f"{datestamp}-{suffix}")

    def rotate(self, base: str) -> None:
        """
        Perform the backup rotation according to the policy.

        :param str base: the base directory where all the date-stamped backups are kept.
        """
        # figure out which dailies and weeklies to keep
        now = datetime.now(timezone.utc)

        # one less day, since we're generating 'today'
        daily_start = now - relativedelta(days=self.days_to_keep - 1)
        dailies = rrule(DAILY, dtstart=daily_start, count=self.days_to_keep)

        days_since_day_of_week = now.weekday() - self.day_of_week
        weekly_start = now - relativedelta(weeks=self.weeks_to_keep - 1, days=days_since_day_of_week)
        weeklies = rrule(WEEKLY, dtstart=weekly_start, count=self.weeks_to_keep)

        # Format with "date only" -> backwards compatibility
        to_keep = sorted({f"{dt.strftime(self.DATE_FORMAT[:8])}" for dt in chain(dailies, weeklies)})
        logger.info(f"Keeping backups from: {to_keep}")

        to_delete = []
        for dir_name in os.listdir(base):
            if not self.is_backup_dir(dir_name):
                logger.info(f"{dir_name} doesn't look like a backup directory, keeping it.")
                continue

            if dir_name[:10] in to_keep:
                logger.info(f"{dir_name} falls within the retention policy, keeping it")
                continue

            to_delete.append(os.path.join(base, dir_name))

        for path in to_delete:
            if os.path.isdir(path):
                logger.info(f"Pruning backup directory {path}")
                shutil.rmtree(path, True)
