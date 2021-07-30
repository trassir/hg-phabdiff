import os
import sys
import subprocess

def ENVVAR_PHAB_DIFF():
    return 'HG_PHAB_DIFF'


def EXE_HG(sys_executable = sys.executable):
    hg_names = [os.path.sep + 'hg.exe', os.path.sep + 'hg']
    hg_full_path = ''

    # running as plugin for hg.exe
    for hg_name in hg_names:
        if sys_executable.endswith(hg_name):
            return os.path.abspath(sys_executable)

    # running as python module
    # importing pip is not supported by devs, they recommend this instead
    cmd = [sys_executable, '-m', 'pip', 'show', '-f', 'mercurial']
    mercurial_files = subprocess.check_output(cmd).decode().splitlines()
    module_location = [x for x in mercurial_files if x.startswith('Location: ')][0].split(': ')[1].strip()
    for hg_name in hg_names:
        hg_paths = [x for x in mercurial_files if x.endswith(hg_name)]
        if hg_paths:
            hg_full_path = os.path.abspath(os.path.join(module_location, hg_paths[0].strip()))
            break

    return hg_full_path
