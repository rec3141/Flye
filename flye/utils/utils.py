#(c) 2013-2016 by Authors
#This file is a part of ABruijn program.
#Released under the BSD license (see LICENSE file)

from __future__ import absolute_import
import os
import re
import signal
import subprocess
import multiprocessing
import logging


logger = logging.getLogger()


def resolve_samtools(min_version=(1, 10)):
    """Prefer a samtools on PATH over the vendored one, when it is new enough.

    Flye vendors samtools 1.9 (lib/samtools-1.9), which predates
    `sort --write-index`, so a sorted BAM has to be indexed in a second pass.
    On a 1.18M-contig metagenome that pass took 5h53m at the hardcoded -@ 4 --
    about half the wall-clock of polishing, and far longer than the 52 min the
    alignment itself needed.

    Environments that ship a newer samtools (danaSeq pins >=1.17 in its flye
    env) can index during sorting instead. Falls back to the vendored binary
    when PATH has nothing suitable, so a plain `make`-built Flye still works.
    """
    for cand in ("samtools", "flye-samtools"):
        if not which(cand):
            continue
        try:
            out = subprocess.check_output([cand, "--version"],
                                          stderr=subprocess.DEVNULL).decode()
            nums = re.findall(r"\d+", out.splitlines()[0])
            if tuple(int(x) for x in nums[:2]) >= min_version:
                return cand
        except (subprocess.CalledProcessError, OSError, IndexError, ValueError):
            continue
    return "flye-samtools"


def which(program):
    """
    Mimics UNIX "which" command
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def process_in_parallel(function, arguments, num_proc):
    """
    Run given function in parallel using multithreading
    """
    #making sure the main process catches SIGINT
    threads = []
    orig_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
    for _ in range(num_proc):
        threads.append(multiprocessing.Process(target=function, args=arguments))
    signal.signal(signal.SIGINT, orig_sigint)

    for t in threads:
        t.start()
    try:
        for t in threads:
            t.join()
            if t.exitcode == -9:
                logger.error("Looks like the system ran out of memory")
            if t.exitcode != 0:
                raise Exception("One of the processes exited with code: {0}"
                                .format(t.exitcode))
    except KeyboardInterrupt:
        for t in threads:
            t.terminate()
        raise


def get_median(lst):
    if not lst:
        raise ValueError("_get_median() arg is an empty sequence")
    sorted_list = sorted(lst)
    if len(lst) % 2 == 1:
        return sorted_list[len(lst) // 2]
    else:
        mid1 = sorted_list[(len(lst) // 2) - 1]
        mid2 = sorted_list[(len(lst) // 2)]
        return (mid1 + mid2) / 2
