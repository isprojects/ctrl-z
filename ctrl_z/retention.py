import logging
import os
import shutil
from datetime import date, datetime
from itertools import chain
from typing import Union

from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, WEEKLY, rrule

from .constants import DATE_FORMAT
from .utils import is_backup_dir

logger = logging.getLogger(__name__)


class RetentionPolicy:
    __slots__ = ['day_of_week', 'days_to_keep', 'weeks_to_keep']

    def __init__(self, **config):
        for key, value in config.items():
            setattr(self, key, value)

    def serialize(self):
        return {key: getattr(self, key) for key in self.__slots__}

    def get_suffix(self, dt: Union[date, datetime]) -> str:
        return 'weekly' if dt.weekday() == self.day_of_week else 'daily'

    def get_base_dir(self, base: str) -> str:
        """
        Figure out the folder name for the current backup.
        """
        now = datetime.utcnow()
        datestamp = now.strftime(DATE_FORMAT)
        suffix = self.get_suffix(now)
        return os.path.join(base, f"{datestamp}-{suffix}")

    def rotate(self, base: str):
        """
        Perform the backup rotation according to the policy.

        :param base: the base directory where all the date-stamped backups
          are kept.
        """
        # figure out which dailies to keep
        now = datetime.utcnow()

        # one less day, since we're generating 'today'
        daily_start = now - relativedelta(days=self.days_to_keep - 1)
        dailies = rrule(DAILY, dtstart=daily_start, count=self.days_to_keep)

        days_since_day_of_week = now.weekday() - self.day_of_week
        weekly_start = now - relativedelta(weeks=self.weeks_to_keep - 1, days=days_since_day_of_week)
        weeklies = rrule(WEEKLY, dtstart=weekly_start, count=self.weeks_to_keep)

        to_keep = sorted({
            "{}-{}".format(dt.strftime(DATE_FORMAT), self.get_suffix(dt))
            for dt in chain(dailies, weeklies)
        })
        logger.debug("Keeping backups from: %r", to_keep)

        to_delete = []
        for dir_name in os.listdir(base):
            if not is_backup_dir(dir_name):
                logger.debug("%s doesn't look like a backup directory, keeping it.", dir_name)
                continue

            if dir_name in to_keep:
                logger.debug("%s falls within the retention policy, keeping it", dir_name)
                continue

            to_delete.append(os.path.join(base, dir_name))

        for path in to_delete:
            logger.info("Pruning backup directory %s", path)
            shutil.rmtree(path)
