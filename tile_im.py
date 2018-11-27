#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 23 15:55:35 2018

@author: avanetten
"""


from __future__ import print_function

import os
import time
import argparse
import numpy as np
import pandas as pd
import cv2
# cv2 can't load large files, so need to import skimage too
import skimage.io 

#import sys
#path_basiss = os.path.dirname(os.path.realpath(__file__))
#sys.path.append(path_basiss)
#import basiss

###############################################################################
def slice_ims(im_dir, out_dir, slice_x, slice_y, 
                    stride_x, stride_y,
                    pos_columns = ['idx', 'name', 'name_full', 'xmin', 
                                   'ymin', 'slice_x', 
                                   'slice_y', 'im_x', 'im_y'],
                    sep0='__', sep1='_', pad=0, ext='.tif', verbose=True):
    '''Slice images into patches, assume ground truth masks 
        are present
    Adapted from basiss.py'''
    
    if verbose:
        print ("Slicing images in:", im_dir)
        
    t0 = time.time()    
    count = 0
    pos_list, name_list = [], []
    #nims,h,w,nbands = im_arr.shape

    im_roots = [z for z in os.listdir(im_dir) if z.endswith('.tif')]
    
    #im_roots = ['90.tif']
    
    
    for i,im_root in enumerate(im_roots):

        im_path =  os.path.join(im_dir, im_root)
        if verbose:
            print (i, "/", len(im_roots), "im_path:", im_path)
        name = im_root.split('.')[0]
        
        use_skimage = False
        try:
        # cv2 can't load large files
            im = cv2.imread(im_path)  
        except:
            # load with skimage, (reversed order of bands)
            im = skimage.io.imread(im_path)#[::-1]
            use_skimage = True

        h, w, nbands = im.shape
        print ("im.shape:", im.shape)
        
        seen_coords = set()
        
        #if verbose and (i % 10) == 0:
        #    print (i, "im_root:", im_root)
                
        # dice it up
        # after resize, iterate through image 
        #     and bin it up appropriately
        for x in range(0, w, stride_x):  
            for y in range(0, h, stride_y): 
                
                xmin = max(0, min(x, w-slice_x) )
                ymin = max(0, min(y, h - slice_y) ) 
                coords = (xmin, ymin)
                
                # check if we've already seen these coords
                if coords in seen_coords:
                    continue
                else:
                    seen_coords.add(coords)
                
                # check if we screwed up binning
                if (slice_x <= w and (xmin + slice_x > w)) \
                    or (slice_y <= h and (ymin + slice_y > h)):
                    print ("Improperly binned image,")
                    return

                # get satellite image cutout
                im_cutout = im[ymin:ymin + slice_y, 
                               xmin:xmin + slice_x]
                
                ##############
                # skip if the whole thing is black
                if np.max(im_cutout) < 1.:
                    continue
                else:
                    count += 1
                
                if verbose and (count % 50) == 0:
                    print ("count:", count, "x:", x, "y:", y) 
                ###############
                                

                # set slice name
                name_full = name + sep0 + str(ymin) + sep1 + str(xmin) + sep1 \
                  + str(slice_y) + sep1 + str(slice_x) + sep1 + str(pad) + sep1 \
                  + str(w) + sep1 +  str(h) + ext
                

                ##name_full = str(i) + sep + name + sep \
                #name_full = name + sep \
                #    + str(xmin) + sep + str(ymin) + sep \
                #    + str(slice_x)  + sep + str(slice_y) \
                #    + sep + str(w) + sep + str(h) \
                #    + '.tif'
                    
                pos = [i, name, name_full, xmin, ymin, slice_x, slice_y, w, h]
                # add to arrays
                #idx_list.append(idx_full)
                name_list.append(name_full)
                #im_list.append(im_cutout)
                #mask_list.append(mask_cutout) 
                pos_list.append(pos)
                
                name_out = os.path.join(out_dir, name_full)
                
                if not use_skimage:
                    cv2.imwrite(name_out, im_cutout)
                else:
                    # if we read in with skimage, need to reverse colors
                    cv2.imwrite(name_out, cv2.cvtColor(im_cutout, cv2.COLOR_RGB2BGR))
    
    # create position datataframe
    df_pos = pd.DataFrame(pos_list, columns=pos_columns)
    df_pos.index = np.arange(len(df_pos))
    
    if verbose:
        print ("  len df;", len(df_pos))
        print ("  Time to slice arrays:", time.time() - t0, "seconds")
        
    return df_pos

###############################################################################
def main():
    
    # construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--im_dir', type=str, default='/ims/to/tile/',
                        help="images location")
    parser.add_argument('--out_dir', type=str, default='/output/folder/for/tiles/',
                        help="output_images location")
    parser.add_argument('--slice_x', type=int, default=544)
    parser.add_argument('--slice_y', type=int, default=544)
    parser.add_argument('--stride_x', type=int, default=108)
    parser.add_argument('--stride_y', type=int, default=108)
    args = parser.parse_args()

    if not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    df_pos = slice_ims(args.im_dir, args.out_dir, args.slice_x, args.slice_y, 
                    args.stride_x, args.stride_y,
                    pos_columns = ['idx', 'name', 'name_full', 'xmin', 
                                   'ymin', 'slice_x', 
                                   'slice_y', 'im_x', 'im_y'],
                    verbose=True)



    path_tile_df_csv = os.path.join(os.path.dirname(args.out_dir), os.path.basename(args.out_dir) + '_df.csv') 
    # save to file
    df_pos.to_csv(path_tile_df_csv)
    print ("df saved to file:", path_tile_df_csv)


#    # use config file
#    # use config file? 
#    from config import Config
#    import json
#    parser = argparse.ArgumentParser()
#    parser.add_argument('config_path')
#    args = parser.parse_args()
#    # get config
#    with open(args.config_path, 'r') as f:
#        cfg = json.load(f)
#        config = Config(**cfg)
#
#    # get input dir
#    path_images_8bit = os.path.join(config.path_data_root, config.test_data_refined_dir)
#
#    # make output dirs
#    # first, results dir
#    res_dir = os.path.join(config.path_results_root, config.test_results_dir)
#    os.makedirs(res_dir, exist_ok=True)
#    path_tile_df_csv = os.path.join(config.path_results_root, config.test_results_dir, config.tile_df_csv)
#    path_tile_df_csv2 = os.path.join(config.path_data_root, os.path.dirname(config.test_sliced_dir), config.tile_df_csv)
#
#    # path for sliced data
#    path_sliced = os.path.join(config.path_data_root, config.test_sliced_dir)
#     
#    #if not os.path.exists(config.results_dir):
#    #    os.mkdir(config.results_dir)
#    #if not os.path.exists(config.path_sliced):
#    #    os.mkdir(config.path_sliced)
#    
#    # only run if nonzer tile and sliced_dir
#    if (len(config.test_sliced_dir) > 0) and (config.slice_x > 0):
#        os.makedirs(path_sliced, exist_ok=True)
#   
#
#        df_pos = slice_ims(path_images_8bit, path_sliced, 
#                       config.slice_x, config.slice_y, 
#                       config.stride_x, config.stride_y,
#                       pos_columns = ['idx', 'name', 'name_full', 'xmin', 
#                                   'ymin', 'slice_x', 
#                                   'slice_y', 'im_x', 'im_y'],
#                       verbose=True)
#        # save to file
#        df_pos.to_csv(path_tile_df_csv)
#        print ("df saved to file:", path_tile_df_csv)
#        # also csv save to data dir
#        df_pos.to_csv(path_tile_df_csv2)


#    # iterate through im_dir and gather files 
#    im_arr = []
#    name_arr = []
#    mask_arr = []
#    im_roots = [z for z in os.listdir(args.im_dir) of z.endswith('.tif')]
#    for i,im_root in enumerate(im_roots):
#        im_file_name = os.path.join(im_dir, im_root)
#        im = cv2.imread(im_file_name, 1)
#        name_arr.append(im_file_name)
#        im_arr.append(im)
#        
#    # slice
#    df_pos, name_out_arr, im_out_arr, mask_out_arr = \
#        basiss.slice_ims(im_arr, mask_arr, names_arr, 
#                    args.slice_x, args.slice_y, 
#                    args.stride_x, args.stride_y,
#                    pos_columns = ['idx', 'name', 'xmin', 
#                                   'ymin', 'slice_x', 
#                                   'slice_y', 'im_x', 'im_y'],
#                    verbose=True)
    

###############################################################################
if __name__ == '__main__':
    main()