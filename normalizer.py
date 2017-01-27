# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 16:05:18 2017

@author: sweel_Rafelski
"""
import sys
from PyQt4 import QtGui, uic
from PyQt4.QtCore import QThread, pyqtSlot, QObject
from PyQt4.QtGui import QFileDialog
from threads import getfilesWorker, normWorker

qtCreatorFile = "normalizer.ui"  # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    """
    GUI for mitograph output normalizer
    """
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.dir_button.clicked.connect(self.getDirThread)
        self.run_button.clicked.connect(self.normalizeThread)
        self.run_button.setEnabled(False)
        self.paths = None
        self.datafolder = None

    def getDirThread(self):
        self.filethread = QThread()

        self.datafolder = QFileDialog.getExistingDirectory(self, 'Folders')
        self.worker = getfilesWorker(str(self.datafolder))
        self.worker.moveToThread(self.filethread)
        self.worker.signal.connect(self._updatedir)
        self.worker.signal[dict].connect(self._getpaths)

        # key signals
        self.worker.finished.connect(self._filedone)
        self.filethread.started.connect(self.worker.work)
        self.filethread.start()

        self.reset_button.setEnabled(True)
        self.reset_button.clicked.connect(self._reset)

    def _updatedir(self, text):
        self.dir_window.addItem(text)

    def _reset(self):
        self.dir_window.clear()
        self.dir_button.setEnabled(True)
        self.reset_button.setEnabled(False)
        self.run_button.setEnabled(False)

    def _getpaths(self, dicts):
        self.paths = dicts

    def _filedone(self):
        self.filethread.quit()
        self.dir_button.setEnabled(False)
        self.run_button.setEnabled(True)

    def normalizeThread(self):
        self.runthread = QThread(self)
        self.worker2 = normWorker(self.paths, self.datafolder)
        self.worker2.moveToThread(self.runthread)
        self.progress_bar.setMaximum(len(self.paths['skel']))
        self.progress_bar.setValue(0)
        self.stop_button.clicked.connect(self.worker2.stop)
        self.worker2.signal.connect(self._report)
        self.worker2.update_progress.connect(self._bar)

        # key signals
        self.worker2.finished.connect(self._done)
        self.worker2.interrupted.connect(self._interrupted)
        self.runthread.started.connect(self.worker2.work)
        self.runthread.start()

        self.stop_button.setEnabled(True)

    def _report(self, text):
        self.results_window.addItem(text)

    def _bar(self):
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def _done(self):
        self.runthread.quit()
        self.dir_button.setEnabled(True)
        self.run_button.setEnabled(False)
        QtGui.QMessageBox.information(self, "Finished", "Files Normalized!")

    def _interrupted(self):
        self.runthread.quit()
        self.dir_button.setEnabled(True)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QtGui.QMessageBox.information(self, "Not Finished",
                                      "Hit Run Again or Select new directory!")

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
