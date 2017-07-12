# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NetworkProfilerDialog
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

import qgis.utils
from PyQt4.QtCore import QVariant, Qt, QUrl
from qgis.core import *
from qgis.gui import *

from NetworkProfiler.debug import Debugger
from NetworkProfiler.profiler import Profile
from NetworkProfiler.popupdialog import okDlg
from NetworkProfiler.plot import Plots

HELP_URL = "https://github.com/Riverscapes/NetworkProfiler"
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'networkprofiler_dialog_base.ui'))

class NetworkProfilerDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(NetworkProfilerDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.theProfile = None

        # Keep this window on top so we can keep working on the map
        self.window().setWindowFlags(self.window().windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        # We need to separate the state handling here into: Map states and App States

        # Map State objects:
        self.mapCanvas = qgis.utils.iface.mapCanvas()
        self.mapVectorLayers = []
        self.mapSelectedObjects = []

        # Map States:
        self.appSelectedLayer = None
        self.appSelectedFields = []
        self.appSelectedObjects = []

        # Hook an event into the selection changed event to tell us if we can grab our object or not
        self.mapCanvas.layersChanged.connect(self.handlerLayerChange)
        self.mapCanvas.selectionChanged.connect(self.handlerSelectionChange)

        # Hook in a couple of control events for good measure
        self.cmbLayer.currentIndexChanged.connect(self.cmbLayerChange)

        # Set up our button events
        self.btnCreateProfile.clicked.connect(self.runProfilerAction)
        self.btnGrabFrom.clicked.connect(self.autoPopulate)
        self.btnGrabTo.clicked.connect(self.autoPopulate)
        self.btnFlipFromTo.clicked.connect(self.flipFromTo)

        self.btnCreateProfile.clicked.connect(self.runProfilerAction)
        self.cmdButtons.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.close)
        self.cmdButtons.button(QtGui.QDialogButtonBox.Help).clicked.connect(self.openHelp)

        # When to recalc app state. Choose these carefully. They run a lot.
        self.cmbLayer.currentIndexChanged.connect(self.stateUpdate)
        self.cmbPathChoose.currentIndexChanged.connect(self.stateUpdate)
        self.cmbPathChooseField.currentIndexChanged.connect(self.stateUpdate)
        self.txtPathChooseValue.textChanged.connect(self.stateUpdate)


    def openHelp(self):
        QtGui.QDesktopServices.openUrl(QUrl(HELP_URL))

    def flipFromTo(self):
        print "hello"
        self.stateUpdate()

    def showEvent(self, event):
        super(NetworkProfilerDialog, self).showEvent(event)
        # Trigger a recalc of everything the first time
        # Now autopopulate values if we can
        debugPrint("SHOW EVENT")
        self.handlerLayerChange()
        self.handlerSelectionChange()
        self.autoPopulate()

    def createProfile(self, event):
        """
        We instantiate the class and do basic pathfinding a bunch of different times before
        we actually save the file
        :param event:
        :return:
        """
        debugPrint("Run Event")
        selectedLayer = self.cmbLayer.itemData(self.cmbLayer.currentIndex())

        # What do I need to run the profiler
        obStartID = int(self.appSelectedObjects[0][0].id())

        theProfile = None
        try:
            self.theProfile = Profile(selectedLayer, msgcallback=self.setFromToStatus)
        except Exception as e:
            if theProfile is not None and theProfile.logmsgs is not None:
                detailstxt = "LOG:\n=====================\n  {0}\n\nException:\n=====================\n{1}".format("\n  ".join(theProfile.logmsgs), str(e))
                self.okDlg("ERROR:", infoText=str(e), detailsTxt=detailstxt, icon=QtGui.QMessageBox.Critical)
            else:
                detailstxt = "Exception:\n=====================\n{0}".format(str(e))
                self.okDlg("ERROR:", "A critical error occured.", detailsTxt=detailstxt, icon=QtGui.QMessageBox.Critical)
                return


        # TODO: None == All. This might need to be revisited
        if len(self.treeFields.selectedIndexes()) == 0:
            self.treeFields.selectAll()

    def saveProfile(self, event):
        """
        Write our file to nice outputs on the hard drive
        :param event:
        :return:
        """

        cols = [str(idx.data(0, Qt.DisplayRole)) for idx in self.treeFields.selectedItems()]

        # Now write to CSV
        try:
            outputdir = QtGui.QFileDialog.getSaveFileName(self, "Output File", "ProfileOutput.csv", "CSV File (*.csv);;All files (*)")

            #TODO: if dir exists prompt for overwrite
            #TODO: if dir doesn't exist, create it.

            # TODO: Output log file
            # - Details about when this was run. Inputs and outputs
            # - Details about the traversal.
            csvpath = os.path.join(outputdir, "profile.csv")
            logpath = os.path.join(outputdir, "profile.log")
            plotspath = os.path.join(outputdir, "plots")

            self.theProfile.writeCSV(self.txtCSVOutput.text(), cols)
            self.okDlg("Completed:", infoText="CSV file written: {}".format(self.txtCSVOutput.text()))

            plots = Plots(csvpath, plotspath)
            plots.createPlots()

            # Write a file with some information about what just happened
            with open(logpath, 'w') as f:
                f.write("Inputs:\n==========================================\n\n")

                f.write("Profile:\n==========================================\n\n")
                f.writelines(self.theProfile.logmsgs)
                f.write("Path:\n==========================================\n\n")
                f.writelines(self.theProfile.logmsgs)

        except Exception as e:
            detailstxt = "LOG:\n=====================\n  {0}\n\nException:\n=====================\n{1}".format("\n  ".join(theProfile.logmsgs), str(e))
            self.okDlg("ERROR:", infoText=str(e), detailsTxt=detailstxt, icon=QtGui.QMessageBox.Critical)


    def setFromToStatus(self, text="", color='black'):
        debugPrint("Set Label event")
        self.lblFromToStatus.setText(text)
        self.lblFromToStatus.setStyleSheet('QLabel { color: ' + color + ' }')

    def recalcVectorLayerFields(self):
        """
        Get current layer index and then repopulate the dropdowns accordingly
        :return:
        """
        debugPrint( "recalcVectorLayerFields")
        selLayerData = self.cmbLayer.itemData(self.cmbLayer.currentIndex())
        selLayerObj = None
        for obj in self.mapVectorLayers:
            if selLayerData == obj['layer']:
                selLayerObj = obj

        if selLayerObj is not None:
            self.treeFields.setEnabled(True)

            # Populate the list of fields to use
            self.treeFields.clear()
            for field in selLayerObj['fields']:
                # QTreeWidget / View
                row = [field.name(), ""]
                item = QtGui.QTreeWidgetItem(self.treeFields, row)

            # Select all by default.
            if len(self.treeFields.selectedIndexes()) == 0:
                self.treeFields.selectAll()

        else:
            self.treeFields.setEnabled(False)

    def recalcVectorLayers(self):
        """
        Rebuild the vector layers combo box and reset the selected item if necessary
        """
        debugPrint( "recalcVectorLayers")
        self.cmbLayer.clear()
        self.cmbLayer.currentIndexChanged.disconnect(self.cmbLayerChange)
        for layerObj in self.mapVectorLayers:
            self.cmbLayer.addItem(layerObj['layer'].name(), layerObj['layer'])
        self.cmbLayer.currentIndexChanged.connect(self.cmbLayerChange)

        idx = self.cmbLayer.currentIndex()
        if idx > 0:
            self.appVectorLayer = self.cmbLayer.itemData(idx)
            # if not in list then self.appVectorLayer = None
        else:
            self.setAppVectorLayerFromMap()

    def setAppVectorLayerFromMap(self):
        """
        Set the current map layer in the dropdown from whatever layer is selected on the map
        """
        debugPrint( "setAppVectorLayerFromMap")
        currLayer = self.mapCanvas.currentLayer()
        selMapLayerIndex = self.cmbLayer.findData(currLayer)

        if selMapLayerIndex > -1:
            self.cmbLayer.setCurrentIndex(selMapLayerIndex)
            # Set the selection independent of the control so if the map changes
            # we'll retain it.
            self.appSelectedLayer = self.cmbLayer.itemData(selMapLayerIndex)

    def getMapVectorLayerFields(self):
        """recalcReachValues each layer and identify the int fields
        as possible ID fields
        """
        debugPrint( "getMapVectorLayerFields")
        for layerObj in self.mapVectorLayers:
            allfields = []
            intfields = []
            for field in layerObj['layer'].fields().toList():
                allfields.append(field)
                if field.type() == QVariant.Int or \
                                field.type() == QVariant.Double:
                    intfields.append(field)
            layerObj['fields'] = allfields
            layerObj['idFields'] = intfields

    def recalcGoButton(self):
        """
        The ok button shouldn't allow bad behaviour
        :return:
        """
        enabled = True
        if self.cmbLayer.count() == 0 or self.cmbLayer.currentIndex() < 0:
            enabled = False
        if len(self.appSelectedObjects) == 0:
            enabled = False
        if len(self.treeFields.selectedIndexes()) == 0:
            enabled = False

        self.btnCreateProfile.setEnabled(enabled)

    def resetAppSelectedObjects(self):
        """
        Set the reach ID field in the UI
        """
        debugPrint( "recalcReachValues")
        self.appSelectedObjects = []
        if len(self.mapSelectedObjects) == 1:
            self.appSelectedObjects.append(self.mapSelectedObjects[0])

            treeroot = self.treeFields.invisibleRootItem()
            child_count = treeroot.childCount()
            for i in range(child_count):
                item = treeroot.child(i)
                fieldidx = self.mapSelectedObjects[0][0].fields().indexFromName(item.data(0, 0))
                if fieldidx > -1:
                    value = self.appSelectedObjects[0][0].attributes()[fieldidx]
                    if value is not None:
                        item.setData(1, Qt.DisplayRole, value)

    def recalcGrabButton(self):
        """
        Set the Grab button to be disabled for all but one case
        :return:
        """
        print "recalcGrabButton"
        self.cmdGetReachFromMap.setEnabled(False)
        if len(self.mapSelectedObjects) > 1:
            self.setFromToStatus(
                "You have {} features selected. To use the grab tool you must select only one.".format(
                    len(self.mapSelectedObjects)))
        elif len(self.mapSelectedObjects) == 0:
            self.setFromToStatus("You have 0 features selected. To use the grab tool you must select at least one.".format(
                len(self.mapSelectedObjects)))
        else:
            if len(self.appSelectedObjects) > 0 and self.mapSelectedObjects[0][0].id() == self.appSelectedObjects[0][0].id():
                self.setFromToStatus("Selected map object is captured above.")
            else:
                self.setFromToStatus("New reach selected. Use the Grab button to populate the fields above")
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
            debugPrint( "handlerLayerChange")
            # Get the data from the maps
            self.getMapVectorLayers()
            self.getMapVectorLayerFields()

            # Now repopulate the dropdowns
            self.recalcVectorLayers()

    def handlerSelectionChange(self):
        if self.isVisible():
            debugPrint( "handlerSelectionChange")
            self.getSelectedMapObjects()
            self.stateUpdate()

    def cmbLayerChange(self):
        if self.isVisible():
            debugPrint( "cmbLayerChange")
            self.recalcVectorLayerFields()
            self.getMapVectorLayerFields()
            self.stateUpdate()

    def autoPopulate(self, event):
        """
        This is the magic function that pulls values from the map selection
        :return:
        """

        # TODO: distinguish between from and to calls and do the right thing. If neither, try to do both

        debugPrint( "autoPopulate")
        self.setAppVectorLayerFromMap()
        self.recalcVectorLayerFields()
        self.resetAppSelectedObjects()
        self.stateUpdate()

    def stateUpdate(self):
        """
        This is the function that ripples through and updates the state of the UI
        :return:
        """
        debugPrint( "stateUpdate")
        self.recalcGrabButton()
        self.recalcBraidOptions()
        self.recalcFieldOptions()
        self.recalcGoButton()

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
            # Only add items that are on the currrent layer
            if layer['layer'] == self.mapCanvas.currentLayer():
                for feat in layer['layer'].selectedFeatures():
                    self.mapSelectedObjects.append((feat, layer['layer']))

    def getMapVectorLayers(self):
        self.mapVectorLayers = [{'layer':layer} for layer in self.mapCanvas.layers() if type(layer) is QgsVectorLayer]



def debugPrint(msg):
    """
    Just a little method to help us figure out what's going on (and in what ordeR)
    :param self:
    :param msg:
    :return:
    """
    if DEBUG:
        print "DEBUG: {}".format(msg)


