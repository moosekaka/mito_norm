# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 14:06:59 2017

@author: sweel_Rafelski
"""

import os
import os.path as op
import re
import time
import errno
from collections import defaultdict
from PyQt4.QtCore import QThread, QObject, pyqtSlot, pyqtSignal
from PyQt4.QtGui import qApp
import functions as pf

# hash table for sorting and labeling the various VTK file type paths
SEARCHDICT = defaultdict(dict,
                         {'resampled': {'RFPstack': 'rfp',
                                        'GFPstack': 'gfp'},
                          'skeleton': {'RFPstack': 'skel'}})


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


class getfilesWorker(QObject):
    """
    Thread method to get paths for skeleton and resampled voxels VTK files
    """
    signal = pyqtSignal([str], [dict])
    finished = pyqtSignal()

    def __init__(self, folder):
        super(getfilesWorker, self).__init__()
        self.folder = folder

    @pyqtSlot()
    def work(self):
        vtks = defaultdict(dict)

        for files in os.listdir(self.folder):
            if op.isfile(op.join(self.folder, files)):
                vtk_type = re.search(r'(skeleton|resampled)', files)
                channel_type = re.search(r'([GR]FPstack)\w?\d+', files)

                if vtk_type and channel_type:
                    # this will be the unique ID for each cell
                    cell_id = channel_type.string[:channel_type.end()].lower()
                    # this is just used to determine which type of VTK file
                    # (ie skeleton or voxel/channel file to use)
                    prefix = (SEARCHDICT.
                              get(vtk_type.group(1)).
                              get(channel_type.group(1)))

                    # if no prefix found, means skeleton.vtk is based on
                    # ch1 which is not what we want
                    if prefix:
                        vtks[prefix][cell_id] = op.join(self.folder, files)

        for prefix in vtks:
            string = ('There are {1} VTK files found'
                      ' with prefix {0}').format(prefix,
                                                 len(vtks[prefix].keys()))
            self.signal.emit(string)

        self.signal[dict].emit(vtks)
        self.finished.emit()


class normWorker(QObject):
    signal = pyqtSignal(str)
    finished = pyqtSignal()
    interrupted = pyqtSignal()
    update_progress = pyqtSignal()

    def __init__(self, paths, savedir,
                 skel_prefix='skel',
                 ch1_prefix='gfp',
                 ch2_prefix='rfp'):
        super(normWorker, self).__init__()
        self.flag = True
        self.paths = paths
        self.savedir = str(savedir)
        self.skel_prefix = skel_prefix
        self.ch1_prefix = ch1_prefix
        self.ch2_prefix = ch2_prefix

    @pyqtSlot()
    def work(self):
        save_folder = op.join(self.savedir, 'Normalized')
        _mkdir_exist(save_folder)
        skels = self.paths[self.skel_prefix]  # dict of skeletons paths
        keys = skels.keys()

        while keys and self.flag:
            key = keys.pop()
            savename = op.join(save_folder,
                               'Normalized_{}_mitoskel.vtk'.format(key))

            # note because skeleton key is based on ch2, re.sub() is needed to
            # get correct value for ch1 path
            data, v1, v2 = pf.point_cloud_scalars(
                self.paths[self.skel_prefix][key],
                self.paths[self.ch1_prefix][re.sub(self.ch2_prefix,
                                                   self.ch1_prefix, key)],
                self.paths[self.ch2_prefix][key],
                radius=2.5)
            dict_output = pf.normalize_skel(data, v1, v2)
            pf.write_vtk(data, savename, **dict_output)

            # report worker status to main GUI
            string1 = 'Saved as {}'.format(savename)
            self.signal[str].emit(string1)
            self.update_progress.emit()
            qApp.processEvents()

        if not keys:
            string2 = 'Finished Normalization of {} files'.format(len(skels))
            self.signal.emit(string2)
            self.finished.emit()
        else:
            string2 = 'Failed!'
            self.interrupted.emit()

    @pyqtSlot()
    def stop(self):
        print "Process Halted"
        self.flag = False
