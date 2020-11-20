from sys import stdout
from logger import log


def test_log_print():
    log('message')


def test_log_stream():
    log('message', stdout)
