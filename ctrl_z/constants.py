import re

DATE_FORMAT = "%Y-%m-%d"

BACKUP_DIR_PATTERN = re.compile(r'^2[0-9]{3}-[0-1][0-9]-[0-3][0-9]-(daily|weekly)')
