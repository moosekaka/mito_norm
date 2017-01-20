# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 14:06:59 2017

@author: sweel_Rafelski
"""

from PyQt4.QtCore import QThread, SIGNAL
import os
import os.path as op
from collections import defaultdict
import fnmatch
import traceback
import cPickle as pickle
import cPickle as pickle
import pipefuncs as pf
import sys


class getFilesThread(QThread):


    def __init__(self, folder):
        QThread.__init__(self)
        self.folder = folder

    def __del__(self):
        self.wait()


    def run(self):
        vtks = defaultdict(dict)
        for files in os.listdir(self.folder):
            if fnmatch.fnmatch(files, '*RFP*skeleton.vtk'):
                vtks['skeleton'][files[:-13]] = op.join(self.folder, files)
            if fnmatch.fnmatch(files, '*RFP*resampled.vtk'):
                vtks['rfp_vol'][files[:-14]] = op.join(self.folder, files)
            if fnmatch.fnmatch(files, '*GFP*resampled.vtk'):
                vtks['gfp_vol'][files[:-14]] = op.join(self.folder, files)

        for keys in vtks:
            string = ('There are {1} VTK files found'
                      ' with prefix {0}').format(keys, len(vtks[keys]))
            self.emit(SIGNAL('printlog(QString)'), string)

        self.emit(SIGNAL('getpaths(PyQt_PyObject)'), vtks)


class writeVtkThread(QThread):
    def __init__(self, paths, savedir):
        QThread.__init__(self)
        self.paths = paths
        self.savedir = str(savedir)

    def __del__(self):
        self.wait()

    def run(self):
        skels = self.paths['skeleton']
        gfp = self.paths['gfp_vol']
        rfp = self.paths['rfp_vol']

        for key, _ in sorted(skels.iteritems()):
            string1 = 'Finished Normalization for {}'.format(key)

            savename = op.join(self.savedir, 'Normalized',
                               'Norm_{}_skeleton.vtk'.format(key))
            string2 = 'Saved as {}'.format(savename)

            data = pf.pt_cld_sclrs(skels[key],
                                   gfp[key.replace('RFP', 'GFP')],
                                   rfp[key],
                                   radius=2.5)
            (a, b, c, d, e) = pf.normSkel(data)
            self.emit(SIGNAL('normsig(QString)'), string1)
#
            # these are the labels used to name the outputs above
            calc = {'norm_scaled': a,
                    'norm_unscaled': b,
                    'background_sub_ch1': c,
                    'background_sub_ch2': d,
                    'width_equivalent': e}
            pf.writevtk(data, savename, **calc)

            self.emit(SIGNAL('savedsig(QString)'), string2)
            self.emit(SIGNAL('update()'))
