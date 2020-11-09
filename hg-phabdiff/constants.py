#!/usr/bin/env python2

import os
import sys
import subprocess

def ENVVAR_PHAB_DIFF():
    return "HG_PHAB_DIFF"


def EXE_HG():
    if sys.platform == "win32":
        hg_name = "\\hg.exe"
    else:
        hg_name  = "/hg"
    # importing pip is not supported by devs, they recommend this instead
    mercurial_files = subprocess.check_output([sys.executable, '-m', 'pip', 'show', '-f', 'mercurial']).splitlines()
    module_location = filter(lambda x: x.startswith('Location: '), mercurial_files)[0].split(': ')[1].strip()
    hg_path = filter(lambda x: x.endswith(hg_name), mercurial_files)[0].strip()
    print(module_location)
    print(hg_path)
    return os.path.abspath(os.path.join(module_location, hg_path))
