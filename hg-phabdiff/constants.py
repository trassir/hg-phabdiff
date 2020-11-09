#!/usr/bin/env python2

import os
import sys
import subprocess

def ENVVAR_PHAB_DIFF():
    return "HG_PHAB_DIFF"


def EXE_HG():
    hg_full_path = ""
    for hg_name in [os.path.sep + "hg.exe", os.path.sep + "hg"]:
        # importing pip is not supported by devs, they recommend this instead
        mercurial_files = subprocess.check_output([sys.executable, '-m', 'pip', 'show', '-f', 'mercurial']).splitlines()
        module_location = filter(lambda x: x.startswith('Location: '), mercurial_files)[0].split(': ')[1].strip()
        hg_paths = filter(lambda x, name=hg_name: x.endswith(name), mercurial_files)
        if hg_paths:
            hg_full_path = os.path.abspath(os.path.join(module_location, hg_paths[0].strip()))
            break
    return hg_full_path
