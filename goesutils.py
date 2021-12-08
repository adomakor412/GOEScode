"""
These are a set of utilities for remapping, reprojection, 
radiance to bt, and visualization
"""

import numpy as np
from pyresample import image, geometry


def norm_im(im,gamma=1.0,reverse=False):
    """ For max-min normalization for visualization,
    applying a gamma, and reversing. Remaps data
    from 0 to 1 using (x-max(x))/(min(x)-max(x))
    """
    nim = ((im-np.nanmin(im))*(np.nanmax(im)-np.nanmin(im))**(-1))
    if reverse:#want clouds to be white
        nim = (1.0-nim**(gamma))
    return nim

def radiance_to_BT(rad, planck_fk1, planck_fk2, planck_bc1, planck_bc2):
    """Radiances to Brightness Temprature 
    (using black body equation) from NOAA
    """
    invRad = np.array(rad)**(-1)
    arg = (invRad*planck_fk1) + 1.0
    T = (- planck_bc1+(planck_fk2 * (np.log(arg)**(-1))) )*(1/planck_bc2) 
    return T


def goes_2_roi(loaded_goes,
               target_extent,
               target_rows,
               target_cols,
               cartopy_target_proj,
               data_key='Rad',
               radius_of_influence=50000):
    """Function that goes from loaded GOES data to data resampled in a
    projection for an extent"""

    dat = loaded_goes.metpy.parse_cf(data_key)
    geos_crs = dat.metpy.cartopy_crs
    cartopy_source_extent = geos_crs.x_limits + geos_crs.y_limits
    pyresample_source_extent = (cartopy_source_extent[0],
                                cartopy_source_extent[2],
                                cartopy_source_extent[1],
                                cartopy_source_extent[3])
    rad = dat.data
    source_area = geometry.AreaDefinition('GOES-1X', 'Full Disk', 'GOES-1X',
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


def cartopy_pyresample_toggle_extent(input_extent):
    """This takes a cartopy style input extent and
    tranforms it into a pyresample style extent or visa-versa.
    [a,b,c,d] -> [a,c,b,d]
    """
    return np.array(input_extent)[np.array([0, 2, 1, 3])]


def trasform_cartopy_extent(source_extent, source_proj, target_proj):
    """This starts with a source 2D extent and uses cartopy to transform
    it to a target extent via two projections. 
    """
    target_extent = target_proj.transform_points(source_proj,
                                                 np.array(source_extent[:2]),
                                                 np.array(source_extent[2:])).ravel()
    # target_extent in 3D, must be in 2D
    return cartopy_pyresample_toggle_extent(np.array(target_extent)[np.array([0, 1, 3, 4])])

