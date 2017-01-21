# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 14:06:59 2017

@author: sweel_Rafelski
"""

import os
import os.path as op
import re
from collections import defaultdict
from PyQt4.QtCore import QThread, SIGNAL
import errno
import functions as pf

SEARCHDICT = defaultdict(dict,
                         {'resampled': {'RFPstack': 'rfp_vol',
                                        'GFPstack': 'gfp_vol'},
                          'skeleton': {'RFPstack': 'skeleton'}})


def _mkdir_exist(path):
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
            if op.isfile(op.join(self.folder, files)):
                vtk_type = channel_type = None  # must be initiliazed
                for match in re.finditer(r'(skeleton|resampled)', files):
                    vtk_type = match.group()
                for match in re.finditer(r'[RG]FPstack', files):
                    channel_type = match.group()
                    cell_id = files[:match.end()]

                if vtk_type and channel_type:  # if both is not None
                    # return None if its a skeleton of GFP type
                    prefix = SEARCHDICT.get(vtk_type).get(channel_type)
                    if prefix is not None:
                        vtks[prefix][cell_id] = op.join(self.folder, files)
        for prefix in vtks:
            string = ('There are {1} VTK files found'
                      ' with prefix {0}').format(prefix,
                                                 len(vtks[prefix].keys()))
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
        save_folder = op.join(self.savedir, 'Normalized')
        skels = self.paths['skeleton']
        gfp = self.paths['gfp_vol']
        rfp = self.paths['rfp_vol']
        _mkdir_exist(save_folder)

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
