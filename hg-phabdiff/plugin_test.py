#!/usr/bin/env python2

import os
import plugin
import subprocess
import pytest
from constants import ENVVAR_PHAB_DIFF
from constants import EXE_HG


class PhabricatorMock(object):
    class DifferentialMock(object):
        class RawDiffMock(object):
            def __init__(self, diff = ""):
                self.response = diff
        def __init__(self, diff = ""):
            self.diff = diff
        def getrawdiff(self, diffID = ""):
            assert diffID == "test"
            return self.RawDiffMock(diff = self.diff)
    def update_interfaces(self):
        pass
    def __init__(self, diff = ""):
        self.differential = self.DifferentialMock(diff=diff)


class Hg(object):
    def __init__(self, repo_cwd):
        self.repo_cwd = repo_cwd
    def check_call(self, *args):
        return subprocess.check_call([EXE_HG(), "--cwd", self.repo_cwd] + list(args))
    def check_output(self, *args):
        return subprocess.check_output([EXE_HG(), "--cwd", self.repo_cwd] + list(args))

    def current_commit(self):
        return self.check_output('log', '-T', '{node}', '-r', '.')
    def count_commits(self):
        return len(self.check_output('log', '-T', 'x'))


def test_apply_phab_diff(mocker, prepare_repos):
    (local, patched, patch) = prepare_repos

    def phabricatormock_factory():
        return PhabricatorMock(diff=patch)

    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)
    os.environ[ENVVAR_PHAB_DIFF()] = "test"
    hg = Hg(local)

    plugin.apply_phab_diff(local)
    hg.check_call("out", patched)
    hg.check_call("strip", "-r", "head()", "--config", "extensions.strip=")
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        hg.check_call("out", patched)
    assert excinfo.value.returncode == 1

def test_apply_no_diff(prepare_repos):
    (local, _, _) = prepare_repos
    if ENVVAR_PHAB_DIFF() in os.environ:
        os.environ.pop(ENVVAR_PHAB_DIFF())
    plugin.apply_phab_diff(local)

def test_hg_import_fail(mocker, prepare_repos):
    (local, _, _) = prepare_repos

    def phabricatormock_factory():
        return PhabricatorMock(diff="not a diff content")

    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)
    os.environ[ENVVAR_PHAB_DIFF()] = "test"
    hg = Hg(local)

    commit_before = hg.current_commit()
    count_before = hg.count_commits()
    with pytest.raises(RuntimeError, match='hg import failed.+stdin: no diffs found'):
        plugin.apply_phab_diff(local)
    assert hg.current_commit() == commit_before
    assert hg.count_commits() == count_before
