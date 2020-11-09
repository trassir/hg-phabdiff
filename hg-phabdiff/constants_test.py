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
    if sys.platform == 'win32':
        assert 'PE32 executable (console) Intel 80386, for MS Windows' in file_str
    else:
        assert 'ASCII text executable' in file_str
