#!/usr/bin/env python2

import os
import subprocess
import re
import hexdump
from phabricator import Phabricator
from constants import ENVVAR_PHAB_DIFF
from constants import EXE_HG
from logger import log

DIFF_GIT_HEADER_REGEX = re.compile('^diff --git a/(.*) b/(.*)$')


def phabricator_factory():  #pragma: no cover
    return Phabricator()


def get_diff_from_phabricator():
    phabricator = phabricator_factory()
    phabricator.update_interfaces()
    diff_id = os.environ[ENVVAR_PHAB_DIFF()]
    diff_txt = phabricator.differential.getrawdiff(diffID=diff_id).response
    phab_diff = phabricator.differential.diff.search(
        constraints=dict(ids=[int(diff_id)]))
    revision_phid = phab_diff.data[0]['fields']['revisionPHID']
    phab_revision = phabricator.differential.revision.search(
        constraints=dict(phids=[revision_phid]))
    revision_title = phab_revision.data[0]['fields']['title']
    revision_id = phab_revision.data[0]['id']
    return diff_id, diff_txt, revision_id, revision_title


def apply_phab_diff(repo_root):
    if ENVVAR_PHAB_DIFF() not in os.environ:
        return
    diff_id, diff_txt, revision_id, revision_title = get_diff_from_phabricator()

    # if diff adds, copies or renames files, then we have to make sure that
    # working copy has no interferring untracked remains
    # which will stop patch from being applied.

    # remove any files mentioned in diff
    diff_lines = diff_txt.splitlines()
    for line in diff_lines:
        match = DIFF_GIT_HEADER_REGEX.match(line)
        if match:
            for fpath in match.groups():
                file_path = os.path.join(repo_root, fpath)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    # restore tracked files to their original state
    subprocess.check_call(
        [
            EXE_HG(), 'revert',
            '--cwd', repo_root,
            '--all'
        ]
    )

    process = subprocess.Popen(
        [
            EXE_HG(), 'import',
            '--cwd', repo_root,
            '--no-commit', '-'
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _, stderr = process.communicate(diff_txt.encode('utf-8'))
    except UnicodeDecodeError:
        log('UnicodeDecodeError error while sending diff to hg, diff dump:')
        for dump_line in hexdump.dumpgen(diff_txt):
            log(dump_line)
        raise

    if process.wait():
        raise RuntimeError('hg import failed: %s' % stderr)

    message = 'D{revision_id} (#{diff_id}) {revision_title}'.format(
        revision_id=revision_id,
        diff_id=diff_id,
        revision_title=revision_title)
    subprocess.check_call(
        [
            EXE_HG(), 'commit',
            '--cwd', repo_root,
            '-m', message,
            '-u', 'jenkins'
        ]
    )
