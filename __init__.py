# -*- coding: utf-8 -*-
"""
/***************************************************************************
 networkProfiler
                                 A QGIS plugin
 Scrape ShapeFile Attributees From a River Network ShapeFile
                             -------------------
        begin                : 2017-03-13
        copyright            : (C) 2017 by North Arrow Research Ltd.
        email                : info@northarrowresearch.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

######################### REMOTE DEBUG #########################
# To activate remote debugging set DEBUG_PLUGIN=AnalystToolbar as a QGIS
# Environment variable in Preferences -> System -> Environment
import os
import logging
DEBUG = False
if 'DEBUG_PLUGIN' in os.environ and os.environ['DEBUG_PLUGIN'] == "NetworkProfiler":
    import pydevd
    pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True, suspend=False)
    DEBUG = True
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
######################### /REMOTE DEBUG #########################

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load networkProfiler class from file networkProfiler.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .networkprofiler import NetworkProfiler
    return NetworkProfiler(iface)
