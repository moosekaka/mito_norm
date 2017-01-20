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

        # these are the labels used to name the outputs above
        calc = {'norm_scaled': a,
                'norm_unscaled': b,
                'background_sub_ch1': c,
                'background_sub_ch2': d,
                'width_equivalent': e}
        pf.writevtk(data, filename, **calc)

if __name__ == '__main__':
    sys.exit(main())
