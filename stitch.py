#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 23 12:26:26 2018

@author: avanetten

adapted from basiss/albu_inference_mod_new/src/stitch.py
"""

from __future__ import print_function
import os
import argparse
import pandas as pd
import numpy as np
import cv2
import time
import argparse



###############################################################################
def post_process_image_name(name, data_dir, size_mult=2, n_bands=3, 
                            sep0='__', sep1='_', ext='.tif', 
                            super_verbose=False):
    '''
    From an image name and a data_dir,
    reconstruct the image. Adapted from basiss.py
    image names are assumed to have the format below (named in ave_xview_parse.py):
        outpath = os.path.join(chip_outdir, out_name + \
            '__' + str(y) + '_' + str(x) + '_' + str(sliceHeight) + '_' + str(sliceWidth) +\
            '_' + str(pad) + '_' + str(win_w) + '_' + str(win_h) + ext)

    Assume image is being resized by super-resolution, so the slices have been
      resized by a factor of size_mult (e.g. 2x super res has size_mult = 2)

    '''
    
    im_slice_names = sorted([z for z in os.listdir(data_dir) if z.startswith(name+sep0)])
    
    im_slice_name_ex = im_slice_names[0].split(ext)[0]
    im_name, vals = im_slice_name_ex.split(sep0)
    ymin, xmin, slice_y, slice_x, pad, im_x, im_y = [int(z) for z in vals.split(sep1)]
    

    # get image width and height
    w, h = im_x * size_mult, im_y * size_mult
    
    if super_verbose:
        print ("im_slice_name_ex:", im_slice_name_ex)
        print ("vals:", vals)
        print ("w, h, n_bands:", w, h, n_bands)
        print ("[int(z) for z in vals.split('_')]:", [int(z) for z in vals.split('_')])
    
    # create numpy zeros of appropriate shape
    #im_raw = np.zeros((h,w), dtype=np.uint8)  # dtype=np.uint16)
    im_raw = np.zeros((h,w,n_bands), dtype=np.uint16)

    #  = create another zero array to record which pixels are overlaid
    im_norm = np.zeros((h,w,n_bands), dtype=np.uint8)  # dtype=np.uint16)
    overlay_count = np.zeros((h,w), dtype=np.uint8)

    # iterate through slices
    #for i, (idx_tmp, item) in enumerate(df_pos_.iterrows()):
    for i, name_full in enumerate(im_slice_names):        
        if (i % 100) == 0:
            print ("  ",  i, "/", len(im_slice_names))
            #print (i, "\n", idx_tmp, "\n", item)

        im_slice_name_ex = name_full.split('.tif')[0]
        im_name, vals = im_slice_name_ex.split(sep0)
        #print(im_name)
        ymin, xmin, slice_y, slice_x, pad, im_x, im_y = [ size_mult* int(z) 
                                                            for z in vals.split(sep1)]


        #[row_val, idx, name, name_full, xmin, ymin, slice_x, slice_y, im_x, im_y] = item
        
        # read in image
        if n_bands == 3:
            im_slice_refine = cv2.imread(os.path.join(data_dir, name_full), 1)
        else:
            print ("Still need to write code to handle multispecral data...")
            return
                
        #print ("im_slice_refine:", im_slice_refine)
        if super_verbose:
            print ("vals:", vals)
        if slice_x > im_x:
            slice_x=im_x
        if slice_y > im_y:
            slice_y=im_y
            
        x0, x1 = xmin, xmin + slice_x
        y0, y1 = ymin, ymin + slice_y

        if super_verbose:
            print ("name_full:", name_full)
            print ("im_slice_refine.shape:", im_slice_refine.shape)
            print ("im_raw.shape:", im_raw.shape)
            print ("im_x, im_y:", im_x, im_y)
            print ("x0, y0, x1, y1:", x0, y0, x1, y1)

        # add data to im_raw for each band
        for j in range(n_bands):
            #print ("j:", j)
            #print ("im_raw[y0:y1, x0:x1.shape, j]:", im_raw[y0:y1, x0:x1, j].shape)
            im_raw[y0:y1, x0:x1, j] += im_slice_refine[:,:,j]

        # update count
        overlay_count[y0:y1, x0:x1] += np.ones((slice_y, slice_x), dtype=np.uint8)

    # compute normalized im
    # if overlay_count == 0, reset to 1
    overlay_count[np.where(overlay_count == 0)] = 1
    
    #print ("np.max(overlay_count):", np.max(overlay_count))
    #print ("np.min(overlay_count):", np.min(overlay_count))
                  
    # throws a memory error if using np.divide...
    if h < 60000:
        for j in range(n_bands):
            im_norm[:,:,j] = np.divide(im_raw[:,:,j], overlay_count).astype(np.uint8)
    else:
        for j in range(h):
            #print ("j:", j)
            im_norm[j] = (im_raw[j] / overlay_count[j]).astype(np.uint8)
        
    #print ("im_norm.shape:", im_norm.shape)
    #print ("im_norm.dtype:", im_norm.dtype)

    return im_name, im_norm, im_raw, overlay_count   


###############################################################################
def main():

    print ("Running stitch.py...")

    # construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--im_dir', type=str, default='/images/to/stitch/',
                        help="images location")
    parser.add_argument('--out_dir', type=str, default='/output/dir/',
                        help="output_images location")
    parser.add_argument('--geo_ref_dir', type=str, default='/optionally/add/georeferencing/back/to/images/',
                        help="Directory of original geotiffs, to insert geo metadate in outputs")
    parser.add_argument('--size_mult', type=int, default=2,
                        help="fraction the image has been resized in post-processing, (e.g. 2x super res has size_mult = 2)")
    parser.add_argument('--n_bands', type=int, default=3,
                        help="number of image bands")    
    args = parser.parse_args()

    # compression 0 to 9 (most compressed)
    compression_params = [cv2.IMWRITE_PNG_COMPRESSION, 5]
    output_ext = '.tif'
    sep0 = '__'
    sep1 = '_'

    if not os.path.exists(args.out_dir):
            os.mkdir(args.out_dir)


    data_dir = args.im_dir 
    stitch_dir = args.out_dir 
    out_dir_im_raw = os.path.join(stitch_dir, 'im_raw')
    out_dir_count = os.path.join(stitch_dir, 'im_count')
    out_dir_im_norm = os.path.join(stitch_dir, 'im_norm')
    for p in [stitch_dir, out_dir_im_raw, out_dir_count, out_dir_im_norm]:
        if not os.path.exists(p):
            os.mkdir(p)
        
        
    # execute
    
    # get image names
    slice_names = sorted([z for z in os.listdir(data_dir) if z.endswith(output_ext)])
    image_names = np.sort(np.unique([z.split(sep0)[0] for z in slice_names]))
    #print ("image_names:", image_names)

    for i,name_root in enumerate(image_names):
        print (i, "/", len(image_names), "  ", name_root+output_ext)
        im_name, im_norm, im_raw, overlay_count = \
            post_process_image_name(name_root, data_dir, size_mult=args.size_mult, 
                                    n_bands=args.n_bands, sep0=sep0, sep1=sep1,
                                    ext=output_ext, super_verbose=False)
    
        # save files
        out_file_root = im_name + output_ext
        out_file_im_norm = os.path.join(out_dir_im_norm, out_file_root)
        out_file_im_raw = os.path.join(out_dir_im_raw, out_file_root)
        out_file_count = os.path.join(out_dir_count, out_file_root)
    
        cv2.imwrite(out_file_im_norm, im_norm.astype(np.uint8), compression_params)
        del im_norm
        cv2.imwrite(out_file_im_raw, im_raw.astype(np.uint8), compression_params)
        del im_raw
        cv2.imwrite(out_file_count, overlay_count, compression_params)
        #cv2.imwrite(out_file_count, overlay_count.astype(np.uint8), compression_params)
        del overlay_count
        
    # add geo meta data, if desired
    if len(args.geo_ref_dir) > 0:
        import AddGeoReferencing
        print ("AddGeoReferencing...")
        AddGeoReferencing.geo_that_raster(out_dir_im_norm, args.geo_ref_dir)

    
    return


if __name__ == "__main__":
    main()