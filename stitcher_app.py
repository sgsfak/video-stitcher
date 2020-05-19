from bottle import route, run, static_file
from stitch_vids import stitch, read_vid_fns, locate
import pathlib
@route('/stitcher/<ts:int>')
def server_stitch(ts):
    ts = int(ts/1000) # make it seconds
    dir = '/home/mped/ubuntu_dev/xvlepsis_streaming/ffmpeg_save_segments'
    files = read_vid_fns(dir)
    lst = locate(ts, files, period_mins=2)
    outfn = stitch(lst)
    p = pathlib.Path(outfn)
    print("MP4 to send " + outfn)
    return static_file(p.name, root=p.parent)

run(host='localhost', port=9696, debug=True)