from .constants import BACKUP_DIR_PATTERN


def is_backup_dir(dir_name: str) -> bool:
    """
    Test if a directory name fits the pattern of backup folder names.

    The pattern is YYYY-MM-DD-suffix, where suffix is either 'daily' or 'weekly'.
    """
    if BACKUP_DIR_PATTERN.match(dir_name):
        return True
    return False
