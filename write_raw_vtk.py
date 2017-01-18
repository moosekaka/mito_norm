import os
import os.path as op
import errno
import fnmatch
import traceback
import cPickle as pickle
import pipefuncs as pf
import sys
# pylint: disable=C0103


class UsageError(Exception):
    """
    Class for user-facing (non-programming) errors
    """
    pass


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


def main():
    """
    Pipeline to normalize'raw' vtk files and make mito network graph
    """
    mkdir_exist(op.join(os.curdir, 'test', 'Normalized'))
    try:
        with open(op.join(os.curdir, 'test', 'background.pkl'), 'rb') as inpt:
            background = pickle.load(inpt)
    except IOError:
        print "No background file detected, default to min of ch 1 and ch2"
        background = {}

    try:
        vtkSkel = swalk(op.join(os.curdir, 'test'), '*RFP*skeleton.vtk', stop=-13)
        vtkVolRfp = swalk(op.join(os.curdir, 'test'), '*RF*resampled.vtk', stop=-14)
        vtkVolGfp = swalk(op.join(os.curdir, 'test'), '*GF*resampled.vtk', stop=-14)
    except UsageError:
        raise

    for key, _ in sorted(vtkSkel.iteritems()):
        print 'processing {}:'.format(key)
        data = pf.pt_cld_sclrs(vtkSkel[key],
                               vtkVolGfp[key.replace('RFP', 'GFP')],
                               vtkVolRfp[key], radius=2.5)

        # saves all results to './Normalized' directory
        filename = op.join(op.curdir, 'test', 'Normalized',
                           'Norm_{}_skeleton.vtk'.format(key))
        (a, b, c, d, e) = pf.normSkel(data, background.get(key))

        calc = {'norm_scaled': a,
                'norm_unscaled': b,
                'background_sub_ch1': c,
                'background_sub_ch2': d,
                'width_equivalent': e}
        pf.writevtk(data, filename, **calc)

if __name__ == '__main__':
    sys.exit(main())
