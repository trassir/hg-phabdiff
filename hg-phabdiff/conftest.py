#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import subprocess
import pytest
from constants import EXE_HG


def _hg_create_randomrepo(root, nchanges):
    def _hg_add_file(filename, size):
        text = open(__file__).read().decode("utf-8")
        filedata = unicode((text * (size / len(text) + 1))[:size])
        filedata += u'строка на русском'
        filedata += u'任何字符串在中國'
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        open(filename, "wb").write(filedata.encode("utf-8"))
        subprocess.check_call([EXE_HG(), "add", filename])
    cd = os.curdir
    os.chdir("%s" % root)
    subprocess.check_call([EXE_HG(), "init"])
    for c in xrange(1, nchanges + 1):
        # this range ensures that current commit has
        # tracked unmodified, newly created and modified files
        for f in xrange((c - 1) ** 2 / 2, c ** 2):
            file_name = "file-%s" % format(f, 'b')
            file_dir = os.path.join(*list(format(f, 'b')[:3]))
            file_size = 128 * f + 16 * c
            _hg_add_file(os.path.join(file_dir, file_name), file_size)
        subprocess.check_call([EXE_HG(), "commit", "-m", "update #%s" % c, "-u", "testuser"])
    os.chdir(cd)


@pytest.fixture(scope='function')
def prepare_repos(tmpdir_factory):
    local = ("%s" % tmpdir_factory.mktemp("local")).replace("\\", "/")
    patched = ("%s" % tmpdir_factory.mktemp("patched")).replace("\\", "/")
    _hg_create_randomrepo(local, 5)
    subprocess.check_call([EXE_HG(), "clone", "--cwd", patched, local, "."])
    patch = subprocess.check_output([EXE_HG(), "export", "--cwd", local, "-r", "head()"]).decode("utf-8")
    subprocess.check_call([EXE_HG(), "strip", "--cwd", local, "-r", "head()", "--config", "extensions.strip="])
    return (local, patched, patch)
