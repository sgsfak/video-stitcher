import redis
import time
from datetime import datetime
import pathlib
from stitch_vids import stitch, read_vid_fns, locate
import asyncio
import json

STREAMS=['critical.apnea', 'critical.vomit', 'critical.fever', 
         'critical.heartrate', 'critical.febrileconvulsions']


def wait_for_events(r, state=None, block=1000, count=20):
    if state is None:
        ## Going back to maximum 30 hours in the past
        mint = int((time.time() - 30*3600)*1000)
        state = {s: mint for s in STREAMS}
    data = r.xread(state, count=count, block=block)
    new_state = state.copy()
    event_ids = set()
    for stream, events in data:
        for key, evt in events:
            t = int(evt['t'])
            new_state[stream] = key
            # ts = int(t/1000)  # make it seconds
            event_ids.add(t)
    return (new_state, event_ids)



VID_SEGMENT_DIR = '/recorded_video'
VID_OUT_DIR = '/var/www/html/stitcher'

async def locate_and_stitch(t:int, files, period_mins=2):
    ts = int(t/1000)
    lst = locate(ts, files, period_mins=period_mins)
    p = pathlib.Path(f"{VID_OUT_DIR}/{t}.mp4")
    output = await stitch(lst, str(p))
    print(f"Wrote {output}!")
    return output

async def main():
    r = redis.Redis(decode_responses=True)
    period_mins = 2
    old_state = None
    p = pathlib.Path("stitcher_state.json")
    if p.exists():
        with open(p) as f:
            old_state = json.load(f)
    while True:
        state, event_ids = wait_for_events(r, old_state, block=60000)
        if len(event_ids) == 0:
            print("No new critical events returned by Redis..")
            continue
        past_time = time.time()*1000 - max(event_ids)
        if past_time > 10*60*1000: # 10 minutes in the past
            files = read_vid_fns(VID_SEGMENT_DIR)
            await asyncio.gather(*[locate_and_stitch(t, files, period_mins) for t in event_ids])
            old_state = state
            with open(p, 'w') as f:
                json.dump(state, f)
            print(f"Stitched {len(event_ids)} videos...state={old_state}")
        else:
            asyncio.sleep(period_mins*60)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())