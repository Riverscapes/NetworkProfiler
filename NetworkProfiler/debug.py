from os import environ
import logging


class Debugger():
    DEBUG = False

    def __init__(self):

        if 'DEBUG_PLUGIN' in environ and environ['DEBUG_PLUGIN'] == "NetworkProfiler":
            import pydevd
            pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True, suspend=False)
            Debugger.DEBUG = True
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)