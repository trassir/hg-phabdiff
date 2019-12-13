#!/usr/bin/env python2

import os
import subprocess
import hashlib
import pytest
from constants import EXE_HG

def _hg_create_randomrepo(root, ncommits):
    def _hg_commit(size):
        text = open(__file__).read()
        filedata = (text * (size / len(text) + 1))[:size]
        md5 = hashlib.md5()
        md5.update(filedata)
        filename = os.path.join(md5.hexdigest())
        open(filename, "wb").write(filedata)
        subprocess.check_call([EXE_HG(), "add", filename])
        subprocess.check_call([EXE_HG(), "commit", "-m", "add %s" % filename, "-u", "testuser"])
    cd = os.curdir
    os.chdir("%s" % root)
    subprocess.check_call([EXE_HG(), "init"])
    for i in xrange(1, ncommits):
        _hg_commit(128 * i)
    os.chdir(cd)


@pytest.fixture(scope='function')
def prepare_repos(tmpdir_factory):
    local = ("%s" % tmpdir_factory.mktemp("local")).replace("\\", "/")
    patched = ("%s" % tmpdir_factory.mktemp("patched")).replace("\\", "/")
    _hg_create_randomrepo(local, 5)
    subprocess.check_call([EXE_HG(), "clone", "--cwd", patched, local, "."])
    patch = subprocess.check_output([EXE_HG(), "export", "--cwd", local, "-r", "head()"])
    subprocess.check_call([EXE_HG(), "strip", "--cwd", local, "-r", "head()"])
    return (local, patched, patch)
