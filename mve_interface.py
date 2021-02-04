import shutil, os, glob, math

from opendm import log
from opendm import io
from opendm import system
from opendm import context
from opendm import point_cloud
from opendm import types
#from opendm.osfm import OSFMContext

def mve_makescene(nvm_file, mve_file_path, max_concurrency):
    system.run('%s "%s" "%s"' % (context.makescene_path, nvm_file, mve_file_path), env_vars={'OMP_NUM_THREADS': max_concurrency})

def mve_dense_recon(undist_image_max_size, mve_file_path,  max_concurrency):

    depthmap_resolution = 640
    max_pixels = depthmap_resolution * depthmap_resolution

    if undist_image_max_size * undist_image_max_size <= max_pixels:
        mve_output_scale = 0
    else:
        ratio = float(undist_image_max_size*undist_image_max_size) / float(max_pixels)
        mve_output_scale = int(math.ceil(math.log(ratio) / math.log(4.0)))

    dmrecon_config = [
        "-s%s" % mve_output_scale,
        "--progress=fancy",
        "--local-neighbors=2",
        # "--filter-width=3",
    ]

    retry_count = 1
    while retry_count < 10:
        try:
            system.run('%s %s "%s"' % (context.dmrecon_path, ' '.join(dmrecon_config), mve_file_path), env_vars={'OMP_NUM_THREADS': max_concurrency})
            break
        except Exception as e:
            if str(e) == "Child returned 134" or str(e) == "Child returned 1":
                retry_count += 1
                log.ODM_WARNING("Caught error code, retrying attempt #%s" % retry_count)
            else:
                raise e

def mve_scene2pset(mve_file_path, mve_model_path, undist_image_max_size, max_concurrency):
    depthmap_resolution = 640
    max_pixels = depthmap_resolution * depthmap_resolution

    if undist_image_max_size * undist_image_max_size <= max_pixels:
        mve_output_scale = 0
    else:
        ratio = float(undist_image_max_size*undist_image_max_size) / float(max_pixels)
        mve_output_scale = int(math.ceil(math.log(ratio) / math.log(4.0)))

    scene2pset_config = [
        "-F%s" % mve_output_scale
    ]

    # run scene2pset
    system.run('%s %s "%s" "%s"' % (context.scene2pset_path, ' '.join(scene2pset_config), mve_file_path, mve_model_path), env_vars={'OMP_NUM_THREADS': max_concurrency})

def mve_cleanmesh(mve_confidence, mve_model, max_concurrency):
    if mve_confidence > 0:
                mve_filtered_model = io.related_file_path(mve_model, postfix=".filtered")
                system.run('%s -t%s --no-clean --component-size=0 "%s" "%s"' % (context.meshclean_path, min(1.0, mve_confidence), mve_model, mve_filtered_model), env_vars={'OMP_NUM_THREADS': max_concurrency})

                # if io.file_exists(mve_filtered_model):
                #     os.remove(tree.mve_model)
                #     os.rename(mve_filtered_model, tree.mve_model)
                # else:
                #     log.ODM_WARNING("Couldn't filter MVE model (%s does not exist)." % mve_filtered_model)
        
            # if args.optimize_disk_space:
            #     shutil.rmtree(tree.mve_views)
    else:
            log.ODM_WARNING('Found a valid MVE reconstruction file in: %s' %
                            mve_model)