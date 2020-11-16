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
    def check_output(self, *args):
        return subprocess.check_output([EXE_HG(), "--cwd", self.repo_cwd] + list(args), stderr=None)
    def current_commit(self):
        return self.check_output('log', '-T', '{node}', '-r', '.')
    def count_commits(self):
        return len(self.check_output('log', '-T', 'x'))


class AssertRepositoryIntact(object):
    def __init__(self, repo):
        self.repo = repo
    def __enter__(self):
        self.hg = Hg(self.repo)
        self.commit_before = self.hg.current_commit()
        self.count_before = self.hg.count_commits()
        self.diff_before = self.hg.check_output("diff")
        return self
    def __exit__(self, exc_type, exc_value, exc_trace):
        if exc_value is not None:
            return False #pragma: no cover
        assert self.hg.current_commit() == self.commit_before
        assert self.hg.count_commits() == self.count_before
        assert self.hg.check_output("diff") == self.diff_before
        return True


class AssertPatchAppliedCorrectly(object):
    def __init__(self, original_repo = None, patched_repo = None):
        assert original_repo is not None
        assert patched_repo is not None
        self.original_repo = original_repo # where code was originally created as commit
        self.patched_repo = patched_repo # where code was applied as patch
    def __enter__(self):
        self.hg = Hg(self.patched_repo)
        return self
    def __exit__(self, exc_type, exc_value, exc_trace):
        if exc_value is not None:
            return False #pragma: no cover
        # after patching, there should be only one commit difference from original
        outgoing = self.hg.check_output("out", "--template", "{node}", "--quiet",
                                   self.original_repo)
        assert len(outgoing.splitlines()) == 1
        # after patching, files in "patched" working copy should be identical "original" one
        diff = subprocess.check_output(["diff", "-x", ".hg", "-r", "-u",
                                        self.patched_repo, self.original_repo])
        assert not diff
        return True


def test_apply_legitimate_patch_from_phab_diff(mocker, prepare_repos):
    (original, patch, local) = prepare_repos

    def phabricatormock_factory():
        return PhabricatorMock(diff=patch)

    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)
    os.environ[ENVVAR_PHAB_DIFF()] = "test"

    with AssertPatchAppliedCorrectly(original_repo = original, patched_repo = local):
        plugin.apply_phab_diff(local)


def test_no_diff_specified_in_envvar(prepare_repos):
    (_, _, local) = prepare_repos

    os.environ.pop(ENVVAR_PHAB_DIFF(), None)

    with AssertRepositoryIntact(local):
        plugin.apply_phab_diff(local)


def test_patch_has_no_diff_content(mocker, prepare_repos):
    (_, _, local) = prepare_repos

    def phabricatormock_factory():
        return PhabricatorMock(diff="not a diff content")

    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)
    os.environ[ENVVAR_PHAB_DIFF()] = "test"

    with AssertRepositoryIntact(local):
        # this call should fail, since patch has no diff content in it
        with pytest.raises(RuntimeError, match='hg import failed.+stdin: no diffs found'):
            plugin.apply_phab_diff(local)


def test_working_copy_has_untracked_files_colliding_with_patch(mocker, prepare_repos):
    (original, patch, local) = prepare_repos

    def phabricatormock_factory():
        return PhabricatorMock(diff=patch)

    mocker.patch('plugin.phabricator_factory', side_effect=phabricatormock_factory)
    os.environ[ENVVAR_PHAB_DIFF()] = "test"

    # create untracked files in "local" working directory
    # that will cause collision with patch
    for root, _, files in os.walk(original):
        if ".hg" in root:
            continue
        for filename in files:
            subprocess.check_call(["touch", os.path.join(root.replace(original, local), filename)])

    with AssertPatchAppliedCorrectly(original_repo = original, patched_repo = local):
        plugin.apply_phab_diff(local)
