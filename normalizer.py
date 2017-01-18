# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 16:05:18 2017

@author: sweel_Rafelski
"""
import os
import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import QFileDialog
import write_raw_vtk as wvtk



qtCreatorFile = "normalizer.ui" # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.dir_button.clicked.connect(self.selectDir)
        self.run_button.clicked.connect(self.runmain)

    def selectDir(self):
        dirpath = QFileDialog.getExistingDirectory(self, 'Select Dir of Files')

        os.chdir(str(dirpath))
        self.dir_window.setText('dir changed to ' + dirpath)

    def runmain(self):
        wvtk.main()
        self.results_window.setText('Finished!')

#    def CalculateTax(self):
#        price = int(self.price_box.toPlainText())
#        tax = (self.tax_rate.value())
#        total_price = price  + ((tax / 100.) * price)
#        total_price_string = ("The total price with tax is: " +
#                              str(total_price))
#        self.results_window.setText(total_price_string)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
