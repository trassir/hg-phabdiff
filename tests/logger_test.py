from sys import stdout
from hg_phabdiff.logger import log


def test_log_print():
    log('message')


def test_log_stream():
    log('message', stdout)
