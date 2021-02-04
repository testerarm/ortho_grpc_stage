import os

from opendm import log
from opendm import io
from opendm import system
from opendm import context
from opendm import point_cloud
from opendm import types

def filter_points(odm_filterpoints_folder, mve_model, filter_points_ply_file, max_concurrency):

        if not os.path.exists(odm_filterpoints_folder): system.mkdir_p(odm_filterpoints_folder)

        pc_filter = 2.5
        pc_sample = 0
        verbose = False

        # check if reconstruction was done before
        if not io.file_exists(filter_points_ply_file):
            inputPointCloud = mve_model

            point_cloud.filter(inputPointCloud, filter_points_ply_file, 
                                standard_deviation=pc_filter, 
                                sample_radius=pc_sample,
                                verbose=verbose,
                                max_concurrency=max_concurrency)
        else:
            log.ODM_WARNING('Found a valid point cloud file in: %s' %
                            filter_points_ply_file)
        
        # if args.optimize_disk_space:
        #     os.remove(inputPointCloud)