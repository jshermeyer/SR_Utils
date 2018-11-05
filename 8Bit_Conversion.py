#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Created on Mon Nov 27 2017

@author: jshermeyer
"""

import sys
import subprocess
import os
import glob
import gdal
import numpy as np
import datetime
from tqdm import tqdm
from fnmatch import fnmatch


def display(image, display_min, display_max):
    image = np.array(image)
    image.clip(display_min, display_max, out=image)
    image -= display_min
    np.floor_divide(image, (display_max - display_min + 1) / 256,out=image, casting='unsafe')
    return image.astype(np.uint8)

def display_16(image, display_min, display_max):
    image = np.array(image)
    image.clip(display_min, display_max, out=image)
    image -= display_min
    np.floor_divide(image, (display_max - display_min + 1) / 65535,out=image, casting='unsafe')
    return image.astype(np.uint16)


def convert_to_8Bit(inputRaster, outputRaster,
                           outputPixType='Byte',
                           outputFormat='GTiff',
                           rescale_type='rescale',
                           percentiles=[1, 99]):
    '''
    Convert 16bit image to 8bit
    rescale_type = [clip, rescale]
        if clip, scaling is done strictly between 0 65535 
        if rescale, each band is rescaled to a min and max 
        set by percentiles
    '''
    srcRaster = gdal.Open(inputRaster)
    driver = gdal.GetDriverByName(outputFormat)
    RasHolder=[]

    # iterate through bands
    count=srcRaster.RasterCount
    for bandId in range(count):
        bandId = bandId+1
        band = srcRaster.GetRasterBand(bandId)
        geo=srcRaster.GetGeoTransform()
        proj=srcRaster.GetProjection()
        NoData=band.GetNoDataValue()
        #print NoData
        if NoData == None or NoData =="None":
            NoData=0
            #print NoData
        
        band=band.ReadAsArray()
        shape=band.shape
        #band = np.ma.masked_equal(band,NoData)
        bandf=band.astype(float)
        bandf[np.where((band == NoData))] = np.nan
        if rescale_type == 'rescale':
            bmin = np.nanpercentile(bandf, percentiles[0])
            bmax = np.nanpercentile(bandf, percentiles[1])
            #print bmin, bmax
            
            
        else:
            bmin, bmax = 1, 7000
        
        imout=display(bandf,bmin,bmax)
        imout[np.where((imout == 0))] = 1
        imout[np.where((band == NoData))] = 0
        RasHolder.append(imout)
        
    rescale_out = driver.Create(outputRaster, RasHolder[0].shape[1], RasHolder[0].shape[0], 3, gdal.GDT_Byte)
    rescale_out.SetGeoTransform( geo )
    rescale_out.SetProjection( proj )
    rescale_out.GetRasterBand(1).WriteArray(RasHolder[2])
    rescale_out.GetRasterBand(1).SetNoDataValue(0)
    rescale_out.GetRasterBand(2).WriteArray(RasHolder[1])
    rescale_out.GetRasterBand(2).SetNoDataValue(0)
    rescale_out.GetRasterBand(3).WriteArray(RasHolder[0])
    rescale_out.GetRasterBand(3).SetNoDataValue(0)
    del rescale_out
