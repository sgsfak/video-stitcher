import re
import datetime
import time
import pathlib
import asyncio


def read_dir(dir, max_age_hours):
    """A generator that finds the files in the given dir that have a
     filename with a timestamp older than the `max_age_hours` in the past"""
    min_ts = (time.time() - max_age_hours*60*60)*1000
    p = pathlib.Path(dir)
    pat = r'(?P<ts>\d+).mp4'
    for f in p.glob("*.mp4"):
        m = re.search(pat, f.name)
        if not m:
            continue
        ts = int(m.groupdict()['ts'])
        if ts < min_ts:
            yield f


def reap_stitched(dir, max_age_hours):
    """Removes the files in the given dir that have a
     filename with a timestamp older than the `max_age_hours` in the past"""
    k = 0
    for f in read_dir(dir, max_age_hours):
        f.unlink()
        k += 1
    return k


async def reaper_coro(dir, max_age_hours):
    sleep_time = 1 * 60 * 60 # 1 hour
    while True:
        k = reap_stitched(dir, max_age_hours)
        print(f"Reaper woke up and deleted {k} files...")
        await asyncio.sleep(sleep_time)





