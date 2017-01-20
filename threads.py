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
import errno
import cPickle as pickle
import pipefuncs as pf


def mkdir_exist(path):
    """
    Makes a folder if it does not already exists
    """
    try:
        os.makedirs(path)
        print "{} created!".format(path)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise


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
        save_folder= op.join(self.savedir, 'Normalized')
        skels = self.paths['skeleton']
        gfp = self.paths['gfp_vol']
        rfp = self.paths['rfp_vol']
        mkdir_exist(save_folder)

        for key, _ in sorted(skels.iteritems()):

            savename = op.join(save_folder,
                               'Norm_{}_skeleton.vtk'.format(key))

            data = pf.pt_cld_sclrs(skels[key],
                                   gfp[key.replace('RFP', 'GFP')],
                                   rfp[key],
                                   radius=2.5)
            (a, b, c, d, e) = pf.normSkel(data)
            string1 = 'Saved as {}'.format(savename)
            self.emit(SIGNAL('beep(QString)'), string1)

            # these are the labels used to name the outputs above
            calc = {'norm_scaled': a,
                    'norm_unscaled': b,
                    'background_sub_ch1': c,
                    'background_sub_ch2': d,
                    'width_equivalent': e}
            pf.writevtk(data, savename, **calc)

            self.emit(SIGNAL('update_progress()'))

        string2 = 'Finished Normalization of {} files'.format(len(skels))
        self.emit(SIGNAL('beep(QString)'), string2)

