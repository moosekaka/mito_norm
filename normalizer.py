# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 16:05:18 2017

@author: sweel_Rafelski
"""
import os
import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QThread, SIGNAL

from PyQt4.QtGui import QFileDialog
import write_raw_vtk as wvtk
from threads import getFilesThread, writeVtkThread
from collections import defaultdict



qtCreatorFile = "normalizer.ui" # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.dir_button.clicked.connect(self.selectDir)
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self.runmain)
        self.paths = None
        self.datafolder = None
#        self.folder = QFileDialog()
#        self.folder.currentChanged.connect(lambda: self.printlog(self.fpath))

    def selectDir(self):
        self.datafolder = QtGui.QFileDialog.getExistingDirectory(self,
                                                                 'Folders')
        self.file_thread = getFilesThread(str(self.datafolder))
        self.connect(self.file_thread, SIGNAL("printlog(QString)"), self.updatedir)
        self.connect(self.file_thread, SIGNAL("getpaths(PyQt_PyObject)"), self.getpaths)
        self.connect(self.file_thread, SIGNAL("finished()"), self.filedone)
        self.file_thread.start()

#
    def updatedir(self, text):
        self.dir_window.addItem(text)

    def getpaths(self, dicts):
        self.paths = dicts

    def runmain(self):
        self.progress_bar.setMaximum(len(self.paths['skeleton']))
        self.progress_bar.setValue(0)

        self.run_thread = writeVtkThread(self.paths, self.datafolder)
        self.connect(self.run_thread, SIGNAL("beep(QString)"), self.report)
        self.connect(self.run_thread, SIGNAL("update_progress()"), self.bar)
        self.run_thread.finished.connect(self.done)
        self.run_thread.start()

    def report(self, text):
        self.results_window.addItem(text)

    def bar(self):
        self.progress_bar.setValue(self.progress_bar.value()+ 1)

    def filedone(self):
        self.dir_button.setEnabled(False)
        self.run_button.setEnabled(True)

    def done(self):
        self.dir_button.setEnabled(True)
        self.run_button.setEnabled(False)
        QtGui.QMessageBox.information(self, "Finished", "Files Normalized!")

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
