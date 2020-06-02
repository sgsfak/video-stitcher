from pathlib import Path
from datetime import datetime
import bisect
import tempfile
import shlex
import subprocess
import os
import time
import asyncio
from shutil import copyfile

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

async def _run(cmd):
    proc = await asyncio.create_subprocess_shell(cmd,
                                                 stdout=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    return (proc.returncode, out.decode('utf-8'), err.decode('utf-8'))


async def stitch(lst, output):
    files = []
    cmds = []
    temp_files = set()
    t = time.time()
    try:
        for fl, ss, to in lst:
            fname = str(fl)
            if ss == 0 and to == 0:
                files.append(fname)
                continue
            fd, tmp = tempfile.mkstemp(".mp4", prefix="stitcher-", dir="/tmp")
            os.close(fd)
            temp_files.add(tmp)
            # tmp = "%s-%s" % (prefix, fl.name)
            files.append(tmp)
            cmd = "ffmpeg -y -i {}".format(shlex.quote(fname))
            if ss > 0:
                cmd += f" -ss {ss}"
            if to > 0:
                cmd += f" -to {to}"
            cmd += " -codec copy {}".format(shlex.quote(tmp))
            cmds.append(cmd)

        results = await asyncio.gather(*[_run(cmd) for cmd in cmds])
        first_failed = next(((c, r) for c, r in zip(cmds, results) if r[0]!=0), None)
        if first_failed is not None:
            failed_cmd, info = first_failed
            raise subprocess.CalledProcessError(info[0], failed_cmd, 
                                                info[1], info[2])

        if len(files) == 1:
            #os.rename(files[0], output)
            #temp_files.remove(files[0])
            copyfile(files[0], output)
            return output

        fd, concatsf = tempfile.mkstemp(".txt", prefix="stitcher-conc-",
                                        dir="/tmp")
        temp_files.add(concatsf)
        with os.fdopen(fd, "w") as fp:
            for fn in files:
                fp.write("file '%s'\n" % (fn,))
        # safe 0: https://ffmpeg.org/ffmpeg-all.html#Options-37
        concat_cmd = "ffmpeg -y -safe 0 -f concat -i {} -codec copy {}".format(
            shlex.quote(concatsf), shlex.quote(output))
        code, out, err = await _run(concat_cmd)
        return output
    finally:
        ## Cleanup temp files:
        for f in temp_files:
            os.unlink(f)
        print(f"Stitching finished in {time.time()-t} seconds")


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
    outfn = asyncio.get_event_loop().run_until_complete(stitch(lst, "/tmp/test.mp4"))
    print("Out mp4 written in %s" % outfn)
