# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 14:06:59 2017

@author: sweel_Rafelski
"""

import os
import os.path as op
import re
import errno
from collections import defaultdict
from PyQt4.QtCore import QThread, SIGNAL
import functions as pf

SEARCHDICT = defaultdict(dict,
                         {'resampled': {'RFPstack': 'rfp',
                                        'GFPstack': 'gfp'},
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
    """
    Thread method to get paths for skeleton and resampled voxels VTK files
    """
    def __init__(self, folder):
        QThread.__init__(self)
        self.folder = folder

    def __del__(self):
        self.wait()

    def run(self):
        vtks = defaultdict(dict)

        for files in os.listdir(self.folder):
            if op.isfile(op.join(self.folder, files)):
                vtk_type = re.search(r'(skeleton|resampled)', files)
                channel_type = re.search(r'([GR]FPstack)\w?\d+', files)

                if vtk_type and channel_type:
                    cell_id = channel_type.string[:channel_type.end()].lower()
                    prefix = (SEARCHDICT.
                              get(vtk_type.group(1)).
                              get(channel_type.group(1)))

                    if prefix:  # if skeleton GFPstack do nothing
                        vtks[prefix][cell_id] = op.join(self.folder, files)

        for prefix in vtks:
            string = ('There are {1} VTK files found'
                      ' with prefix {0}').format(prefix,
                                                 len(vtks[prefix].keys()))
            self.emit(SIGNAL('printlog(QString)'), string)

        self.emit(SIGNAL('getpaths(PyQt_PyObject)'), vtks)


class writeVtkThread(QThread):
    """
    Thread method to for normalization of VTK files
    """
    def __init__(self, paths, savedir,
                 skel_prefix='skeleton',
                 ch1_prefix='gfp',
                 ch2_prefix='rfp'):
        QThread.__init__(self)
        self.paths = paths
        self.savedir = str(savedir)
        self.skel_prefix = skel_prefix
        self.ch1_prefix = ch1_prefix
        self.ch2_prefix = ch2_prefix

    def __del__(self):
        self.wait()

    def run(self):
        save_folder = op.join(self.savedir, 'Normalized')
        _mkdir_exist(save_folder)
        skels = self.paths[self.skel_prefix]  # dict of skeletons paths

        # note because skeleton key is based on ch2, re.sub() is needed to
        # get correct value for ch1 path
        for key, _ in sorted(skels.iteritems()):
            savename = op.join(save_folder,
                               'Norm_{}_skeleton.vtk'.format(key))

            data = pf.pt_cld_sclrs(self.paths[self.skel_prefix][key],
                                   (self.paths[self.ch1_prefix]
                                    [re.sub(self.ch2_prefix,
                                            self.ch1_prefix,
                                            key)]),
                                   self.paths[self.ch2_prefix][key],
                                   radius=2.5)
            dict_output = pf.normSkel(data)
            string1 = 'Saved as {}'.format(savename)
            self.emit(SIGNAL('beep(QString)'), string1)

            pf.writevtk(data, savename, **dict_output)

            self.emit(SIGNAL('update_progress()'))

        string2 = 'Finished Normalization of {} files'.format(len(skels))
        self.emit(SIGNAL('beep(QString)'), string2)
