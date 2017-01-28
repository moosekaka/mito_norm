# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 16:05:18 2017

@author: swee lim
"""
import sys
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QFileDialog
from threads import getFileThread, normalizeThread

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
        self.dir_button.clicked.connect(self.getDirThreadClient)
        self.run_button.clicked.connect(self.normalizeThreadClient)
        self.run_button.setEnabled(False)
        self.paths = None
        self.datafolder = None

    def getDirThreadClient(self):
        self.datafolder = QFileDialog.getExistingDirectory(self, 'Folders')
        self.filethread = getFileThread(str(self.datafolder))
        self.filethread.signal.connect(self._update_dir_window)
        self.filethread.signal[dict].connect(self._getpaths)

        # key signals
        self.filethread.success.connect(self._onsuccess)
        self.filethread.failed.connect(self._onfailed)
        self.filethread.start()

        self.reset_button.setEnabled(True)
        self.reset_button.clicked.connect(self._reset)

    def _update_dir_window(self, text):
        self.dir_window.addItem(text)

    def _reset(self):
        self.dir_window.clear()
        self.dir_button.setEnabled(True)
        self.reset_button.setEnabled(False)
        self.run_button.setEnabled(False)

    def _getpaths(self, dicts):
        self.paths = dicts

    def _onsuccess(self):
        self.dir_button.setEnabled(False)
        self.run_button.setEnabled(True)

    def _onfailed(self):
        # placeholder for future actions if failed
        pass

    def normalizeThreadClient(self):
        self.normthread = normalizeThread(self.paths, self.datafolder)
        self.progress_bar.setMaximum(len(self.paths['skel']))
        self.progress_bar.setValue(0)
        self.stop_button.clicked.connect(self.normthread.stop)
        self.normthread.signal.connect(self._update_result_window)
        self.normthread.update_progress.connect(self._bar)

        # key signals
        self.normthread.finished.connect(self._done)
        self.normthread.interrupted.connect(self._interrupted)
        self.normthread.start()

        self.stop_button.setEnabled(True)

    def _update_result_window(self, text):
        self.results_window.addItem(text)

    def _bar(self):
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def _done(self):
        self.dir_button.setEnabled(True)
        self.run_button.setEnabled(False)
        QtGui.QMessageBox.information(self, "Finished", "Files Normalized!")

    def _interrupted(self):
        self.normthread.quit()
        self.normthread.wait()
        self.dir_button.setEnabled(True)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QtGui.QMessageBox.information(self, "Aborted",
                                      "Hit Run Again or Select new directory!")

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
