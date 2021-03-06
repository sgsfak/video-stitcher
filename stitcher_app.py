from sanic import Sanic
from sanic.response import text, empty
import sanic.response
from sanic_cors import CORS
from stitch_vids import stitch, read_vid_fns, locate
import cron_stitcher
from cron_stitcher import locate_and_stitch
import pathlib
import tempfile
import os
import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
import reaper
import shlex
import json


VID_SEGMENT_DIR = '/recorded_video'
VID_OUT_DIR = '/var/www/html/stitcher'


app = Sanic(name="Video Stitcher")
CORS(app)

@app.route('/stitcher/<t:int>', methods=['GET', 'OPTIONS'])
async def server_stitch(request, t):
    period_mins=int(request.args.get('w', 2))
    fname = f"{t}.mp4"
    ## if period_mins>2:
    ##     fname = f"{t}-{period_mins}.mp4"
    real_file = pathlib.Path(VID_OUT_DIR).joinpath(fname)
    if not real_file.exists():
        files = read_vid_fns(VID_SEGMENT_DIR)
        output = await locate_and_stitch(t, files, period_mins=period_mins)
        #ts = int(t/1000)  # make it seconds
        #lst = locate(ts, files, period_mins=2)
        ## Create the output file:
        #fd, outfn = tempfile.mkstemp(".mp4", prefix="stitcher-out-", dir="/tmp")
        #os.close(fd)
        #output = await stitch(lst, output)
        # p = pathlib.Path(outfn)
    #return await response.file_stream(output)
    uri = '/stitched/' + fname
    print(f"MP4 to send {real_file} through {uri}" )
    return empty(headers={'x-accel-redirect': uri})



async def _probe(fname):
    cmd = f"ffprobe -v quiet -print_format json -show_format -show_streams {shlex.quote(fname)}"
    proc = await asyncio.create_subprocess_shell(cmd,
                                                 stdout=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    if proc.returncode == 0:
        return json.loads(out)
    return {}



@app.route('/stitcher/info/<t:int>', methods=['GET', 'OPTIONS'])
async def server_stitch_info(request, t):
    fname = f"{t}.mp4"
    real_file = pathlib.Path(VID_OUT_DIR).joinpath(fname)
    info = {'exists': False}
    if real_file.exists():
        info = await _probe(str(real_file))
        info['exists'] = True
    return sanic.response.json(info)



if __name__ == "__main__":
    app.add_task(cron_stitcher.main())
    app.add_task(reaper.reaper_coro(VID_OUT_DIR, 7*24))
    app.run(host='localhost', port=8686, debug=True)
