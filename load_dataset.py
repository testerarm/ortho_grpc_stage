import os
import json

from opendm import context
from opendm import io
from grpc_opendm import types
from opendm import log
from opendm import system
from shutil import copyfile
from opendm import progress




# Load the Dataset, Extract features from images, // calls ODM Reconstruction at the end
class Load_Dataset(types.ODM_Stage): 
  def process(self, args, outputs):
        tree = types.ODM_Tree(args.project_path, args.gcp)
        outputs['tree'] = tree

        if args.time and io.file_exists(tree.benchmarking):
            # Delete the previously made file
            os.remove(tree.benchmarking)
            with open(tree.benchmarking, 'a') as b:
                b.write('ODM Benchmarking file created %s\nNumber of Cores: %s\n\n' % (system.now(), context.num_cores))
    
        # check if the extension is supported
        def supported_extension(file_name):
            (pathfn, ext) = os.path.splitext(file_name)
            return ext.lower() in context.supported_extensions

        # Get supported images from dir
        def get_images(in_dir):
            # filter images for its extension type
            log.ODM_DEBUG(in_dir)
            return [f for f in io.get_files_list(in_dir) if supported_extension(f)]

        # get images directory
        input_dir = tree.input_images
        images_dir = tree.dataset_raw

        if not io.dir_exists(images_dir):
            log.ODM_INFO("Project directory %s doesn't exist. Creating it now. " % images_dir)
            system.mkdir_p(images_dir)
            copied = [copyfile(io.join_paths(input_dir, f), io.join_paths(images_dir, f)) for f in get_images(input_dir)]

        # define paths and create working directories
        system.mkdir_p(tree.odm_georeferencing)
        if not args.use_3dmesh: system.mkdir_p(tree.odm_25dgeoreferencing)

        log.ODM_INFO('Loading dataset from: %s' % images_dir)

        # check if we rerun cell or not
        images_database_file = io.join_paths(tree.root_path, 'images.json')
        if not io.file_exists(images_database_file) or self.rerun():
            files = get_images(images_dir)
            if files:
                # create ODMPhoto list
                path_files = [io.join_paths(images_dir, f) for f in files]

                photos = []
                with open(tree.dataset_list, 'w') as dataset_list:
                    log.ODM_INFO("Loading %s images" % len(path_files))
                    for f in path_files:
                        photos += [types.ODM_Photo(f)]
                        dataset_list.write(photos[-1].filename + '\n')

                # Save image database for faster restart
                save_images_database(photos, images_database_file)
            else:
                log.ODM_ERROR('Not enough supported images in %s' % images_dir)
                exit(1)
        else:
            # We have an images database, just load it
            photos = load_images_database(images_database_file)

        log.ODM_INFO('Found %s usable images' % len(photos))

        # Create reconstruction object
        reconstruction = types.ODM_Reconstruction(photos)
        
        if tree.odm_georeferencing_gcp and not args.use_exif:
            reconstruction.georeference_with_gcp(tree.odm_georeferencing_gcp,
                                                 tree.odm_georeferencing_coords,
                                                 tree.odm_georeferencing_gcp_utm,
                                                 rerun=self.rerun())
        else:
            reconstruction.georeference_with_gps(tree.dataset_raw, 
                                                 tree.odm_georeferencing_coords, 
                                                 rerun=self.rerun())

        reconstruction.save_proj_srs(io.join_paths(tree.odm_georeferencing, tree.odm_georeferencing_proj))
        outputs['reconstruction'] = reconstruction