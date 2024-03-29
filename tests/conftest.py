# -*- coding: utf-8 -*-

import os
import subprocess
import pytest
from hg_phabdiff.constants import EXE_HG


def _hg_create_randomrepo(root, nchanges):
    def _hg_add_file(filename, size):
        # bytes and encode/decode here are mandatory - otherwise, windows errors
        # with UnicodeDecodeError during either reading __file__ or writing filename
        text = open(__file__, 'rb').read().decode()
        filedata = str((text * (size // len(text) + 1))[:size])
        filedata += 'строка на русском'
        filedata += '任何字符串在中國'
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        new_file = not os.path.exists(filename)
        open(filename, 'wb').write(filedata.encode('utf-8'))
        if new_file:
            subprocess.check_call([EXE_HG(), 'add', '--quiet', filename])
    cd = os.curdir
    os.chdir(str(root))
    subprocess.check_call([EXE_HG(), 'init'])
    rename_list = []
    for c in range(1, nchanges + 1):
        if len(rename_list) > 1:
            # have some files "copied" in commit
            subprocess.check_call([EXE_HG(), 'cp', rename_list[-1], rename_list[-1] + '-copied'])
            # have some files "renamed" in commit
            subprocess.check_call([EXE_HG(), 'mv', rename_list[0], rename_list[0] + '-renamed'])
            rename_list = []
        # this range ensures that current commit has
        # tracked unmodified, newly created and modified files
        for f in range((c - 1) ** 2 // 2, c ** 2):
            file_name = 'file-%s' % format(f, 'b')
            file_dir = os.path.join(*list(format(f, 'b')[:3]))
            file_size = 128 * f + 16 * c
            file_path = os.path.join(file_dir, file_name)
            _hg_add_file(file_path, file_size)
            rename_list.append(file_path)
        subprocess.check_call([EXE_HG(), 'commit', '-m', 'update #%s' % c, '-u', 'testuser'])
    os.chdir(cd)


@pytest.fixture(scope='function')
def prepare_repos(tmpdir_factory):
    local = str(tmpdir_factory.mktemp('local')).replace('\\', '/')
    original = str(tmpdir_factory.mktemp('original')).replace('\\', '/')
    _hg_create_randomrepo(local, 5)
    subprocess.check_call([EXE_HG(), 'clone', '--cwd', original, local, '.'])
    patch = subprocess.check_output([EXE_HG(), 'export', '--git', '--cwd', local, '-r', 'head()']).decode('utf-8')
    subprocess.check_call([EXE_HG(), 'strip', '--cwd', local, '-r', 'head()', '--config', 'extensions.strip='])
    return (original, patch, local)
