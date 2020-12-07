#!/usr/bin/env python2

import os
import subprocess
import hexdump
import re
from constants import EXE_HG
from phabricator import Phabricator
from constants import ENVVAR_PHAB_DIFF
from logger import log

DIFF_GIT_HEADER_REGEX = re.compile('^diff --git a/(.*) b/(.*)$')


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
            EXE_HG(), 'id', '--id', '-T', '{id}',
            '--cwd', repo_root,
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, commit_id = p.communicate()
    commit_id = commit_id.replace('+', '')

    # if diff adds, copies or renames files, then we have to make sure that
    # working copy has no interferring untracked remains
    # which will stop patch from being applied.

    # remove any files mentioned in diff
    diff_lines = diff_txt.splitlines()
    while diff_lines:
        line = diff_lines.pop()
        m = DIFF_GIT_HEADER_REGEX.match(line)
        if m:
            for f in m.groups():
                file_path = os.path.join(repo_root, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    # restore tracked files to their original state
    subprocess.check_call(
        [
            EXE_HG(), 'update',
            '--cwd', repo_root,
            '--rev', commit_id,
            '--clean'
        ]
    )

    p = subprocess.Popen(
        [
            EXE_HG(), 'import',
            '--cwd', repo_root,
            '--no-commit', '-'
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _, stderr = p.communicate(diff_txt.encode('utf-8'))
    except UnicodeDecodeError:
        log('UnicodeDecodeError error while sending diff to hg, diff dump:')
        for dump_line in hexdump.dumpgen(diff_txt):
            log(dump_line)
        raise
    import_ret = p.wait()
    if import_ret:
        raise RuntimeError('hg import failed: %s' % stderr)

    subprocess.check_call(
        [
            EXE_HG(), 'commit',
            '--cwd', repo_root,
            '-m', 'auto-applied diff %s' % os.environ[ENVVAR_PHAB_DIFF()],
            '-u', 'jenkins'
        ]
    )
