from sanic import Sanic
from sanic.response import json, text
import sanic.response
from stitch_vids import stitch, read_vid_fns, locate
import pathlib
import tempfile
import os

VID_SEGMENT_DIR = '/home/mped/ubuntu_dev/xvlepsis_streaming/ffmpeg_save_segments'

app = Sanic(name="Video Stither")


@app.route('/stitcher/<ts:int>')
async def server_stitch(request, ts):
    ts = int(ts/1000)  # make it seconds
    files = read_vid_fns(VID_SEGMENT_DIR)
    lst = locate(ts, files, period_mins=2)
    ## Create the output file:
    fd, outfn = tempfile.mkstemp(".mp4", prefix="stitcher-out-", dir="/tmp")
    os.close(fd)
    output = await stitch(lst, output)
    # p = pathlib.Path(outfn)
    print("MP4 to send " + output)
    return await response.file_stream(output)


if __name__ == "__main__":
    app.run(host='localhost', port=9696, debug=True)
