# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 14:06:59 2017

@author: swee lim
"""

import os
import os.path as op
import re
import errno
from collections import defaultdict
from PyQt4.QtCore import QThread, pyqtSlot, pyqtSignal
from PyQt4.QtGui import qApp
import functions as pf

# hash table for sorting and labeling the various VTK file type paths
SEARCHDICT = defaultdict(dict,
                         {'resampled': {'ch2': 'ch2',
                                        'ch1': 'ch1'},
                          'skeleton': {'ch2': 'skel'}})


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


class getFileThread(QThread):
    """
    Subclass  QThead.run() to get paths for skeleton and resampled
    voxels VTK files.
    """
    signal = pyqtSignal([str], [dict])
    failed = pyqtSignal()
    success = pyqtSignal()

    def __init__(self, folder):
        super(getFileThread, self).__init__()
        self.folder = folder

    @pyqtSlot()
    def run(self):
        """
        Runs a regex search for the labels skeleton, resampled and ch1 or ch2.
        """
        vtks = defaultdict(dict)

        for files in os.listdir(self.folder):
            if op.isfile(op.join(self.folder, files)):
                vtk_type = re.search(r'(skeleton|resampled)', files)
                channel_type = re.search(r'(ch[12])\w+\d+', files)

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

        # Checks
        numfiles = len(vtks['skel'].keys())
        if numfiles:
            condition2 = all([len(vtks[k].keys()) == numfiles for k in vtks])
            if condition2:
                self.signal[dict].emit(vtks)
                self.signal.emit("Found {} skeleton that are ready "
                                 "to be normalized!".format(numfiles))
                self.success.emit()
            else:
                self.signal.emit("The number of Skeleton and Resampled files "
                                 "in channels 1 and 2 are not the same, "
                                 "please fix!")
                self.failed.emit()
        else:
            self.signal.emit("No suitable skeleton VTK files found, please "
                             "check your labels are in the correct format!")
            self.failed.emit()


class normalizeThread(QThread):
    """
    Subclass QThread to run normalizing routine
    """
    signal = pyqtSignal(str)
    finished = pyqtSignal()
    interrupted = pyqtSignal()
    update_progress = pyqtSignal()

    def __init__(self, paths, savedir,
                 skel_prefix='skel',
                 ch1_prefix='ch1',
                 ch2_prefix='ch2'):
        super(normalizeThread, self).__init__()
        self.flag = True
        self.paths = paths
        self.savedir = str(savedir)
        self.skel_prefix = skel_prefix
        self.ch1_prefix = ch1_prefix
        self.ch2_prefix = ch2_prefix

    @pyqtSlot()
    def run(self):
        """
        Runs pf.point_cloud_data() to get a point cloud of VTK values around
        each point on the skeleton, normalizes the channels with pf.normalize()
        and writes output using pf.write_vtk()
        """
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
            string2 = 'Finished Normalization of {} files!'.format(len(skels))
            self.signal.emit(string2)
            self.finished.emit()
        else:
            remain = len(skels) - len(keys)
            string2 = ('Process interrupted! {} out of {} files '
                       'were normalized!'.format(remain, len(skels)))
            self.interrupted.emit()
            self.signal.emit(string2)

    @pyqtSlot()
    def stop(self):
        print "Thread Interrupted!"
        self.flag = False
