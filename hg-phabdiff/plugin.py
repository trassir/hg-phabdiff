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
    p = subprocess.Popen(
        [
            EXE_HG(), "import",
            "--cwd", repo_root,
            "--no-commit", "-"
        ],
        stdin=subprocess.PIPE)
    p.communicate(diff_txt)
    subprocess.check_call(
        [
            EXE_HG(), "commit",
            "--cwd", repo_root,
            "-m", "'auto-applied diff %s'" % os.environ[ENVVAR_PHAB_DIFF()],
            "-u", "jenkins"
        ]
    )
