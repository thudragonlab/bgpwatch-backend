import time
from src import app
from datetime import datetime, timedelta, timezone

timeFormat = "%Y-%m-%d %H:%M:%S"
utc = timezone(timedelta(hours=0))
bj = timezone(timedelta(hours=8))


def local_time_offset(t=None):
    """Return offset of local zone from GMT, either at present or at time t."""
    # python2.3 localtime() can't take None
    if t is None:
        t = time.time()
    if time.localtime(t).tm_isdst and time.daylight:
        return -time.altzone
    else:
        return -time.timezone


def time_formatting(time_str):
    time_array = time.strptime(time_str, timeFormat)
    time_stamp = int(time.mktime(time_array)) * 1000
    return time_stamp


def transfer_time_to_datetime(start, end, tz_offset):
    tz_offset = int(tz_offset)
    return datetime.utcfromtimestamp(((int(end) - tz_offset * 60000) / 1000)), datetime.utcfromtimestamp(
        ((int(start) - tz_offset * 60000) / 1000))


def generate_time_period(end_time, start_time):
    if start_time is None or end_time is None:
        start_time = time_formatting(datetime.now().strftime(timeFormat))
        end_time = time_formatting((datetime.now() - timedelta(days=3)).strftime(timeFormat))
    start = start_time
    end = end_time
    return end, start
