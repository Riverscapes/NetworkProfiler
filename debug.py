import os
DEBUG = False

######################### REMOTE DEBUG #########################
# To activate remote debugging set DEBUG_PLUGIN=AnalystToolbar as a QGIS
# Environment variable in Preferences -> System -> Environment
if 'DEBUG_PLUGIN' in os.environ and os.environ['DEBUG_PLUGIN'] == "NetworkProfiler":
    import pydevd
    pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True, suspend=False)
    DEBUG=True
######################### /REMOTE DEBUG #########################