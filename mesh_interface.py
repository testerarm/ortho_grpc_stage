import os, math

from opendm import log
from opendm import io
from opendm import system
from opendm import context
from opendm import mesh
from opendm import gsd
from opendm import types


def mesh_3d(args,odm_mesh_folder,odm_mesh_ply, filter_point_cloud_path, max_concurrency, reconstruction, current_path):
	oct_tree =10
        samples = 1.0
        max_vertex = 200000
        point_weight = 4
        verbose = False
	args['fast_orthophoto'] = True

	if args['use_3dmesh']:
	    if not io.file_exists(odm_mesh_ply):
		      log.ODM_INFO('Writing ODM Mesh file in: %s' % odm_mesh_ply)
		     
		      mesh.screened_poisson_reconstruction(filter_point_cloud_path,
		        odm_mesh_ply,
		        depth=oct_tree,
		        samples=samples,
		        maxVertexCount=max_vertex,
		        pointWeight=point_weight,
		        threads=max(1,  max_concurrency- 1), # poissonrecon can get stuck on some machines if --threads == all cores
		        verbose=verbose)

	    else:
		      log.ODM_WARNING('Found a valid ODM Mesh file in: %s' %
		                      odm_mesh_ply)

	if not args['use_3dmesh']:
          if not io.file_exists(odm_mesh_ply):
	      opensfm_reconstruction = io.join_paths(current_path,'reconstruction.json')
              reconstruction = reconstruction

              log.ODM_INFO('Writing ODM 2.5D Mesh file in: %s' % odm_mesh_ply)
              ortho_resolution = gsd.cap_resolution(args['orthophoto_resolution'], opensfm_reconstruction, 
                                                    ignore_gsd=args['ignore_gsd'],
                                                    ignore_resolution=not reconstruction.is_georeferenced(),
                                                    has_gcp=reconstruction.has_gcp()) / 100.0 
              
              dsm_multiplier = max(1.0, gsd.rounded_gsd(opensfm_reconstruction, default_value=4, ndigits=3, ignore_gsd=args['ignore_gsd']))
              
              # A good DSM size depends on the flight altitude.
              # Flights at low altitude need more details (higher resolution) 
              # Flights at higher altitude benefit from smoother surfaces (lower resolution)
              dsm_resolution = ortho_resolution * dsm_multiplier
              
              dsm_radius = dsm_resolution * math.sqrt(2)

              # Sparse point clouds benefits from using
              # a larger radius interolation --> less holes
              if args['fast_orthophoto']:
                  dsm_radius *= 2

              log.ODM_INFO('ODM 2.5D DSM resolution: %s' % dsm_resolution)
              
              mesh.create_25dmesh(filter_point_cloud_path, odm_mesh_ply,
                    dsm_radius=dsm_radius,
                    dsm_resolution=dsm_resolution, 
                    depth=oct_tree,
                    maxVertexCount=max_vertex,
                    samples=samples,
                    verbose=verbose,
                    available_cores=max_concurrency,
                    method='poisson' if args['fast_orthophoto'] else 'gridded',
                    smooth_dsm=not args['fast_orthophoto'])
          else:
              log.ODM_WARNING('Found a valid ODM 2.5D Mesh file in: %s' %
                              odm_mesh_ply)
