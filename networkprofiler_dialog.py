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
from lib.profiler import Profile

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

        # DEBUG: Just set some default values for now
        self.txtCSVOutput.setText("/Users/work/Desktop/TEST.csv")

        self.cmdBrowseCSV.clicked.connect(lambda: self.save_csv_dialog(self.txtCSVOutput))

        self.cmdGetReachFromMap.clicked.connect(self.manualGrabReach)
        self.cmdButtons.button(QtGui.QDialogButtonBox.Ok).clicked.connect(self.RunAction)
        self.cmdButtons.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.close)
        self.recalc_state()

    def RunAction(self, event):
        selectedLayer = self.ctlLayer.itemData(self.ctlLayer.currentIndex())
        selectedPath = selectedLayer.dataProvider().dataSourceUri().split('|')[0]
        theProfile = Profile(selectedPath, int(self.ctlReachInt.text()))
        theProfile.writeCSV(self.txtCSVOutput.text())

    def updateLayerCombo(self):
        for layer in self.vectorLayers:
            self.ctlLayer.addItem(layer.name(), layer)

    def getSelectedReaches(self):
        # TODO: Grab the currently selected Reach
        self.selectedReaches = []
        for layer in self.vectorLayers:
            for feat in layer.selectedFeatures():
                self.selectedReaches.append((feat, layer))

        # We only want to do the work if there's exactly one reach selected
        if len(self.selectedReaches) == 1:
            selectedItem = self.selectedReaches[0]
            selectedindex = self.ctlLayer.findData(selectedItem[1])
            if selectedindex >= 0:
                self.ctlLayer.setCurrentIndex(selectedindex)
            self.ctlReachInt.setText(str(selectedItem[0].id()))

    def manualGrabReach(self):
        # This function just gives a little more context to why things aren't working.
        self.getSelectedReaches()
        if len(self.selectedReaches) > 1:
            self.setLabelMsg("You have {} features selected. You must only select one.".format(len(self.selectedReaches)), "red")
        elif len(self.selectedReaches) == 0:
            self.setLabelMsg("You have 0 features selected. You must only select at least one.".format(len(self.selectedReaches)), "red")

    def save_csv_dialog(self, txtControl):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Output File", "", "CSV File (*.csv);;All files (*)")
        txtControl.setText(filename)
        self.recalc_state()

    def existing_shp_browser(self, txtControl):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Open file", "", "Shp File (*.shp);;All files (*)")
        txtControl.setText(filename)
        self.recalc_state()

    def folder_browser(self, txtControl):
        foldername = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder")
        txtControl.setText(foldername)
        self.recalc_state()

    def setLabelMsg(self, text="", color='black'):
        self.lblWarning.setText(text)
        self.lblWarning.setStyleSheet('QLabel { color: ' + color + ' }')


    def recalc_state(self):
        """
        When something happens we want to recalculate the state of the application.
        Careful when and how you call this to avoid infinite event loops
        :return:
        """
        # Clear the warning label
        self.setLabelMsg()
        canvas = qgis.utils.iface.mapCanvas()
        layers = canvas.layers()

        # It's useful to have a list of vector layers for what comes next
        self.vectorLayers = [layer for layer in layers if type(layer) is qgis._core.QgsVectorLayer]

        # Here are the state recalc functions we're calling. Be careful not to cause infinite loops.
        # These should not call recalc_state or each other
        self.updateLayerCombo()
        self.getSelectedReaches()
        print "recalc state"