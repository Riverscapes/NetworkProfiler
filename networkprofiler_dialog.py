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
from PyQt4.QtCore import QVariant, Qt, QUrl
from profiler import Profile
from . import DEBUG
from qgis.core import *
from qgis.gui import *
import qgis.utils

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
        self.ctlLayer.currentIndexChanged.connect(self.ctlLayerChange)

        # Set up our button events
        self.cmdBrowseCSV.clicked.connect(lambda: self.save_csv_dialog(self.txtCSVOutput))
        self.cmdGetReachFromMap.clicked.connect(self.autoPopulate)

        self.btnCreateProfile.clicked.connect(self.runProfilerAction)
        self.cmdButtons.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.close)
        self.cmdButtons.button(QtGui.QDialogButtonBox.Help).clicked.connect(self.openHelp)

        # When to recalc app state. Choose these carefully. They run a lot.
        self.treeFields.itemSelectionChanged.connect(self.stateUpdate)
        self.txtCSVOutput.textChanged.connect(self.stateUpdate)
        self.ctlLayer.currentIndexChanged.connect(self.stateUpdate)

        # DEBUG: Just set some default values for now
        if DEBUG:
            self.txtCSVOutput.setText("/Users/work/Desktop/TEST.csv")

    def showEvent(self, event):
        super(NetworkProfilerDialog, self).showEvent(event)
        # Trigger a recalc of everything the first time
        # Now autopopulate values if we can
        debugPrint("SHOW EVENT")
        self.handlerLayerChange()
        self.handlerSelectionChange()
        self.autoPopulate()

    def runProfilerAction(self, event):
        """
        Here's where we call the actual tool
        :param event:
        :return:
        """
        debugPrint("Run Event")
        selectedLayer = self.ctlLayer.itemData(self.ctlLayer.currentIndex())

        # What do I need to run the profiler
        obStartID = int(self.appSelectedObjects[0][0].id())

        theProfile = None
        try:
            theProfile = Profile(selectedLayer, obStartID, debug=DEBUG, msgcallback=self.setLabelMsg)
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

        cols = [str(idx.data(0, Qt.DisplayRole)) for idx in self.treeFields.selectedItems()]

        # Now write to CSV
        try:
            theProfile.writeCSV(self.txtCSVOutput.text(), cols)
            self.okDlg("Completed:", infoText="CSV file written: {}".format(self.txtCSVOutput.text()))
        except Exception as e:
            detailstxt = "LOG:\n=====================\n  {0}\n\nException:\n=====================\n{1}".format("\n  ".join(theProfile.logmsgs), str(e))
            self.okDlg("ERROR:", infoText=str(e), detailsTxt=detailstxt, icon=QtGui.QMessageBox.Critical)

    def setLabelMsg(self, text="", color='black'):
        debugPrint("Set Label event")
        self.lblWarning.setText(text)
        self.lblWarning.setStyleSheet('QLabel { color: ' + color + ' }')

    def recalcVectorLayerFields(self):
        """
        Get current layer index and then repopulate the dropdowns accordingly
        :return:
        """
        debugPrint( "recalcVectorLayerFields")
        selLayerData = self.ctlLayer.itemData(self.ctlLayer.currentIndex())
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
        debugPrint( "setAppVectorLayerFromMap")
        currLayer = self.mapCanvas.currentLayer()
        selMapLayerIndex = self.ctlLayer.findData(currLayer)

        if selMapLayerIndex > -1:
            self.ctlLayer.setCurrentIndex(selMapLayerIndex)
            # Set the selection independent of the control so if the map changes
            # we'll retain it.
            self.appSelectedLayer = self.ctlLayer.itemData(selMapLayerIndex)

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
        if self.ctlLayer.count() == 0 or self.ctlLayer.currentIndex() < 0:
            enabled = False
        if len(self.appSelectedObjects) == 0:
            enabled = False
        if len(self.txtCSVOutput.text()) == 0:
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
            self.setLabelMsg(
                "You have {} features selected. To use the grab tool you must select only one.".format(
                    len(self.mapSelectedObjects)))
        elif len(self.mapSelectedObjects) == 0:
            self.setLabelMsg("You have 0 features selected. To use the grab tool you must select at least one.".format(
                len(self.mapSelectedObjects)))
        else:
            if len(self.appSelectedObjects) > 0 and self.mapSelectedObjects[0][0].id() == self.appSelectedObjects[0][0].id():
                self.setLabelMsg("Selected map object is captured above.")
            else:
                self.setLabelMsg("New reach selected. Use the Grab button to populate the fields above")
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

    def ctlLayerChange(self):
        if self.isVisible():
            debugPrint( "ctlLayerChange")
            self.recalcVectorLayerFields()
            self.getMapVectorLayerFields()
            self.stateUpdate()

    def autoPopulate(self):
        """
        This is the magic function that pulls values from the map selection
        :return:
        """
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

    """
    Dialog Boxes
    """

    def save_csv_dialog(self, txtControl):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Output File", "ProfileOutput.csv", "CSV File (*.csv);;All files (*)")
        txtControl.setText(filename)

    def okDlg(self, txt, infoText="", detailsTxt=None, icon=QtGui.QMessageBox.Information):
        msg = QtGui.QMessageBox()
        msg.setIcon(icon)

        msg.setText(txt)
        msg.setInformativeText(infoText)
        msg.setWindowTitle("Network Profiler")
        if detailsTxt is not None:
            msg.setDetailedText(detailsTxt)
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        msg.buttonClicked.connect(msg.close)

        # This is a hack to be able to resize the box
        horizontal_spacer = QtGui.QSpacerItem(500, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        layout = msg.layout()
        layout.addItem(horizontal_spacer, layout.rowCount(), 0, 1, layout.columnCount())

        msg.exec_()

    def openHelp(self):
        QtGui.QDesktopServices.openUrl(QUrl(HELP_URL))


def debugPrint(msg):
    """
    Just a little method to help us figure out what's going on (and in what ordeR)
    :param self:
    :param msg:
    :return:
    """
    if DEBUG:
        print "DEBUG: {}".format(msg)


