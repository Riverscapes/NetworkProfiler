from PyQt4 import QtGui


def okDlg(txt, infoText="", detailsTxt=None, icon=QtGui.QMessageBox.Information):
    """
    Call it like this:
        self.okDlg("ERROR:", infoText=str(e), detailsTxt=detailstxt, icon=QtGui.QMessageBox.Critical)
    :param self:
    :param txt:
    :param infoText:
    :param detailsTxt:
    :param icon:
    :return:
    """

    # Just a helper box to display an OK dialog prompt.
    msg = QtGui.QMessageBox()
    msg.setIcon(icon)

    msg.setText(txt)
    msg.setInformativeText(infoText)
    msg.setWindowTitle("Riverscapes Toolbar")
    if detailsTxt is not None:
        msg.setDetailedText(detailsTxt)
    msg.setStandardButtons(QtGui.QMessageBox.Ok)
    msg.buttonClicked.connect(msg.close)

    # This is a hack to be able to resize the box
    horizontal_spacer = QtGui.QSpacerItem(500, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    layout = msg.layout()
    layout.addItem(horizontal_spacer, layout.rowCount(), 0, 1, layout.columnCount())

    msg.exec_()