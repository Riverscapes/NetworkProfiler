from PyQt4.QtCore import QSettings
from os import path

# BASE is the name we want to use inside the settings keys
BASE="QGISNetworkProfiler"
# DEFAULT SETTINGS: We may need to externalize this somehow
_SETTINGS = {
    "DataDir": {
        "default": path.join(path.expanduser("~"), "RiverscapesData")
    }
}

class SettingsBorg(object):
    _shared_state = {}
    _initdone = False

    def __init__(self):
        self.__dict__ = self._shared_state


class Settings(SettingsBorg):
    """
    Read up on the Borg pattern if you don't already know it. Super useful
    """
    def __init__(self):
        super(SettingsBorg, self).__init__()
        if not self._initdone:
            print "Init Settings"
            s = QSettings()
            # Do a sanity check and reset anything that looks fishy
            for key in _SETTINGS.iterkeys():
                s.beginGroup(BASE)
                if key not in s.childKeys():
                    self.resetDefault(key)
                else:
                    val = self.getSetting(key)
                    if len(val) == 0 or val is None:
                        self.resetDefault(key)
                s.endGroup()
            # Must be the last thing we do in init
            self._initdone = True


    def resetAll(self):
        """
        rRset all items to their default values
        :return:
        """
        for key in _SETTINGS.iterkeys():
            self.resetDefault(key)

    def resetDefault(self, key):
        """
        Reset a single value to its default
        :param key:
        :return:
        """
        s = QSettings()
        s.beginGroup(BASE)
        if key in _SETTINGS and "default" in _SETTINGS[key]:
            s.setValue(key, _SETTINGS[key]['default'])
            _SETTINGS[key]['value'] = _SETTINGS[key]['default']
        s.endGroup()

    def getSetting(self, key):
        """
        Get one setting from the in-memory store and if not present then the settings file
        :return:
        """
        value = None
        if key in _SETTINGS and 'value' in _SETTINGS[key]:
            value = _SETTINGS[key]['value']
        else:
            s = QSettings()
            s.beginGroup(BASE)
            if key in s.childKeys():
                value = s.value(key)
                _SETTINGS[key]['value'] = value
            s.endGroup()
        return value

    def saveSetting(self, key, value):
        """
        Write or overwrite a setting. Update the in-memory store  at the same time
        :param name:
        :param settings:
        :return:
        """
        s = QSettings()
        s.beginGroup(BASE)
        # Set it in the file
        s.setValue(key, value)
        # Don't forget to save it back to memory
        _SETTINGS[key]['value'] = value
        s.endGroup()


