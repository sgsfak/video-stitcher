from pathlib import Path
from datetime import datetime
import bisect
import tempfile
import shlex
import subprocess
import os


def test_fns():
    lst = ["video-20200519-%02d%02d00.mp4" % (x, y)
           for x in range(0, 23)
           for y in range(0, 59, 5)]
    return lst


# dir = /home/mped/ubuntu_dev/xvlepsis_streaming/ffmpeg_save_segments
def read_vid_fns(dir=".", fnpat="video-*.mp4"):
    p = Path(dir)
    files = list(f.absolute() for f in p.glob(fnpat) if f.is_file())
    return files


def fn_to_dt(fn):
    # datetime.strptime('video-20200519-223001.mp4', "video-%Y%m%d-%H%M%S.mp4")
    dt = datetime.strptime(fn, "video-%Y%m%d-%H%M%S.mp4")
    return dt.timestamp()


def locate(ts, files, period_mins=5):
    #  period in seconds
    period_ms = period_mins * 60  # 5 mins
    start = ts - 0.5 * period_ms
    end = ts + 0.5 * period_ms
    dd = dict((fn_to_dt(fn.name), fn) for fn in files)
    kk = sorted(dd.keys())
    si = bisect.bisect_right(kk, start)
    # so now all(val <= ts for val in a[0:si])  and
    # all(val > ts for val in a[si:])
    si -= 1
    sj = bisect.bisect_right(kk, end)
    # so now all(val <= ts for val in a[0:sj])  and
    # all(val > ts for val in a[sj:])
    print("centering at {}, start={}, si={}, end={} sj={}".format(
          datetime.fromtimestamp(ts),
          datetime.fromtimestamp(start),
          si, datetime.fromtimestamp(end), sj))
    ret = []
    for i in range(si, sj):
        ss = 0
        to = 0
        if i == si:
            ss = int(start - kk[i])
            if ss < 1:
                ss = 0
        if i == sj - 1:
            to = int(end - kk[i])
            if to < 1:
                to = 0
        fname = dd[kk[i]]
        ret.append((fname, ss, to))
    return ret


def stitch(lst):
    files = []
    cmds = []
    for fl, ss, to in lst:
        fname = str(fl)
        if ss == 0 and to == 0:
            files.append(fname)
            continue
        fd, tmp = tempfile.mkstemp(".mp4", prefix="stitcher-", dir="/tmp")
        os.close(fd)
        # tmp = "%s-%s" % (prefix, fl.name)
        files.append(tmp)
        cmd = "ffmpeg -y -i %s" % (fname,)
        if ss > 0:
            cmd += " -ss %d" % (ss,)
        if to > 0:
            cmd += " -to %d" % (to,)
        cmd += " -codec copy %s" % (tmp,)
        cmds.append(shlex.split(cmd))
    for args in cmds:
        # Wait for command to complete
        # If the return code was not zero it raises CalledProcessError.
        subprocess.check_call(args, shell=False)

    if len(files) == 1:
        return files[0]

    fd, concatsf = tempfile.mkstemp(".txt", prefix="stitcher-conc-",
                                    dir="/tmp")
    with os.fdopen(fd, "w") as fp:
        for fn in files:
            fp.write("file '%s'\n" % (fn,))
    fd, output = tempfile.mkstemp(".mp4", prefix="stitcher-out-", dir="/tmp")
    os.close(fd)
    # safe 0: https://ffmpeg.org/ffmpeg-all.html#Options-37
    concat_cmd = ("ffmpeg -y -safe 0 -f concat -i {}"
                  " -codec copy {}").format(concatsf, output)
    subprocess.check_call(shlex.split(concat_cmd), shell=False)
    return output


def write_stdout(fn):
    import shutil
    import sys
    with open(fn, "r") as f:
        shutil.copyfileobj(f, sys.stdout)


if __name__ == "__main__":
    dir = '/home/mped/ubuntu_dev/xvlepsis_streaming/ffmpeg_save_segments'
    files = read_vid_fns(dir)
    ts = 1589833700.0
    lst = locate(ts, files, period_mins=2)
    outfn = stitch(lst)
    print("Out mp4 written in %s" % outfn)
