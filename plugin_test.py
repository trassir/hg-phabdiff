#!/usr/bin/env python2

import os
import plugin
import subprocess
import pytest
from constants import ENVVAR_PHAB_DIFF
from constants import EXE_HG

class DiffIds:
    GENERIC = "1337"
    DEPENDS_ON = "1338"
class RevPhids:
    GENERIC = "PHID-generic"
    DEPENDS_ON = "PHID-depends-on"

class PhabricatorMock:
    class DifferentialMock:
        class RawDiffMock:
            # RawDiffMock
            def __init__(self, diff = ""):
                self.response = diff
        # DifferentialMock
        def __init__(self, diff_contents = ""):
            self.diff_contents = diff_contents
            self.diff = self.DiffMock()

        def getrawdiff(self, diffID = ""):
            return self.RawDiffMock(diff = self.diff_contents)

        def query(self, phids):
            if phids[0] == RevPhids.DEPENDS_ON:
                return [dict(auxiliary={'phabricator:depends-on': 'something'})]
            if phids[0] == RevPhids.GENERIC:
                return [dict(auxiliary={'phabricator:depends-on': None})]
            assert False, 'Unknown query'

        class DiffMock:
            class SearchDiffMock:
                # SearchDiffMock
                def __init__(self, data):
                    self.data = data
            def search(self, constraints):
                if 'ids' in constraints:
                    ids = constraints['ids']
                    if int(DiffIds.DEPENDS_ON) in ids:
                        return self.SearchDiffMock([dict(fields=dict(revisionPHID=RevPhids.DEPENDS_ON))])
                    if int(DiffIds.GENERIC) in ids:
                        return self.SearchDiffMock([dict(fields=dict(revisionPHID=RevPhids.GENERIC))])
                assert False, 'Unknown search'
    def update_interfaces(self):
        pass
    def __init__(self, diff = ""):
        self.differential = self.DifferentialMock(diff_contents=diff)


def test_apply_with_uncommitted(mocker, prepare_repos):
    (local, patched, patch) = prepare_repos
    def phabricatormock_factory():
        return PhabricatorMock(diff=patch)
    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)

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

    os.environ[ENVVAR_PHAB_DIFF()] = DiffIds.GENERIC
    with pytest.raises(Exception, match='Uncommitted changes'):
        plugin.apply_phab_diff(local)

    assert has_uncommitted()
    assert count_commits() == initial_commits+1
    assert current_commit() == commit


def test_apply_phab_diff(mocker, prepare_repos):
    (local, patched, patch) = prepare_repos
    def phabricatormock_factory():
        return PhabricatorMock(diff=patch)
    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)
    os.environ[ENVVAR_PHAB_DIFF()] = DiffIds.GENERIC
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

def test_apply_stacked_diff(mocker, prepare_repos):
    (local, patched, patch) = prepare_repos
    def phabricatormock_factory():
        return PhabricatorMock(diff=patch)
    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)

    def current_commit():
        return subprocess.check_output([EXE_HG(), "--cwd", local, 'log', '-T', '{node}', '-r', '.'])
    def count_commits():
        return len(subprocess.check_output([EXE_HG(), "--cwd", local, 'log', '-T', 'x']))
    def has_uncommitted():
        return bool(subprocess.check_output([EXE_HG(), "--cwd", local, 'status',
            '--no-status', '--modified', '--added', '--removed', '--deleted']))


    initial_commits = count_commits()
    commit = current_commit()

    os.environ[ENVVAR_PHAB_DIFF()] = DiffIds.DEPENDS_ON
    with pytest.raises(Exception, match='The diff has dependencies in stack'):
        plugin.apply_phab_diff(local)

    assert not has_uncommitted()
    assert count_commits() == initial_commits
    assert current_commit() == commit
