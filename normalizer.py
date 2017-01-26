# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 16:05:18 2017

@author: sweel_Rafelski
"""
import sys
from PyQt4 import QtGui, uic
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QFileDialog
from threads import getFilesThread, writeVtkThread

qtCreatorFile = "normalizer.ui"  # Enter file here.
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

    def selectDir(self):
        self.datafolder = QFileDialog.getExistingDirectory(self,
                                                           'Folders')
        self.file_thread = getFilesThread(str(self.datafolder))
        self.connect(self.file_thread,
                     SIGNAL("printlog(QString)"),
                     self._updatedir)
        self.connect(self.file_thread,
                     SIGNAL("getpaths(PyQt_PyObject)"),
                     self._getpaths)
        self.file_thread.finished.connect(self._filedone)

        self.file_thread.start()  # not run()!!

        self.reset_button.setEnabled(True)
        self.reset_button.clicked.connect(self._reset)

    def _updatedir(self, text):
        self.dir_window.addItem(text)

    def _reset(self):
        self.file_thread.terminate()
        self.dir_window.clear()
        self.dir_button.setEnabled(True)
        self.reset_button.setEnabled(False)
        self.run_button.setEnabled(False)

    def _getpaths(self, dicts):
        self.paths = dicts

    def runmain(self):
        self.progress_bar.setMaximum(len(self.paths['skel']))
        self.progress_bar.setValue(0)
        self.run_thread = writeVtkThread(self.paths, self.datafolder)
        self.connect(self.run_thread, SIGNAL("beep(QString)"), self._report)
        self.connect(self.run_thread, SIGNAL("update_progress()"), self._bar)
        self.connect(self.run_thread, SIGNAL("Abort(QString)"), self._cleanup)
        self.stop_button.clicked.connect(self._stopthread)
        self.run_thread.finished.connect(self._done)

        self.run_thread.start()  # not run()!!

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.stop_button.clicked.connect(self.run_thread.quit)

    def _stopthread(self):
        self.run_thread.flag = False

    def _cleanup(self, text):
        self.progress_bar.setValue(0)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.results_window.addItem(text)

    def _report(self, text):
        self.results_window.addItem(text)

    def _bar(self):
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def _filedone(self):
        self.dir_button.setEnabled(False)
        self.run_button.setEnabled(True)

    def _abort(self):
        self.run_thread.exit(1)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QtGui.QMessageBox.information(self, "Aborted!",
                                      "Press run to try again!")

    def _done(self):
        self.dir_button.setEnabled(True)
        self.run_button.setEnabled(False)
        QtGui.QMessageBox.information(self, "Finished", "Files Normalized!")

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
