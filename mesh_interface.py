import os, math

from opendm import log
from opendm import io
from opendm import system
from opendm import context
from opendm import mesh
from opendm import gsd
from opendm import types


def mesh_3d(odm_mesh_folder,odm_mesh_ply, filter_point_cloud_path, max_concurrency):
    if not io.file_exists(odm_mesh_ply):
              log.ODM_INFO('Writing ODM Mesh file in: %s' % odm_mesh_ply)
              oct_tree =10
              samples = 1.0
              max_vertex = 200000
              point_weight = 4
              verbose = False
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
