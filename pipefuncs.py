# -*- coding: utf-8 -*-
"""
Module for functions for mito network normalization
@author: sweel_rafelski
"""
import os
import os.path as op
import vtk
import vtk.util.numpy_support as vnpy
import numpy as np
# pylint: disable=C0103
datadir = op.join(os.getcwd())


def vtk_read(fpath, readertype='vtkPolyDataReader'):
    """
    Reads vtk files and returns the VTK object
    """
    reader = getattr(vtk, readertype)()
    reader.SetFileName(fpath)
    reader.Update()
    data = reader.GetOutput()
    return data


def pt_cld_sclrs(skelpath, ch1path, ch2path, **kwargs):
    """
    Returns scalar values from voxels data (eg. resampledVTK) lying within
    a point cloud of a specified radius for each point

    Parameters
    ----------
    skelpath, ch1path, ch2path : str
        filepaths to skeleton vtk, volume/voxels vtk output of respective
        channels to be normalized
    kwargs :
        radius value argument (float) for _pointcloud(), default=2.5 pixels
    Returns
    -------
    polydata : VTK poly
        polydata object with raw scalar values and width
    """
    dataSkel = vtk_read(skelpath)
    voxels_ch1 = vtk_read(ch1path,
                          readertype='vtkStructuredPointsReader')
    voxels_ch2 = vtk_read(ch2path,
                          readertype='vtkStructuredPointsReader')

    ptcld_ch1, ptcld_ch2 = _pointcloud(dataSkel, voxels_ch1, voxels_ch2, **kwargs)
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(dataSkel.GetPoints())
    polydata.SetLines(dataSkel.GetLines())
    polydata.GetPointData().AddArray(ptcld_ch1)
    polydata.GetPointData().AddArray(ptcld_ch2)
    return polydata


def _pointcloud(skel, ch1, ch2, radius=2.5):
    vox_ch2 = vtk.vtkDoubleArray()
    vox_ch2.SetName("vox_ch2")
    vox_ch1 = vtk.vtkDoubleArray()
    vox_ch1.SetName("vox_ch1")

    # vtk.pointlocator() used to to find the set of points lying within the
    # radius of the point of interest, returns results in a list called
    # result
    loc = vtk.vtkPointLocator()
    loc.SetDataSet(ch2)
    loc.BuildLocator()

    inten_ch1 = ch1.GetPointData().GetScalars().GetTuple1
    inten_ch2 = ch2.GetPointData().GetScalars().GetTuple1
    result = vtk.vtkIdList()

#   averaging of pts intensity value surrounding each point in skel
    for n in range(skel.GetNumberOfPoints()):

        pt_of_int = tuple(np.ceil(i/.055) for i in skel.GetPoint(n))
        loc.FindPointsWithinRadius(radius, pt_of_int, result)
        vox_id = [result.GetId(i) for i in range(result.GetNumberOfIds())]

        vox_ch1.InsertNextValue(np.mean([inten_ch1(m) for m in vox_id]))

        vox_ch2.InsertNextValue(np.mean([inten_ch2(m) for m in vox_id]))
    return vox_ch1, vox_ch2


def normSkel(polydata, background=None):
    """
    Normalize channels to correct for focal plane intensity variations

    Parameters
    ----------
    polydata : vtkPolyData
        vtk object returned from pt_cld_sclrs()
    backgrnd : tuple
        tuple containing background values for each channel
    """
    temp = polydata.GetPointData()
    vox_ch1 = vnpy.vtk_to_numpy(temp.GetArray('vox_ch1'))
    vox_ch2 = vnpy.vtk_to_numpy(temp.GetArray('vox_ch2'))

    # pick the lowest value in the channel
    if background is not None:
        min_ch1 = min(background[0], min(vox_ch1))
        min_ch2 = min(background[1], min(vox_ch2))
    # if no background data file provided, default to min value in skeleton
    else:
        min_ch1 = min(vox_ch1)
        min_ch2 = min(vox_ch2)

    min_ch2 = min_ch2 - 1  # ensure no division by zero

#   background Substracted rfp and gfps
    ch2_bckgrnd = vox_ch2 - min_ch2
    ch1_bckgrnd = vox_ch1 - min_ch1

#   width equivalent
    width_eqv = ch2_bckgrnd / min(ch2_bckgrnd)
    unscaled_dy = ch1_bckgrnd / width_eqv  # raw DY/W normalized values

#   rescale DY to minmax
    _min = min(unscaled_dy)
    _max = max(unscaled_dy)
    normalized_dy = ((unscaled_dy - _min)/(_max - _min))
    return normalized_dy, unscaled_dy, ch1_bckgrnd, ch2_bckgrnd, width_eqv


def writevtk(dat, fname, **kwargs):
    """
    Output as "fname", with labels for scalar values as a dictionary
    """
    for k in kwargs:
        temp = vnpy.numpy_to_vtk(kwargs[k])
        temp.SetName(k)
        dat.GetPointData().AddArray(temp)

    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(fname)
    writer.SetInputData(dat)
    writer.Update()
