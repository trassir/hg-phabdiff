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

    def has_uncommitted():
        return bool(subprocess.check_output(
            [
                EXE_HG(), 'status',
                '--cwd', repo_root,
                '--no-status', '--modified', '--added', '--removed', '--deleted'
            ]
        ))
    if has_uncommitted():
        raise RuntimeError('Uncommitted changes')
    p = phabricator_factory()
    p.update_interfaces()
    diff_id=os.environ[ENVVAR_PHAB_DIFF()]

    diffs = p.differential.diff.search(constraints=dict(ids=[int(diff_id)])).data
    assert len(diffs) == 1
    revs = p.differential.query(phids=[diffs[0]['fields']['revisionPHID']])
    assert len(revs) == 1
    depends = revs[0]['auxiliary']['phabricator:depends-on']
    if depends:
        raise RuntimeError('The diff has dependencies in stack')

    diff_txt = p.differential.getrawdiff(diffID=diff_id).response
    cmd = [
        EXE_HG(), "import",
        "--cwd", repo_root,
        "--no-commit", "-"
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    _, err = p.communicate(diff_txt)
    code = p.wait()
    if code:
        raise RuntimeError("hg import failed with %d:\n%s" % (code, err))
    subprocess.check_call(
        [
            EXE_HG(), "commit",
            "--cwd", repo_root,
            "-m", "'auto-applied diff %s'" % os.environ[ENVVAR_PHAB_DIFF()],
            "-u", "jenkins"
        ]
    )
