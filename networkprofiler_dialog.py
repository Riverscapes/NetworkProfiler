# -*- coding: utf-8 -*-
"""
/***************************************************************************
 networkProfilerDialog
                                 A QGIS plugin
 Scrape ShapeFile Attributees From a River Network ShapeFile
                             -------------------
        begin                : 2017-03-13
        git sha              : $Format:%H$
        copyright            : (C) 2017 by North Arrow Research Ltd.
        email                : info@northarrowresearch.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic


from qgis.core import *
from qgis.gui import *
import qgis.utils

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'networkprofiler_dialog_base.ui'))


class networkProfilerDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(networkProfilerDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.cmdBrowseNetwork.clicked.connect(self.browseNetwork)

    def browseNetwork(self, event):

        canvas = qgis.utils.iface.mapCanvas()
        layers = canvas.layers()

        for i in layers:

            if i.name() == "Layer2":
                alayer = i
            elif i.name() == "Layer1":
                blayer = i



        # filename = QtGui.QFileDialog.getOpenFileName(self, "Open XML file", "",
        #                                              "XML File (*.xml);;GCD File (*.gcd);;All files (*)")
        # self.xmlLocation.setText(filename)
        # self.projectXML = ProjectXML(filename, self.treeView)
        # self.recalc_state()
        print "button clicked"