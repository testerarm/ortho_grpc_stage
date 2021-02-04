import os, shutil

from opendm import log
from opendm import io
from opendm import system
from opendm import context
from opendm import types


def mvs_texturing(odm_mesh_ply,odm_texturing_path, opensfm_reconstruction_nvm):

        # default params
        params = {}
        params['data_term']='gmi',
        params['outlier_rem_type']= "gauss_clamping",
        params['skip_vis_test']=False,
        params['skip_glob_seam_leveling']=False,
        params['skip_loc_seam_leveling']=False,
        params['skip_hole_fill']=False,
        params['keep_unseen_faces']=False,
        params['tone_mapping']='none'

        r = ODMMvsTexStage(odm_mesh_ply, odm_texturing_path, opensfm_reconstruction_nvm, params)
        r.process()

class ODMMvsTexStage:
    def __init__(self,odm_mesh_ply,odm_texturing_path, opensfm_reconstruction_nvm, params):
        self.runs = []
        self.params = params
        self.odm_texturing_path = odm_texturing_path
        self.opensfm_reconstruction_nvm = opensfm_reconstruction_nvm
        self.odm_textured_model_obj = "odm_textured_model.obj"
        self.texturing_nadir_weight = 16
        self.odm_mesh = odm_mesh_ply
        
    def process(self):
        
        def add_run(nvm_file, primary=True, band=None):
            subdir = ""
          
            self.runs += [{
                    'out_dir': os.path.join(self.odm_texturing_path, subdir),
                    'model': self.odm_mesh,
                    'nadir': False,
                    'nvm_file': nvm_file
            }]

        
        add_run(self.opensfm_reconstruction_nvm)

       
        for r in self.runs:
            if not io.dir_exists(r['out_dir']):
                system.mkdir_p(r['out_dir'])

            odm_textured_model_obj = os.path.join(r['out_dir'], self.odm_textured_model_obj)

            if not io.file_exists(odm_textured_model_obj):
                log.ODM_INFO('Writing MVS Textured file in: %s'
                              % odm_textured_model_obj)

                # Format arguments to fit Mvs-Texturing app
                skipGeometricVisibilityTest = ""
                skipGlobalSeamLeveling = ""
                skipLocalSeamLeveling = ""
                skipHoleFilling = ""
                keepUnseenFaces = ""
                nadir = ""

                if (self.params.get('skip_vis_test')):
                    skipGeometricVisibilityTest = "--skip_geometric_visibility_test"
                if (self.params.get('skip_glob_seam_leveling')):
                    skipGlobalSeamLeveling = "--skip_global_seam_leveling"
                if (self.params.get('skip_loc_seam_leveling')):
                    skipLocalSeamLeveling = "--skip_local_seam_leveling"
                if (self.params.get('skip_hole_fill')):
                    skipHoleFilling = "--skip_hole_filling"
                if (self.params.get('keep_unseen_faces')):
                    keepUnseenFaces = "--keep_unseen_faces"
                if (r['nadir']):
                    nadir = '--nadir_mode'

                # mvstex definitions
                print('$$$$$$$$$$$$$$$$$$$$4')
                print(r['nvm_file'])
                print('$$$$$$$$$$$$$$$$$44')
                kwargs = {
                    'bin': context.mvstex_path,
                    'out_dir': io.join_paths(r['out_dir'], "odm_textured_model"),
                    'model': r['model'],
                    'dataTerm': 'gmi',
                    'outlierRemovalType': "gauss_clamping",
                    'skipGeometricVisibilityTest': skipGeometricVisibilityTest,
                    'skipGlobalSeamLeveling': skipGlobalSeamLeveling,
                    'skipLocalSeamLeveling': skipLocalSeamLeveling,
                    'skipHoleFilling': skipHoleFilling,
                    'keepUnseenFaces': keepUnseenFaces,
                    'toneMapping': 'none',
                    'nadirMode': nadir,
                    'nadirWeight': 2 ** self.texturing_nadir_weight - 1,
                    'nvm_file': r['nvm_file']
                }

                mvs_tmp_dir = os.path.join(r['out_dir'], 'tmp')

                # Make sure tmp directory is empty
                if io.dir_exists(mvs_tmp_dir):
                    log.ODM_INFO("Removing old tmp directory {}".format(mvs_tmp_dir))
                    shutil.rmtree(mvs_tmp_dir)

                # run texturing binary
                system.run('{bin} {nvm_file} {model} {out_dir} '
                        '-d {dataTerm} -o {outlierRemovalType} '
                        '-t {toneMapping} '
                        '{skipGeometricVisibilityTest} '
                        '{skipGlobalSeamLeveling} '
                        '{skipLocalSeamLeveling} '
                        '{skipHoleFilling} '
                        '{keepUnseenFaces} '
                        '{nadirMode} '
                        '-n {nadirWeight}'.format(**kwargs))
                
                # if args.optimize_disk_space:
                #     cleanup_files = [
                #         os.path.join(r['out_dir'], "odm_textured_model_data_costs.spt"),
                #         os.path.join(r['out_dir'], "odm_textured_model_labeling.vec"),
                #     ]
                #     for f in cleanup_files:
                #         if io.file_exists(f):
                #             os.remove(f # if args.optimize_disk_space:
                #     cleanup_files = [
                #         os.path.join(r['out_dir'], "odm_textured_model_data_costs.spt"),
                #         os.path.join(r['out_dir'], "odm_textured_model_labeling.vec"),
                #     ]
                #     for f in cleanup_files:
                #         if io.file_exists(f):
                #             os.remove(f))
                
                #progress += progress_per_run
                #self.update_progress(progress)
            else:
                log.ODM_WARNING('Found a valid ODM Texture file in: %s'
                                % odm_textured_model_obj)
        
        # if args.optimize_disk_space:
        #     for r in nonloc.runs:
        #         if io.file_exists(r['model']):
        #             os.remove(r['model'])
            
        #     undistorted_images_path = os.path.join(tree.opensfm, "undistorted", "images")
        #     if io.dir_exists(undistorted_images_path):
        #         shutil.rmtree(undistorted_images_path)



#  texturing = ODMMvsTexStage('mvs_texturing', args, progress=70.0,
#                                     data_term=args.texturing_data_term,
#                                     outlier_rem_type=args.texturing_outlier_removal_type,
#                                     skip_vis_test=args.texturing_skip_visibility_test,
#                                     skip_glob_seam_leveling=args.texturing_skip_global_seam_leveling,
#                                     skip_loc_seam_leveling=args.texturing_skip_local_seam_leveling,
#                                     skip_hole_fill=args.texturing_skip_hole_filling,
#                                     keep_unseen_faces=args.texturing_keep_unseen_faces,
#                                     tone_mapping=args.texturing_tone_mapping)