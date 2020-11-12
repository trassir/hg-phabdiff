#!/usr/bin/env python2

import os
import subprocess
from constants import EXE_HG
from phabricator import Phabricator
from constants import ENVVAR_PHAB_DIFF


def phabricator_factory():  #pragma: no cover
    return Phabricator()


def apply_phab_diff(repo_root):
    if ENVVAR_PHAB_DIFF() not in os.environ:
        return
    p = phabricator_factory()
    p.update_interfaces()
    diff_id=os.environ[ENVVAR_PHAB_DIFF()]
    diff_txt = p.differential.getrawdiff(diffID=diff_id).response

    # if diff adds files, then we have to make sure that
    # working copy has no interferring untracked remains
    # which will stop patch from being applied
    diff_lines = diff_txt.splitlines()
    while diff_lines:
        line = diff_lines.pop()
        if line.startswith("+++ ") and diff_lines:
            file_added_mark = diff_lines.pop()
            if file_added_mark == "--- /dev/null":
                file_added_name = line[6:]
                file_full_path = os.path.join(repo_root, file_added_name)
                if os.path.isfile(file_full_path):
                    os.remove(file_full_path)

    p = subprocess.Popen(
        [
            EXE_HG(), "import",
            "--cwd", repo_root,
            "--no-commit", "-"
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = p.communicate(diff_txt.encode("utf-8"))
    import_ret = p.wait()
    if import_ret:
        raise RuntimeError("hg import failed: %s" % stderr)

    subprocess.check_call(
        [
            EXE_HG(), "commit",
            "--cwd", repo_root,
            "-m", "auto-applied diff %s" % os.environ[ENVVAR_PHAB_DIFF()],
            "-u", "jenkins"
        ]
    )
