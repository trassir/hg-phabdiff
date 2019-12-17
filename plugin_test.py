#!/usr/bin/env python2

import os
import plugin
import subprocess
import pytest
from constants import ENVVAR_PHAB_DIFF
from constants import EXE_HG


class PhabricatorMock:
    class DifferentialMock:
        class RawDiffMock:
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


def test_apply_with_uncommitted(mocker, prepare_repos):
    (local, patched, patch) = prepare_repos
    def current_commit():
        return subprocess.check_output([EXE_HG(), "--cwd", local, 'log', '-T', '{node}', '-r', '.'])
    def count_commits():
        return len(subprocess.check_output([EXE_HG(), "--cwd", local, 'log', '-T', 'x']))
    def has_uncommitted():
        return bool(subprocess.check_output([EXE_HG(), "--cwd", local, 'status',
            '--no-status', '--modified', '--added', '--removed', '--deleted']))

    assert not has_uncommitted()
    initial_commits = count_commits()
    filename = 'file'
    with open(filename, 'w') as f:
        f.write('hi\n')
    subprocess.check_call([EXE_HG(), "--cwd", local, "add", filename])
    subprocess.check_call([EXE_HG(), "--cwd", local, "commit", "-m", "add %s" % filename, "-u", "testuser"])
    assert count_commits() == initial_commits+1
    commit = current_commit()

    with open(filename, 'a') as f:
        f.write('world\n')
    assert has_uncommitted()

    os.environ[ENVVAR_PHAB_DIFF()] = "test"
    with pytest.raises(Exception):
        plugin.apply_phab_diff(local)

    assert has_uncommitted()
    assert count_commits() == initial_commits+1
    assert current_commit() == commit


def test_apply_phab_diff(mocker, prepare_repos):
    (local, patched, patch) = prepare_repos
    def phabricatormock_factory():
        return PhabricatorMock(diff=patch)
    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)
    os.environ[ENVVAR_PHAB_DIFF()] = "test"
    plugin.apply_phab_diff(local)
    subprocess.check_call([EXE_HG(), "out", "--cwd", local, patched])
    subprocess.check_call([EXE_HG(), "strip", "--cwd", local, "-r", "head()", "--config", "extensions.strip="])
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        subprocess.check_call([EXE_HG(), "out", "--cwd", local, patched])
    assert excinfo.value.returncode == 1

def test_apply_no_diff(mocker, prepare_repos):
    (local, patched, patch) = prepare_repos
    if ENVVAR_PHAB_DIFF() in os.environ:
        os.environ.pop(ENVVAR_PHAB_DIFF())
    plugin.apply_phab_diff(local)
