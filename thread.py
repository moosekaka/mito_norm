# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 14:06:59 2017

@author: sweel_Rafelski
"""

from PyQt4.QtCore import QThread


class UsageError(Exception):
    """
    Class for user-facing (non-programming) errors
    """
    pass


def swalk(ddir, txt, start=None, stop=None):
    """
    wrapper caller for single level file dict, returns a dict

    Parameters
    ----------
    ddir : str
        path of dir

    txt : str
        text to be matched with fnmatch, shell format

    start : int
      start of slice

    end : int
      end of slice
    """
    vtf = dict()
    for root, _, files in os.walk(ddir):
        for f in files:
            if fnmatch.fnmatch(f, txt):
                vtf[f[start:stop]] = op.join(root, f)
        break  # only walk thru the top directory, not the Normalized dir
    if len(vtf):
        return vtf
    else:
        traceback.print_stack(limit=5)
        raise UsageError('Search for file with ext. {} in dir {} failed'
                         .format(txt, ddir))



class getFilesThread(QThread):

    def __init__(self, dirpath):
        QThread.__init__(self)
        self.dirpath = dirpath

    def __del__(self):
        self.wait()

    def run(self):
        try:
            vtkSkel = swalk(self.dirpath, '*RFP*skeleton.vtk', stop=-13)
            vtkVolRfp = swalk(self.dirpath, '*RF*resampled.vtk', stop=-14)
            vtkVolGfp = swalk(self.dirpath, '*GF*resampled.vtk', stop=-14)
        except UsageError:
            raise
        if len(vtkSkel) == len(vtkVolRfp) == len(vtkVolGfp):
            return vtkSkel, vtkVolRfp, vtkVolGfp
        else:
            return None

        # your logic here