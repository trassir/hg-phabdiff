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


def test_apply_phab_diff(mocker, prepare_repos):
    (local, patched, patch) = prepare_repos
    def phabricatormock_factory():
        return PhabricatorMock(diff=patch)
    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)
    os.environ[ENVVAR_PHAB_DIFF()] = "test"
    plugin.apply_phab_diff(local)
    subprocess.check_call([EXE_HG(), "out", "--cwd", local, patched])
    subprocess.check_call([EXE_HG(), "strip", "--cwd", local, "-r", "head()"])
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        subprocess.check_call([EXE_HG(), "out", "--cwd", local, patched])
    assert excinfo.value.returncode == 1

def test_apply_no_diff(mocker, prepare_repos):
    (local, patched, patch) = prepare_repos
    if ENVVAR_PHAB_DIFF() in os.environ:
        os.environ.pop(ENVVAR_PHAB_DIFF())
    plugin.apply_phab_diff(local)
