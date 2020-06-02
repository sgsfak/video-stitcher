from sanic import Sanic
from sanic.response import json, text
import sanic.response
from sanic_cors import CORS
from stitch_vids import stitch, read_vid_fns, locate
from cron_stitcher import locate_and_stitch
import pathlib
import tempfile
import os

VID_SEGMENT_DIR = '/recorded_video'
VID_OUT_DIR = '/var/www/html/stitcher'


app = Sanic(name="Video Stither")
CORS(app)

@app.route('/stitcher/<t:int>', methods=['GET', 'OPTIONS'])
async def server_stitch(request, t):
    period_mins=int(request.args.get('w', 2))
    fname = f"{t}.mp4"
    if period_mins>2:
        fname = f"{t}-{period_mins}.mp4"
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
        print("MP4 to send " + output)
    #return await response.file_stream(output)
    return response.empty(headers={'x-accel-redirect': '/stitched/'+fname})


if __name__ == "__main__":
    app.run(host='localhost', port=9696, debug=True)
