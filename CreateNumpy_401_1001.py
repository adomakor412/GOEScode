#!/usr/bin/env python3

import numpy as np
import sys
import os
from os import path as op
import re
from subprocess import Popen
import xarray as xr
import metpy
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from pyresample import image, geometry
import seaborn as sns
import netCDF4
sns.set(style="darkgrid")

class CreateNumpy_401_1001(ncFile=sys.argv[1], pathIn=sys.argv[2], pathOut=sys.argv[3]):
    def __init__(self):
        self.ncFile = ncFile
        self.pathIn = PathIn
        self.pathOut = PathOut
        
    def normIm(self,im,gamma=1.0,reverse=False):
        nim = ((im-np.nanmin(im))*(np.nanmax(im)-np.nanmin(im))**(-1))
        if reverse:#want clouds to be white
            nim = (1.0-nim**(gamma))
        return nim
    
    def goes_2_roi(self,loaded_goes, 
               target_extent,
               target_rows,#actual length or base
               target_cols,#actual width or height
               cartopy_target_proj,
               data_key='Rad',
               radius_of_influence=50000):
        """Function that goes from loaded GOES data to data resampled in a projection for an extent"""
        dat = loaded_goes.metpy.parse_cf('Rad')
        geos_crs = dat.metpy.cartopy_crs
        cartopy_source_extent = geos_crs.x_limits + geos_crs.y_limits
        pyresample_source_extent = (cartopy_source_extent[0],
                                    cartopy_source_extent[2],
                                    cartopy_source_extent[1],
                                    cartopy_source_extent[3])
        rad = dat.data
        source_area = geometry.AreaDefinition('GOES-1X', 'Full Disk','GOES-1X', 
                                              geos_crs.proj4_params,
                                              rad.shape[1], rad.shape[0],
                                              pyresample_source_extent)
        area_target_def = geometry.AreaDefinition('areaTest', 'Target Region', 'areaTest',
                                            cartopy_target_proj.proj4_params,
                                            target_rows, target_cols,
                                            target_extent)
        geos_con_nn = image.ImageContainerNearest(rad, 
                                                source_area, 
                                                radius_of_influence=radius_of_influence)

        # Here we are using pyresample for the remapping
        area_proj_con_nn = geos_con_nn.resample(area_target_def)
        return area_proj_con_nn.image_data
        
    def cartopy_pyresample_toggle_extent(self,input_extent):
        return np.array(input_extent)[np.array([0,2,1,3])]

    def trasform_cartopy_extent(self,source_extent,source_proj, target_proj):
        target_extent = target_proj.transform_points(source_proj, 
                                                     np.array(source_extent[:2]),
                                                     np.array(source_extent[2:])).ravel()
        # target_extent in 3D, must be in 2D
        return cartopy_pyresample_toggle_extent(np.array(target_extent)[np.array([0,1,3,4])])
    
    def create_nc_Numpy(self):
        myFile = xr.open_dataset(op.join(self.pathIn,self.ncFile))
        dat = myFile.metpy.parse_cf('Rad')
        geos = dat.metpy.cartopy_crs

        cartopy_extent_goes = geos.x_limits + geos.y_limits
        pyresample_extent_goes = (cartopy_extent_goes[0],
                                    cartopy_extent_goes[2],
                                    cartopy_extent_goes[1],
                                    cartopy_extent_goes[3])
        goes_params = geos.proj4_params
        rad = dat.data
    
        pc = ccrs.PlateCarree()
        mc = ccrs.Mercator()

        # Convert extent from pc to mc (both cylindrical projections)
        extent_pc = [-109.59326, -102.40674, 8.94659, -8.94656]

        target_extent_mc_cartopy = trasform_cartopy_extent(extent_pc, pc, mc)
        target_extent_mc_pyresample = cartopy_pyresample_toggle_extent(target_extent_mc_cartopy)

        roi_rads = goes_2_roi(myFile,
                   target_extent_mc_pyresample,
                   401,1001,
                   mc)
    
        full_filename = op.join(pathOut,ncFile[:-3])
        np.save(full_filename,roi_rads)
        myFile.close()
        return
if __name__=='__main__':
    CreateNumpy_401_1001.run()