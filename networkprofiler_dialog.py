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
from PyQt4.QtCore import QVariant
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

        # Keep this window on top so we can keep working on the map
        self.window().setWindowFlags(self.window().windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        # We need to separate the state handling here into: Map states and App States

        # Map State objects:
        self.mapCanvas = qgis.utils.iface.mapCanvas()
        self.mapVectorLayers = []
        self.mapSelectedObjects = []

        # Map States:
        self.appSelectedLayer = None
        self.appSelectedIDField = None
        self.appSelectedFields = []

        # Hook an event into the selection changed event to tell us if we can grab our object or not
        self.mapCanvas.layersChanged.connect(self.handlerLayerChange)
        self.mapCanvas.selectionChanged.connect(self.handlerSelectionChange)

        # Hook in a couple of control events for good measure
        self.ctlLayer.currentIndexChanged.connect(self.ctlLayerChange)
        self.ctlIDField.currentIndexChanged.connect(self.ctlIDFieldChange)

        # Set up our button events
        self.cmdBrowseCSV.clicked.connect(lambda: self.save_csv_dialog(self.txtCSVOutput))
        self.cmdGetReachFromMap.clicked.connect(self.autoPopulate)
        self.cmdButtons.button(QtGui.QDialogButtonBox.Ok).clicked.connect(self.RunAction)
        self.cmdButtons.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.close)

        # DEBUG: Just set some default values for now
        self.txtCSVOutput.setText("/Users/work/Desktop/TEST.csv")

    def showEvent(self, event):
        super(networkProfilerDialog, self).showEvent(event)
        # Trigger a recalc of everything the first time
        # Now autopopulate values if we can
        self.handlerLayerChange()
        self.handlerSelectionChange()
        self.autoPopulate()


    def RunAction(self, event):
        """
        Here's where we call the actual tool
        :param event:
        :return:
        """
        selectedLayer = self.ctlLayer.itemData(self.ctlLayer.currentIndex())
        selectedPath = selectedLayer.dataProvider().dataSourceUri().split('|')[0]
        theProfile = Profile(selectedPath, int(self.ctlReachInt.text()))
        theProfile.writeCSV(self.txtCSVOutput.text())

    def setLabelMsg(self, text="", color='black'):
        self.lblWarning.setText(text)
        self.lblWarning.setStyleSheet('QLabel { color: ' + color + ' }')

    def recalcVectorLayerFields(self):
        """
        Get current layer index and then repopulate the dropdowns accordingly
        :return:
        """
        selLayerData = self.ctlLayer.itemData(self.ctlLayer.currentIndex())
        selLayerObj = None
        for obj in self.mapVectorLayers:
            if selLayerData == obj['layer']:
                selLayerObj = obj

        if selLayerObj is not None:
            self.ctlIDField.setEnabled(True)
            self.lstFields.setEnabled(True)

            # Populate the id fields
            self.ctlIDField.clear()
            self.ctlIDField.currentIndexChanged.disconnect(self.ctlIDFieldChange)
            for field in selLayerObj['idFields']:
                self.ctlIDField.addItem(field.name(), field)
            self.ctlIDField.currentIndexChanged.connect(self.ctlIDFieldChange)

            # Populate the list of fields to use
            self.lstFields.clear()
            for field in selLayerObj['fields']:
                item = QtGui.QListWidgetItem(field.name())
                self.lstFields.addItem(item)

            # Select all by default.
            if len(self.lstFields.selectedIndexes()) == 0:
                self.lstFields.selectAll()

        else:
            self.ctlIDField.clear()
            self.ctlIDField.setEnabled(False)
            self.lstFields.setEnabled(False)

    def recalcVectorLayers(self):
        """
        Rebuild the vector layers combo box and reset the selected item if necessary
        """
        self.ctlLayer.clear()
        self.ctlLayer.currentIndexChanged.disconnect(self.ctlLayerChange)
        for layerObj in self.mapVectorLayers:
            self.ctlLayer.addItem(layerObj['layer'].name(), layerObj['layer'])
        self.ctlLayer.currentIndexChanged.connect(self.ctlLayerChange)

        idx = self.ctlLayer.currentIndex()
        if idx > 0:
            self.appVectorLayer = self.ctlLayer.itemData(idx)
            # if not in list then self.appVectorLayer = None
        else:
            self.setAppVectorLayerFromMap()


    def setAppVectorLayerFromMap(self):
        """
        Set the current map layer in the dropdown from whatever layer is selected on the map
        """
        currLayer = self.mapCanvas.currentLayer()
        selMapLayerIndex = self.ctlLayer.findData(currLayer)

        if selMapLayerIndex > -1:
            self.ctlLayer.setCurrentIndex(selMapLayerIndex)
            # Set the selection independent of the control so if the map changes
            # we'll retain it.
            self.appSelectedLayer = self.ctlLayer.itemData(selMapLayerIndex)

    def getMapVectorLayerFields(self):
        """
        Now just get a list of fields for each layer and identify the int fields
        as possible ID fields
        """
        for layerObj in self.mapVectorLayers:
            allfields = []
            intfields = []
            for field in layerObj['layer'].fields().toList():
                allfields.append(field)
                if field.type() == QVariant.Int:
                    intfields.append(field)
            layerObj['fields'] = allfields
            layerObj['idFields'] = intfields

    def recalcOkButton(self):
        print "ok"


    def recalcReachID(self):
        """
        Set the reach ID field in the UI
        """
        if len(self.mapSelectedObjects) == 1:
            selectedItem = self.mapSelectedObjects[0]

            idx = self.ctlIDField.currentIndex()
            if idx > -1:
                fieldname = self.ctlIDField.itemData(idx).name()
                self.txtReachID.setText(str(selectedItem[0].attribute(fieldname)))

    def recalcGrabButton(self):
        """
        Set the Grab button to be disabled for all but one case
        :return:
        """
        self.cmdGetReachFromMap.setEnabled(False)
        if len(self.mapSelectedObjects) > 1:
            self.setLabelMsg(
                "You have {} features selected. To use the grab tool you must select only one.".format(
                    len(self.mapSelectedObjects)))
        elif len(self.mapSelectedObjects) == 0:
            self.setLabelMsg("You have 0 features selected. To use the grab tool you must select at least one.".format(
                len(self.mapSelectedObjects)))
        else:
            self.setLabelMsg("One reach selected. Use the Grab button to populate the fields above")
            self.cmdGetReachFromMap.setEnabled(True)


    """
    There are 3 kinds of change events we care about:
        1. the layer changes
        2. the selection changes
        3. the app changes

    These methods should be REALLY simple. No logic at all please.
    """
    def handlerLayerChange(self):
        if self.isVisible():
            # Get the data from the maps
            self.getMapVectorLayers()
            self.getMapVectorLayerFields()

            # Now repopulate the dropdowns
            self.recalcVectorLayers()

    def handlerSelectionChange(self):
        if self.isVisible():
            self.getSelectedMapObjects()
            self.recalcGrabButton()

    def ctlLayerChange(self):
        if self.isVisible():
            self.recalcVectorLayerFields()
            self.stateUpdate()

    def ctlIDFieldChange(self):
        if self.isVisible():
            self.stateUpdate()

    def autoPopulate(self):
        """
        This is the magic function that pulls values from the map selection
        :return:
        """
        self.setAppVectorLayerFromMap()
        self.stateUpdate()

    def stateUpdate(self):
        """
        This is the function that ripples through and updates the state of the UI
        :return:
        """
        self.recalcReachID()
        self.recalcGrabButton()
        self.recalcOkButton()


    """
    MAP HELPERS
    """
    def getSelectedMapObjects(self):
        """
        Get a helpful list of selected objects on the map
        :return:
        """
        self.mapSelectedObjects = []
        for layer in self.mapVectorLayers:
            for feat in layer['layer'].selectedFeatures():
                self.mapSelectedObjects.append((feat, layer['layer']))

    def getMapVectorLayers(self):

        self.mapVectorLayers = [{'layer':layer} for layer in self.mapCanvas.layers() if type(layer) is QgsVectorLayer]

    """
    Dialog Boxes
    """

    def save_csv_dialog(self, txtControl):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Output File", "", "CSV File (*.csv);;All files (*)")
        txtControl.setText(filename)
        self.appChangeEvent()

    def existing_shp_browser(self, txtControl):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Open file", "", "Shp File (*.shp);;All files (*)")
        txtControl.setText(filename)
        self.appChangeEvent()

    def folder_browser(self, txtControl):
        foldername = QtGui.QFileDialog.getExistingDirectory(self, "Select Folder")
        txtControl.setText(foldername)

