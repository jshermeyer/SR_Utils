#jshermeyer- 10/23/18
#Super resolution is difficult with georeferenced data, as an enhacnement on an image with an odd number of pixels can cause  more or fewer rows and columns to be added to an output image.  To ensure georeferencing remains consistent this script takes in a folder of the native data and corrects the super-resolved output images to match the original georeferncing info exactly.  Thus, super-resolved footprints are identical to the native imagery, although they may not match identical pixel space.

import numpy as np
import gdal
import os
import datetime
import glob
import sys
from tqdm import tqdm



def geo_that_raster(norm_folder,original_image_folder):
    os.chdir(norm_folder)
    SR_output=glob.glob("*.tif")

    os.chdir(original_image_folder)
    Originals=glob.glob("*.tif")

    SR_output.sort()
    Originals.sort()
    #print(SR_output,Originals)

    if len(SR_output) != len(Originals):  ### could add more error checking as needed, I think simple sorting should work
        print("Inequal number of images in each folder, check your data")
        print("Exiting")
    else:
        for image,SR in tqdm(zip(Originals,SR_output)):
            #print(image,SR)
            os.chdir(original_image_folder)
            raster=gdal.Open(image)
            geo=raster.GetGeoTransform()
            proj=raster.GetProjection()
            #print(geo)
            rows1=raster.RasterXSize
            cols1=raster.RasterYSize
            #print(rows1,cols1)
            os.chdir(norm_folder)
            O=gdal.Open(SR, gdal.GA_Update)
            geo2=O.GetGeoTransform()
            #print(geo2)
            rows2=O.RasterXSize
            cols2=O.RasterYSize
            #print(rows2,cols2)
            SF1=rows1/float(rows2)
            SF2=cols1/float(cols2)
            #print(SF1,SF2)
            pixH=float(geo[1])*SF1
            pixW=float(geo[5])*SF2
            geo=[geo[0],pixH,geo[2],geo[3],geo[4],pixW]
            #print(geo)
            O.SetProjection( proj )
            O.SetGeoTransform( geo )
            del O
            
            
if __name__ == "__main__":
    geo_that_raster(sys.argv[1],sys.argv[2])

# python3 AddGeoReferencing.py "/folder/to/add/referencing/to" "/native/resolution/imagery/with/georeferencing"

