import os
import subprocess
from hg_phabdiff.constants import EXE_HG


def test_hg_found_is_executable():
    hg_exe_full_path = EXE_HG()
    assert os.path.isfile(hg_exe_full_path)
    assert os.path.exists(hg_exe_full_path)
    file_str = subprocess.check_output(['file', hg_exe_full_path])
    assert 'executable' in file_str


def test_hg_findable_from_sys_executable():
    test_executable_win = os.path.abspath(os.path.join('C:\\', 'path', 'to', 'python', 'Scripts', 'hg.exe'))
    hg_exe_full_path = EXE_HG(sys_executable = test_executable_win)
    assert hg_exe_full_path == test_executable_win
    test_executable_linux = os.path.abspath(os.path.join('/', 'home', 'user', '.local', 'bin', 'hg'))
    hg_exe_full_path = EXE_HG(sys_executable = test_executable_linux)
    assert hg_exe_full_path == test_executable_linux
