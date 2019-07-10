"""
Test that the backup retention policy is correctly implemented.
"""
from ctrl_z.retention import RetentionPolicy


def test_rotation(tmpdir, freezer):
    freezer.move_to("2018-06-27")  # it's Wednesday
    base = tmpdir.mkdir("backups")
    base.mkdir("2018-06-24-daily")  # should be gone
    base.mkdir("2018-06-25-weekly")  # should be gone
    base.mkdir("2018-06-26-daily")  # should be kept
    policy = RetentionPolicy(day_of_week=0, days_to_keep=2, weeks_to_keep=0)

    policy.rotate(base=str(base))

    remaining = [local.basename for local in base.listdir()]
    assert remaining == ["2018-06-26-daily"]


def test_gaps(tmpdir, freezer):
    freezer.move_to("2018-06-26")  # it's Tuesday
    base = tmpdir.mkdir("backups")
    base.mkdir("2018-06-11-weekly")
    base.mkdir("2018-06-12-daily")
    base.mkdir("2018-06-13-daily")
    base.mkdir("2018-06-14-daily")
    base.mkdir("2018-06-15-daily")
    base.mkdir("2018-06-16-daily")
    # 17 & 18 missing - daily & weekly
    base.mkdir("2018-06-19-daily")
    base.mkdir("2018-06-20-daily")
    base.mkdir("2018-06-21-daily")
    base.mkdir("2018-06-22-daily")
    base.mkdir("2018-06-23-daily")
    base.mkdir("2018-06-24-daily")
    base.mkdir("2018-06-25-weekly")
    # should keep everything from (including) 2018-06-18-daily
    policy = RetentionPolicy(day_of_week=0, days_to_keep=9, weeks_to_keep=1)

    policy.rotate(base=str(base))

    remaining = sorted([local.basename for local in base.listdir()])
    assert remaining == [
        "2018-06-19-daily",
        "2018-06-20-daily",
        "2018-06-21-daily",
        "2018-06-22-daily",
        "2018-06-23-daily",
        "2018-06-24-daily",
        "2018-06-25-weekly",
    ]


def test_do_not_touch_other_directories(tmpdir, freezer):
    """
    Only folders that look like backup dirs may be rotated.
    """
    freezer.move_to("2018-06-26")  # it's Tuesday
    base = tmpdir.mkdir("backups")
    # keep these
    base.mkdir("no-touchy")
    base.mkdir("2018-01-01")
    base.mkdir("2018-01-01-yearly")

    # delete these
    base.mkdir("2018-01-01-daily")
    base.mkdir("2018-01-01-weekly")
    policy = RetentionPolicy(day_of_week=0, days_to_keep=7, weeks_to_keep=4)

    policy.rotate(base=str(base))

    remaining = sorted([local.basename for local in base.listdir()])
    assert remaining == ["2018-01-01", "2018-01-01-yearly", "no-touchy"]
