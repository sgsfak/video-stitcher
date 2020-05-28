from sanic import Sanic
from sanic.response import json, text
from stitch_vids import stitch, read_vid_fns, locate
import pathlib
import tempfile
import os

VID_SEGMENT_DIR = '/home/mped/ubuntu_dev/xvlepsis_streaming/ffmpeg_save_segments'

app = Sanic(name="Video Stither")


@app.route('/test/<ts:int>')
def test(request, ts):
    return text("You gave {} ({})".format(ts+1, type(ts)))


@app.route('/stitcher/<ts:int>')
async def server_stitch(ts):
    ts = int(ts/1000)  # make it seconds
    files = read_vid_fns(VID_SEGMENT_DIR)
    lst = locate(ts, files, period_mins=2)
    ## Create the output file:
    fd, outfn = tempfile.mkstemp(".mp4", prefix="stitcher-out-", dir="/tmp")
    os.close(fd)
    await stitch(lst, outfn)
    p = pathlib.Path(outfn)
    print("MP4 to send " + outfn)
    return static_file(p.name, root=p.parent)


if __name__ == "__main__":
    app.run(host='localhost', port=9696, debug=True)
