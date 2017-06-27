from os import environ
import logging

# class DebuggerBorg(object):
#     _shared_state = {}
#     _initdone = False
#
#     def __init__(self):
#         self.__dict__ = self._shared_state

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