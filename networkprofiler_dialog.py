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
import traceback

import qgis.utils
from PyQt4.QtCore import QVariant, Qt, QUrl
from qgis.core import *
from qgis.gui import *

from NetworkProfiler.debug import Debugger
from NetworkProfiler.profiler import Profile
from NetworkProfiler.plot import Plots
from NetworkProfiler.popupdialog import okDlg


HELP_URL = "https://github.com/Riverscapes/NetworkProfiler"
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'networkprofiler_dialog_base.ui'))

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
        self.appFromID = None
        self.appToID = None

        self.lblFrom.setText("")
        self.lblTo.setText("")

        # Braid choices are constant
        self.cmbPathChoose.clear()
        self.cmbPathChoose.addItem(Profile.CHOICE_SHORTEST)
        self.cmbPathChoose.addItem(Profile.CHOICE_FIELD_NOT_EMPTY)
        self.cmbPathChoose.addItem(Profile.CHOICE_FIELD_VALUE)
        self.cmbPathChoose.addItem(Profile.CHOICE_FIELD_NOT_VALUE)
        self.cmbPathChoose.currentIndexChanged.connect(self.recalcBraidRuleState)

        # Hook an event into the selection changed event to tell us if we can grab our object or not
        self.mapCanvas.layersChanged.connect(self.handleMapLayerChange)
        self.mapCanvas.selectionChanged.connect(self.handleMapSelectionChange)

        # Hook in a couple of control events for good measure
        self.cmbLayer.currentIndexChanged.connect(self.cmbLayerChange)

        # Set up our button events
        self.btnCreateProfile.clicked.connect(self.saveProfile)
        self.btnGrabFrom.clicked.connect(self.grabFrom)
        self.btnGrabTo.clicked.connect(self.grabTo)
        self.btnFlipFromTo.clicked.connect(self.flipFromTo)

        self.cmdButtons.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.close)
        self.cmdButtons.button(QtGui.QDialogButtonBox.Help).clicked.connect(self.actionOpenHelp)

        # When to recalc app state. Choose these carefully. They run a lot.
        self.cmbLayer.currentIndexChanged.connect(self.stateUpdate)
        self.cmbPathChoose.currentIndexChanged.connect(self.stateUpdate)
        self.cmbPathChooseField.currentIndexChanged.connect(self.stateUpdate)
        self.txtPathChooseValue.textChanged.connect(self.stateUpdate)

    def showEvent(self, event):
        debugPrint("showEvent")
        super(NetworkProfilerDialog, self).showEvent(event)
        self.loadPopulate()


    """
    
    Direct Actions caused by events like clicks    
    
    Actions trigger a downward cascade of effects
    
    """

    def loadPopulate(self, event=None):
        """
        This is the magic function that pulls values from the map selection
        when the form loads
        :return:
        """

        # TODO: distinguish between from and to calls and do the right thing. If neither, try to do both

        debugPrint( "loadPopulate")
        self.appFromID = None
        self.appToID = None
        self.handleMapLayerChange(True)
        self.handleMapSelectionChange()
        self.setAppVectorLayerFromMap()
        self.recalcVectorLayerFields()
        self.resetAppSelectedObjects()
        self.recalcBraidRuleState()
        self.stateUpdate()

    def cmbLayerChange(self):
        if self.isVisible():

            debugPrint( "cmbLayerChange")

            self.recalcVectorLayerFields()
            self.getMapVectorLayerFields()
            self.createProfile()
            self.appFromID = None
            self.appToID = None
            self.updateReachLabels()

    def resetFromTo(self):
        debugPrint("resetFromTo")
        self.appFromID = None
        self.appToID = None
        self.theProfile = None
        self.updateReachLabels()

    def grabFrom(self):
        debugPrint("grabFrom")
        self.appFromID = self.mapSelectedObjects[0][0].id()
        self.runProfile()
        self.updateReachLabels()

    def grabTo(self):
        debugPrint("grabTo")
        self.appToID = self.mapSelectedObjects[0][0].id()
        self.runProfile()
        self.updateReachLabels()

    def flipFromTo(self):
        debugPrint("flipFromTo")
        fromID = self.appFromID
        toID = self.appToID

        self.appFromID = toID
        self.appToID = fromID

        self.runProfile()

        self.updateReachLabels()

    def actionOpenHelp(self):
        QtGui.QDesktopServices.openUrl(QUrl(HELP_URL))

    """
    
    Indirect and biproduct actions
    
    """

    def handleMapSelectionChange(self):
        """
        Triggered when the map selection changes
        :return:
        """
        if self.isVisible():
            debugPrint( "handleMapSelectionChange")
            self.getSelectedMapObjects()
            self.stateUpdate()

    def handleMapLayerChange(self, force=False):
        """
        Triggered when new layers are added or removed from the map
        :return:
        """
        if self.isVisible() or force:
            debugPrint( "handleMapLayerChange")
            # Get the data from the maps
            self.getMapVectorLayers()
            self.getMapVectorLayerFields()

            # Now repopulate the dropdowns
            self.recalcVectorLayers()

    def updateReachLabels(self):
        debugPrint("updateReachLabels")
        self.lblFrom.setText("ID: {}".format(self.appFromID))
        self.lblTo.setText("ID: {}".format(self.appToID))


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

    def recalcBraidRuleState(self):
        """
        The braid choices are a little logic-y so we need to enable/disable some of the controls
        :return:
        """
        debugPrint("recalcBraidRuleState")
        currentSelection = self.cmbPathChoose.currentText()

        txtPathChooseValue = currentSelection == Profile.CHOICE_FIELD_NOT_VALUE or currentSelection == Profile.CHOICE_FIELD_VALUE
        cmbPathChooseField = currentSelection != Profile.CHOICE_SHORTEST

        # Only change things if we need to
        if self.txtPathChooseValue.isHidden() == txtPathChooseValue:
            self.txtPathChooseValue.setEnabled(txtPathChooseValue)
            self.lblPathChooseValue.setEnabled(txtPathChooseValue)

            self.txtPathChooseValue.setHidden(not txtPathChooseValue)
            self.lblPathChooseValue.setHidden(not txtPathChooseValue)

        if self.cmbPathChooseField.isHidden() == cmbPathChooseField:
            self.cmbPathChooseField.setEnabled(cmbPathChooseField)
            self.lblPathChooseField.setEnabled(cmbPathChooseField)

            self.cmbPathChooseField.setHidden(not cmbPathChooseField)
            self.lblPathChooseField.setHidden(not cmbPathChooseField)


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

        # Now add tree objects for each field
        # Also populate the field dropdown in the path chooser
        if selLayerObj is not None:
            self.treeFields.setEnabled(True)

            # Populate the list of fields to use
            self.treeFields.clear()
            self.cmbPathChooseField.clear()
            for field in selLayerObj['fields']:
                # QTreeWidget / View
                row = [field.name(), "", ""]
                item = QtGui.QTreeWidgetItem(self.treeFields, row)
                self.cmbPathChooseField.addItem(field.name())

            # Select all by default.
            if len(self.treeFields.selectedIndexes()) == 0:
                self.treeFields.selectAll()

        else:
            self.treeFields.setEnabled(False)

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
        debugPrint("recalcGoButton")
        enabled = True
        if self.cmbLayer.count() == 0 or self.cmbLayer.currentIndex() < 0:
            enabled = False
        if self.appFromID is None or self.appToID is None:
            enabled = False
        if len(self.treeFields.selectedIndexes()) == 0:
            enabled = False

        self.btnCreateProfile.setEnabled(enabled)

    def resetAppSelectedObjects(self):
        """
        Set the reach ID field in the UI
        """
        debugPrint("resetAppSelectedObjects")
        if self.appFromID is None and len(self.mapSelectedObjects) > 0:
            self.appFromID = self.mapSelectedObjects[0][0].id()

        if self.appToID is None and len(self.mapSelectedObjects) > 1:
            self.appToID = self.mapSelectedObjects[1][0].id()

        self.runProfile()
        self.updateReachLabels()


    def recalcFieldOptions(self):
        debugPrint("recalcFieldOptions")


    def recalcGrabButtons(self):
        """
        Set the Grab button to be disabled for all but one case
        :return:
        """
        debugPrint("recalcGrabButtons")
        self.btnGrabFrom.setEnabled(False)
        self.btnGrabTo.setEnabled(False)

        if len(self.mapSelectedObjects) > 1:
            self.setFromToMsg(
                "You have {} features selected. To use the grab tool you must select only one.".format(len(self.mapSelectedObjects)))

        elif len(self.mapSelectedObjects) == 0:
            self.setFromToMsg("You have 0 features selected. To use the grab tool you must select at least one.".format(
                len(self.mapSelectedObjects)))
        else:
            if self.appFromID is None or self.mapSelectedObjects[0][0].id() != self.appFromID:
                self.btnGrabFrom.setEnabled(True)

            if self.appToID is None or self.mapSelectedObjects[0][0].id() != self.appToID:
                self.btnGrabTo.setEnabled(True)


    def stateUpdate(self):
        """
        This is the function that ripples through and updates the state of the UI
        :return:
        """
        debugPrint( "stateUpdate")
        self.recalcGrabButtons()
        self.recalcFieldOptions()
        self.recalcGoButton()


    """
    
    Profile functions to do with the profile class
    
    """


    def createProfile(self):
        """
        The create profile transforms the SHP file into a networkX object for future
        processing
        :param event:
        :return:
        """
        debugPrint("Create profile")
        selectedLayer = self.cmbLayer.itemData(self.cmbLayer.currentIndex())

        self.theProfile = None

        try:
            self.theProfile = Profile(selectedLayer, msgcallback=self.setFromToMsg)
        except Exception as e:
            if self.theProfile is not None and self.theProfile.metalogs is not None:
                detailstxt = "LOG:\n=====================\n  {0}\n\nException:\n=====================\n{1}".format("\n  ".join(self.theProfile.metalogs), str(e))
                okDlg("ERROR:", infoText=str(e), detailsTxt=detailstxt, icon=QtGui.QMessageBox.Critical)
            else:
                detailstxt = "Exception:\n=====================\n{0}".format(str(e))
                okDlg("ERROR:", "A critical error occured.", detailsTxt=detailstxt, icon=QtGui.QMessageBox.Critical)
                return
            self.resetFromTo()


    def runProfile(self):
        """
        Run profile does the pathfinding and reports back
        We do basic pathfinding a bunch of different times before
        we actually save the file. We may do this multiple times so it makes sense for this
        to be as fast as humanly possible
        :param event:
        :return:
        """

        try:
            if self.appFromID is not None:
                debugPrint("runProfile")

                if self.theProfile is None:
                    self.createProfile()

                self.theProfile.pathfinder(self.appFromID, self.appToID)
                newToID = self.theProfile.getToID()

                noOutflowStr = ""
                if self.appToID is None and newToID is not None:
                    self.appToID = newToID
                    noOutflowStr = "'To' point was discovered and "

                self.updateReachLabels()
                if len(self.theProfile.paths) > 0:
                    msg = "{}at least one path was found between 'from' and 'to' points.".format(noOutflowStr)
                    self.setFromToMsg(msg[0].upper() + msg[1:])
                else:
                    self.setFromToMsg("No path found between 'From' and 'To' point.", 'red')

        except Exception as e:
            traceback.print_exc()
            self.setFromToMsg("No path found between 'From' and 'To' point.", 'red')

    def saveProfile(self):
        """
        Write our file to nice outputs on the hard drive
        :param event:
        :return:
        """

        if len(self.treeFields.selectedIndexes()) == 0:
            self.treeFields.selectAll()

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
            okDlg("Completed:", infoText="CSV file written: {}".format(self.txtCSVOutput.text()))

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
            traceback.print_exc()
            detailstxt = "LOG:\n=====================\n  {0}\n\nException:\n=====================\n{1}".format("\n  ".join(self.theProfile.logmsgs), str(e))
            okDlg("ERROR:", infoText=str(e), detailsTxt=detailstxt, icon=QtGui.QMessageBox.Critical)


    """
    
    Helper Functions
    
    """

    def setFromToMsg(self, text="", color='black'):
        """
        Give us some helpful text about grabbing map objects
        :param text:
        :param color:
        :return:
        """
        debugPrint("Set Label event")
        self.lblFromToStatus.setText(text)
        self.lblFromToStatus.setStyleSheet('QLabel { color: ' + color + ' }')

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


    def getSelectedMapObjects(self):
        """
        Get a helpful list of selected objects on the map
        :return:
        """
        debugPrint("getSelectedMapObjects")
        self.mapSelectedObjects = []
        for layer in self.mapVectorLayers:
            # Only add items that are on the currrent layer
            if layer['layer'] == self.mapCanvas.currentLayer():
                for feat in layer['layer'].selectedFeatures():
                    self.mapSelectedObjects.append((feat, layer['layer']))

    def getMapVectorLayers(self):
        debugPrint("getMapVectorLayers")
        self.mapVectorLayers = [{'layer':layer} for layer in self.mapCanvas.layers() if type(layer) is QgsVectorLayer]


def debugPrint(msg):
    """
    Just a little method to help us figure out what's going on (and in what ordeR)
    :param self:
    :param msg:
    :return:
    """
    if Debugger.DEBUG is True:
        print "DEBUG: {}".format(msg)


