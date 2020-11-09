#!/usr/bin/env python2

import os
import sys
import subprocess
from constants import EXE_HG


def test_hg_found():
    hg_exe_full_path = EXE_HG()
    assert os.path.isfile(hg_exe_full_path)
    assert os.path.exists(hg_exe_full_path)
    file_str = subprocess.check_output(['file', hg_exe_full_path])
    assert 'executable' in file_str
