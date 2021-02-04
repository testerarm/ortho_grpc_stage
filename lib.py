import os
import io
import time
import glob
import grpc
import traceback

from concurrent import futures
from concurrent.futures import ThreadPoolExecutor

import faulthandler
faulthandler.enable()


import sys
sys.path.append('../')
sys.path.append('./opensfm/opensfm/')
sys.path.append('/home/j/ODM-master/SuperBuild/src/opensfm')
sys.path.append('/home/j/ODM-master/SuperBuild/install/lib/python2.7/dist-packages')
sys.path.append('/home/j/ODM-master/SuperBuild/install/lib')


import sendFile_pb2, sendFile_pb2_grpc

CHUNK_SIZE = 1024 * 1024  # 1MB

from geopy import distance

from opendm import log
from opendm import config
from opendm import system
from opendm import io
from opendm import gsd

from collections import defaultdict

import stages

from opensfm import exif

import opensfm_interface

from opensfm_modified import tracking
from opensfm_modified import new_matching
from opensfm_modified import reconstruction

import mve_interface
import mvs_texturing
import filterpoint_interface
import mesh_interface


dir_path = os.path.dirname(os.path.realpath(__file__))

print('dir path: ' + str(dir_path))


def get_file_chunks(filename):
    print('file name in get file chucks ' + filename)
    with open(filename, 'rb') as f:
        while True:
            piece = f.read(CHUNK_SIZE)
            if len(piece) == 0:
                return
            yield sendFile_pb2.Chunk(content=piece)
       


def save_chunks_to_file(chunks, filename):
    print('save chuck size: ' + str(CHUNK_SIZE)+ ' Bytes  to filename: ' + str(filename))

    with open(filename, 'wb') as f:
        for chunk in chunks:
            f.write(chunk.content)


class FileClient:
    def __init__(self, address, nodeid):
        # strongly typed for now
        self.nodeid = str(nodeid)
        print(nodeid)
        print('address' + str(address))
        channel = grpc.insecure_channel(address) 
        self.stub = sendFile_pb2_grpc.FileServiceStub(channel)

    def sendTask(self, taskName, this_nodeid, taskDir, pairs=[]):


        #send Task -> task name 

        try:
            print('task ' + str(taskName) + ' id ' + str(this_nodeid))

            
           

            task = sendFile_pb2.Task(taskName = taskName, nodeId='node'+str(this_nodeid))
            if (taskName == 'feature_match_pairs'):
                task.feature_pair.pair1 = pairs[0]
                task.feature_pair.pair2 = pairs[1]

            response = self.stub.sendTask(task)
            response_dir = dir_path + '/node' + str(this_nodeid) + taskDir
            if not os.path.isdir(response_dir):
                system.mkdir_p(response_dir)
            print(response_dir)

            file_chunk_list = []
            current_filename = ''
            for each in response:
                print('file name ' + str(each.filename))
                if current_filename == '': 
                    current_filename = each.filename
                if each.filename != current_filename:
                    #empty the file chucks into the file
                    print(current_filename)
                    save_chunks_to_file(file_chunk_list, response_dir + '/' + current_filename)

                    current_filename = each.filename
                    file_chunk_list = []
                    file_chunk_list.append(each)

                else:
                    file_chunk_list.append(each)
                
                #print(each.content)
            if len(file_chunk_list) > 0:
                if current_filename == 'camera_models.json':
                    response_dir = dir_path + '/node' + str(this_nodeid)
                save_chunks_to_file(file_chunk_list, response_dir + '/' + current_filename)


            print('len of file chuck ')
            print(len(file_chunk_list))
            print(current_filename)
            





            # print(str(response))
            # print(type(response))
        
            return response

        except Exception as e:
            print(' Exception : ' + str(e.message))
            print(traceback.print_exc())







    def upload(self, file_path, filename_list):
        

        #https://stackoverflow.com/questions/45071567/how-to-send-custom-header-metadata-with-python-grpc
        folder = file_path.split('/')[-1]
        print('folder ' + str(folder))


        for each_file in filename_list:   
                chunks_generator = get_file_chunks(io.join_paths(file_path, each_file))
                print('folder here before call ' + str(folder))
                if(folder is None):
                    print('folder is none')
                #foldername = 'images'
                call_future , call = self.stub.upload.with_call(chunks_generator, metadata=(('node-id', 'node'+self.nodeid),('filename', each_file), ('folder', folder)))
                #call_future.add_done_callback(self.process_response)
                #print('here in client upload')
                print(call_future)
        # else:
        #     images = glob.glob(in_file_name_or_file_path)
        #     #print(images)
        #     for each in images: 
                
        #         chunks_generator = get_file_chunks(each)
        #         filename = each.split('/')[-1]
        #         response, call = self.stub.upload.with_call(chunks_generator, metadata=(('node-id', self.nodeid),('filename', filename)))
                #print(response.length)

            # to do loop through the files 

        #assert response.length == os.path.getsize(in_file_name_or_file_path)
        return call_future

    def download(self, target_name, out_file_name):
        response = self.stub.download(sendFile_pb2.Request(name=target_name))
        save_chunks_to_file(response, out_file_name)





"""""

Server Compute Functions

"""""

def sfm_extract_metadata_list_of_images(image_path,  opensfm_config, node_file_path):

    try:
        ref_image = os.listdir(image_path)
        print('inside sfm extract')
        print(str(ref_image))
        camera_models = {}
        for i in range(len(ref_image)):
            each = ref_image[i]
            print('path ' + io.join_paths(image_path, each))
            if os.path.isfile(io.join_paths(image_path, each)):
                print('path is valid')
                d  = opensfm_interface.extract_metadata_image(io.join_paths(image_path, each), opensfm_config)
                if d['camera'] not in camera_models:
                    camera = exif.camera_from_exif_metadata(d, opensfm_config)
                    camera_models[d['camera']] = camera
                print('nodefile path ' + str(node_file_path))
                opensfm_interface.save_exif(io.join_paths(node_file_path,'exif'),each,d)
            
            else:
                print('path is not valid')
        opensfm_interface.save_camera_models(node_file_path, camera_models)
           

        return True
    except Exception as e:
        print(e.message)
        print(traceback.print_exc())
        print(traceback.print_exception())
        
        return False
    



def sfm_detect_features(ref_image, current_path, opensfm_config):

    """
     feature path 
     image path
     opensfm config

    """
    print('detect feature' + str(current_path))

    feature_path = current_path + '/features'
    
    image_path = current_path + '/images/'

    try: 
        for each in ref_image:
            opensfm_interface.detect(feature_path, image_path+each,each ,opensfm_config)
    except Exception as e:
        print(traceback.print_exc())
        return False
    
    return True

def sfm_feature_matching(current_path, ref_image, cand_images , opensfm_config):

    """

    image_path
    ref_image : list of images 
    opensfm config


    """
    try: 

        # load exif is needed
        print('feature matching')

        pairs_matches, preport = new_matching.match_images(current_path+'/', ref_image, ref_image, opensfm_config)
        print(pairs_matches)
        new_matching.save_matches(current_path+'/', ref_image, pairs_matches)

        #tracking.load_matches(current_path, ref_image)
    except Exception as e:
        print(traceback.print_exc())
        return False

    return 

def sfm_feature_matching_pairs(current_path, ref_image, cand_images , opensfm_config):

    """

    image_path
    ref_image : list of images 
    opensfm config


    """
    try: 

        # load exif is needed
        print('feature matching')

        pairs_matches, preport = new_matching.match_images(current_path+'/', ref_image, ref_image, opensfm_config)
        print(pairs_matches)

        new_matching.save_matches(current_path+'/', ref_image, pairs_matches)

        #tracking.load_matches(current_path, ref_image)
        return pairs_matches
    except Exception as e:
        print(traceback.print_exc())
        return None

    return 

def sfm_create_tracks(current_path, ref_image, opensfm_config, matches = {}):
    """
    
    path to features 
    ref_image list 
    opensfm config


    """

    try: 
        features, colors = tracking.load_features(current_path+'/features', ref_image, opensfm_config)
        if bool(matches) is False:
            matches = tracking.load_matches(current_path, ref_image)
    

        print('feature length: ' + str(len(features)))

        graph = tracking.create_tracks_graph(features, colors, matches,
                                            opensfm_config)

        opensfm_interface.save_tracks_graph(graph, current_path)
    
    except Exception as e:
        print(traceback.print_exc())
        return False
    
    return True


def sfm_opensfm_reconstruction(current_path, opensfm_config):


    try:
        graph = opensfm_interface.load_tracks_graph(current_path)
        report, reconstructions = reconstruction.incremental_reconstruction(current_path, graph, opensfm_config)
        opensfm_interface.save_reconstruction(current_path,reconstructions)
    except Exception as e:
        print(traceback.print_exc())
        return False
    return True 

def sfm_max_undistort_image_size(current_path, image_path):
    outputs = {}
    photos = []
    from opendm import photo
    from opendm import types

    ref_image = os.listdir(image_path)
    
    try: 
        for each in ref_image:
            photos += [types.ODM_Photo(os.path.join(image_path, each))]
        
    
        # get match image sizes
        outputs['undist_image_max_size'] = max(
            gsd.image_max_size(photos, 5.0, current_path+'reconstruction.json'),
            0.1
        )        
        # print(outputs)

        # #undistort image dataset: 

        #
    except Exception as e:
        print(traceback.print_exc())
        return False

    return outputs['undist_image_max_size'] 


def sfm_undistort_image(current_path, opensfm_config):
    
    try:
    
        opensfm_interface.opensfm_undistort(current_path, opensfm_config)
    except Exception as e:
        print(traceback.print_exc())
        return False
    return True

def sfm_export_visual_sfm(current_path, opensfm_config):


    try:

        opensfm_interface.open_export_visualsfm(current_path, opensfm_config)
    except Exception as e:
        print(traceback.print_exc())
        return False

    return 


def sfm_compute_depthmaps(current_path, opensfm_config):

    try:
        opensfm_interface.open_compute_depthmaps(current_path, opensfm_config)
    except Exception as e:
        print(traceback.print_exc())
        return False
    
    return True 


def mve_dense_reconstruction(current_path, max_concurrency):

    try:
        mve_file_path = os.path.join(current_path,'mve')
    
        mve_interface.mve_dense_recon(sfm_max_undistort_image_size(current_path, os.path.join(current_path, 'images')), mve_file_path, max_concurrency)
    except Exception as e:
        print(traceback.print_exc())
        return False
    
    return True


def mve_makescene_function(current_path, max_concurrency):

    try: 
        mve_file_path =os.path.join(current_path,'mve')
        nvm_file = os.path.join(current_path,'undistorted', 'reconstruction.nvm')
        mve_interface.mve_makescene(nvm_file, mve_file_path, max_concurrency)
    except Exception as e:
        print(traceback.print_exc())
        return False

    return True 


def mve_scene2pset_function(current_path, max_concurrency):

    try:
        mve_file_path = os.path.join(current_path,'mve')
        mve_model = io.join_paths(mve_file_path, 'mve_dense_point_cloud.ply')
        mve_interface.mve_scene2pset(mve_file_path, mve_model,sfm_max_undistort_image_size(current_path, os.path.join(current_path, 'images')),max_concurrency)
    except Exception as e:
        print(traceback.print_exc())
        return False

    return True 

def mve_cleanmesh_function(current_path, max_concurrency):
    
    try:
        mve_file_path = os.path.join(current_path,'mve')
        mve_model = io.join_paths(mve_file_path, 'mve_dense_point_cloud.ply')
        mve_interface.mve_cleanmesh(0.6, mve_model, max_concurrency)
    except Exception as e:
        print(traceback.print_exc())
        return False
    return True


def odm_filterpoints_function(current_path, max_concurrency):

    try:
        mve_file_path = os.path.join(current_path,'mve')
        mve_model = io.join_paths(mve_file_path, 'mve_dense_point_cloud.ply')

        odm_filterpoints = os.path.join(current_path,'filterpoints')
        filterpoint_cloud = io.join_paths(odm_filterpoints, "point_cloud.ply")

        filterpoint_interface.filter_points(odm_filterpoints, mve_model, filterpoint_cloud, max_concurrency)
    except Exception as e:
        print(traceback.print_exc())
        return False
    return True

def odm_mesh_function(current_path, max_concurrency):


    try:
    
        odm_filterpoints = os.path.join(current_path,'filterpoints')
        filterpoint_cloud = io.join_paths(odm_filterpoints, "point_cloud.ply")

        odm_mesh_folder= os.path.join(current_path,'mesh')
        odm_mesh_ply = io.join_paths(odm_mesh_folder, "odm_mesh.ply")
        mesh_interface.mesh_3d(odm_mesh_folder, odm_mesh_ply, filterpoint_cloud, max_concurrency)
    except Exception as e:
        print(traceback.print_exc())
        return False

    return True

def odm_texturing_function(current_path):
      
    try:   
        mvs_folder= os.path.join(current_path,'mvs')
        odm_mesh_folder= cos.path.join(current_path,'mesh')
        odm_mesh_ply = io.join_paths(odm_mesh_folder, "odm_mesh.ply")
        nvm_file = os.path.join(current_path,'undistorted', 'reconstruction.nvm')

        mvs_texturing.mvs_texturing(odm_mesh_ply, mvs_folder, nvm_file)  
    except Exception as e:
        print(traceback.print_exc())
        return False

    return True





class FileServer(sendFile_pb2_grpc.FileServiceServicer):
    def __init__(self, port, node_id, dataset_path):
        self.port = port
        self.node_id = str(node_id)
        node_path = io.join_paths(dir_path, 'node'+self.node_id)
        self.dataset_dir = dataset_path
        #configuration
        # args  = config.config()
        # args.project_path = "./dataset/images"
        self.datapath = 'dataset'
        # data = ODMLoadDatasetStage(self.datapath , args, progress=5.0,
        #                                   verbose=args.verbose)

        #distance to include the image in meters
        self.include_distance = 10

        #run the dataset layer
        #data.run()

        print('sfm')
        print(self.datapath)

        #opensfm configuration

        opensfm_config = opensfm_interface.setup_opensfm_config(self.datapath)
        self.opensfm_config = opensfm_config

        #extract metadata 

        # camera_models = {}
        # current_path = '/home/j/ODM-master/grpc_stages/node1/'

        # ref_image = ['DJI_0019.JPG', 'DJI_0018.JPG','DJI_0020.JPG','DJI_0021.JPG','DJI_0022.JPG','DJI_0023.JPG','DJI_0024.JPG'
        # ,'DJI_0025.JPG','DJI_0026.JPG','DJI_0027.JPG','DJI_0028.JPG','DJI_0029.JPG','DJI_0030.JPG','DJI_0031.JPG','DJI_0032.JPG','DJI_0033.JPG','DJI_0034.JPG','DJI_0035.JPG']
        # cand_images = ['DJI_0019.JPG', 'DJI_0018.JPG','DJI_0020.JPG','DJI_0021.JPG','DJI_0022.JPG','DJI_0023.JPG','DJI_0024.JPG'
        # ,'DJI_0025.JPG','DJI_0026.JPG','DJI_0027.JPG','DJI_0028.JPG','DJI_0029.JPG','DJI_0030.JPG','DJI_0031.JPG','DJI_0032.JPG','DJI_0033.JPG','DJI_0034.JPG','DJI_0035.JPG']

        # for each in ref_image:
        #     d  = opensfm_interface.extract_metadata_image('/home/j/ODM-master/grpc_stages/node1/'+each, opensfm_config)
        #     if d['camera'] not in camera_models:
        #         camera = exif.camera_from_exif_metadata(d, opensfm_config)
        #         camera_models[d['camera']] = camera 
             #opensfm_interface.save_exif('/home/j/ODM-master/grpc_stages/node1/exif', each,d)
         #opensfm_interface.save_camera_models('/home/j/ODM-master/grpc_stages/node1/', camera_models)
        
        # #c  = opensfm_interface.extract_metadata_image('/home/j/ODM-master/grpc_stages/node1/DJI_0019.JPG', opensfm_config)
       

        # print(d)
        # print(camera_models)
        # #opensfm_interface.save_exif('/home/j/ODM-master/grpc_stages/node1/', 'DJI_0019.JPG', c)
        
        # #save the exif metadata to file in a folder
        # # send extracted metedata and camera model back

 

        # #feature extraction
        # for each in ref_image:
        #     opensfm_interface.detect(current_path+'features', current_path+each,each ,opensfm_config)


        # #opensfm_interface.detect(current_path+'features', current_path+'DJI_0019.JPG','DJI_0019.JPG' ,opensfm_config)




        # #feature matching

       

        # pairs_matches, preport = new_matching.match_images(current_path, ref_image, cand_images, opensfm_config)
        # new_matching.save_matches(current_path, ref_image, pairs_matches)
        # print('matching')
        



        # #create tracks first

        # features, colors = tracking.load_features(current_path+'features', ref_image, opensfm_config)
        # matches = tracking.load_matches(current_path, ref_image)
        # graph = tracking.create_tracks_graph(features, colors, matches,
        #                                      opensfm_config)

        # opensfm_interface.save_tracks_graph(graph, current_path)



        # #reconstruction


        # # load tracks graph

        # graph = opensfm_interface.load_tracks_graph(current_path)
        # report, reconstructions = reconstruction.incremental_reconstruction(current_path, graph, opensfm_config)

        # opensfm_interface.save_reconstruction(current_path,reconstructions)
        # #opensfm_interface.save_report(io.json_dumps(report), 'reconstruction.json')
      
        # outputs = {}
        # photos = []
        # from opendm import photo
        # from opendm import types
        
        # for each in ref_image:
        #     photos += [types.ODM_Photo(current_path+each)]
          
        
        # # get match image sizes
        # outputs['undist_image_max_size'] = max(
        #     gsd.image_max_size(photos, 5.0, current_path+'reconstruction.json'),
        #     0.1
        # )        
        # print(outputs)

        # #undistort image dataset: 

        # opensfm_interface.opensfm_undistort(current_path, opensfm_config)


        # #export visualsfm

        # opensfm_interface.open_export_visualsfm(current_path, opensfm_config)

        # #compute depthmaps 

        # opensfm_interface.open_compute_depthmaps(current_path, opensfm_config)

      
        # #mve stage 1 makescene

        # #input compute depthmaps file
        
        # mve_file_path = '/home/j/ODM-master/grpc_stages/node1/mve'
        # nvm_file = '/home/j/ODM-master/grpc_stages/node1/undistorted/reconstruction.nvm'
        # mve_interface.mve_makescene(nvm_file, mve_file_path, 2)


        # #mve stage 2 dense reconstruction

        # mve_interface.mve_dense_recon(outputs['undist_image_max_size'], mve_file_path, 2)

        # #mve stage 3 scene2pset_path
        # mve_model = io.join_paths(mve_file_path, 'mve_dense_point_cloud.ply')
        # mve_interface.mve_scene2pset(mve_file_path, mve_model,outputs['undist_image_max_size'],2)

        # #mve stage 4 clean_mesh
        # mve_interface.mve_cleanmesh(0.6, mve_model, 2)



        # # filterpoint cloud
        # odm_filterpoints = '/home/j/ODM-master/grpc_stages/node1/filterpoints'
        # filterpoint_cloud = io.join_paths(odm_filterpoints, "point_cloud.ply")

        # filterpoint_interface.filter_points(odm_filterpoints, mve_model, filterpoint_cloud,2)

        # #meshing stage
        # odm_mesh_folder= '/home/j/ODM-master/grpc_stages/node1/mesh'
        # odm_mesh_ply = io.join_paths(odm_mesh_folder, "odm_mesh.ply")
        # mesh_interface.mesh_3d(odm_mesh_folder, odm_mesh_ply, filterpoint_cloud, 2)

        # #texturing stage

        # mvs_folder= '/home/j/ODM-master/grpc_stages/node1/mvs'
        # mvs_texturing.mvs_texturing(odm_mesh_ply, mvs_folder, nvm_file)       

        #https://stackoverflow.com/questions/45071567/how-to-send-custom-header-metadata-with-python-grpc


        class Servicer(sendFile_pb2_grpc.FileServiceServicer):
            def __init__(self):
                self.tmp_file_name = './dataset2/IMG_2359.JPG'


            def upload(self, request_iterator, context):
                # client uploads images to this node
                #request iterator is the file iterator through the chuncks

                #self.tmp_file_name is the name to save the file chucks to 
                nodeid = ''
                filename = ''
                folder = ''
                for key, value in context.invocation_metadata():
                    
                    if(key == 'node-id'):
                        nodeid = value
                        #check if there is a dir for the node id
                        system.mkdir_p('node'+str(node_id)+'/'+nodeid)
                    if key == 'filename':
                        filename = value
                    if key == 'folder':
                        folder = value
                        print('node_id '+ str(node_id))
                        system.mkdir_p('node'+str(node_id)+'/'+nodeid+'/'+folder)

                 
                    print('Received initial metadata: key=%s value=%s' % (key, value))
                #print(os.path.dirname(os.path.abspath(__file__)))
                if (nodeid != '' and filename  != ''):
                    save_chunks_to_file(request_iterator, os.path.join('node'+str(node_id),nodeid, folder, filename))

                    return sendFile_pb2.UploadStatus(message = " Successul ", code=sendFile_pb2.UploadStatusCode.Ok) 
                else:
                    print('bad node id and bad filename')
                    # reply = sendFile_pb2.UploadStatus()
                    # reply.Message = " Failed "
                    # reply.c
                    return sendFile_pb2.UploadStatus(message = " Failure ", code=sendFile_pb2.UploadStatusCode.Failed)

            def download(self, request, context):
                if request.name:
                    return get_file_chunks(self.tmp_file_name)

            def sendTask(self, request, context):
                taskName = request.taskName
                nodeid = request.nodeId
                print('here in send Task ' + str(taskName) + ' ' + str(nodeid))

                #node_path is the path of this node
                print(node_path)
                req_node_path = io.join_paths(node_path, str(nodeid))
                print(req_node_path)
                try:
                    if(taskName == 'exif'):
                        # check 
                        
                            print('run sfm extract metadata')
                           
                            image_path =   req_node_path + '/images'
                            print('image path ' + str(image_path))
                            is_complete = sfm_extract_metadata_list_of_images(image_path,opensfm_config, req_node_path)
                            
                            if (is_complete):
                                print('is complete')
                                #files to send back to the main node
                                # #camera model.json and <nodeid>/ exif folder
                                exif_folder_path = req_node_path + '/exif'
                                print(exif_folder_path)
                                
                            
                                exif_list =  os.listdir(exif_folder_path)
                                print(exif_list)
                                exif_list.append('camera_models.json')

                                for each_file in exif_list:
                                    folder_path = exif_folder_path
                                    if each_file == 'camera_models.json':
                                        folder_path = req_node_path

            


                                    
                                    with open(io.join_paths(folder_path, each_file), 'rb') as f:
                                        while True:
                                            piece = f.read(CHUNK_SIZE)
                                            if len(piece) == 0:
                                                break
                                            yield sendFile_pb2.NewChunk(filename=each_file  ,content=piece)

                                #send camera model.json




                                return
                            else: 
                                print('not complete')
                    elif(taskName == 'detect_features'):

                        print('detect features')
                       
                   
                        image_path = req_node_path + '/images'
                        print('image path ' + str(image_path))
                        image_list = os.listdir(image_path)

                        is_complete =sfm_detect_features(image_list,req_node_path ,opensfm_config)



                        if(is_complete):

                            detect_folder_path = req_node_path + '/features'
                            print(detect_folder_path)


                            _list =  os.listdir(detect_folder_path)
                            print(_list)

                            for each_file in _list:
                                
                                with open(io.join_paths(detect_folder_path, each_file), 'rb') as f:
                                    while True:
                                        piece = f.read(CHUNK_SIZE)
                                        if len(piece) == 0:
                                            break
                                        yield sendFile_pb2.NewChunk(filename=each_file  ,content=piece)

                            return





                    elif(taskName == 'feature_matching'):

                   
                        image_path =   req_node_path + '/images'
                        print('image path ' + str(image_path))
                        image_list =os.listdir(image_path)

                        is_complete = sfm_feature_matching(req_node_path, image_list, image_list, opensfm_config)
                        

                        if(is_complete):

                            detect_folder_path = req_node_path + '/features'
                            print(detect_folder_path)


                            _list =  os.listdir(detect_folder_path)
                            print(_list)

                            for each_file in _list:
                                
                                with open(io.join_paths(detect_folder_path, each_file), 'rb') as f:
                                    while True:
                                        piece = f.read(CHUNK_SIZE)
                                        if len(piece) == 0:
                                            break
                                        yield sendFile_pb2.NewChunk(filename=each_file  ,content=piece)



                        return
                    elif(taskName == 'feature_match_pairs'):

                        image_path =   req_node_path + '/images'
                        
                        print('image path ' + str(image_path))
                        #image_list =os.listdir(image_path)
                        pair1 = request.feature_pair.pair1
                        pair2 = request.feature_pair.pair2

                        image_list = [pair1, pair2]

                        print('pairs ' + str(pair1) + ' ' + str(pair2))

                        pairs_matches = sfm_feature_matching_pairs(req_node_path, image_list , image_list, opensfm_config)
                       

                        print('here in main taskName')
                        print(pairs_matches)
                        filename = pair1+'-'+pair2


                        # save pair matches in a file 
                        # send it to client

                        opensfm_interface.save_matches(req_node_path, filename, pairs_matches)

                        detect_folder_path = req_node_path + '/matches'
                        with open(io.join_paths(detect_folder_path, filename+'_matches.pkl.gz'), 'rb') as f:
                                    while True:
                                        piece = f.read(CHUNK_SIZE)
                                        if len(piece) == 0:
                                            break
                                        yield sendFile_pb2.NewChunk(filename=filename+'_matches.pkl.gz'  ,content=piece)


                        return 

                        


                       


                        
                    
                    elif(taskName == 'create_tracks'):

                        print('create_tracks')
                        image_path =   req_node_path + '/images'
                        print('image path ' + str(image_path))
                        image_list = os.listdir(image_path)

                        sfm_create_tracks(req_node_path, image_list, opensfm_config)

                    
                    
                    elif(taskName == 'opensfm_reconstruction'):

                        sfm_opensfm_reconstruction(req_node_path, opensfm_config)
                        
                        return 
                   
                    elif(taskName == 'undistort_image'):

                        sfm_undistort_image(req_node_path, opensfm_config)

                        return 
                    elif(taskName == 'export_visualsfm'):

                        sfm_export_visual_sfm(req_node_path, opensfm_config)
                        return
                    elif(taskName == 'compute_depthmaps'):
                        sfm_compute_depthmaps(req_node_path, opensfm_config)
                        return
                    elif(taskName == 'dense_reconstruction'):
                        mve_dense_reconstruction(req_node_path)
                        return
                    elif(taskName == 'makescene_function'):
                        mve_makescene_function(req_node_path, 2)
                        return
                    elif(taskName == 'scene2pset'):
                        mve_scene2pset_function(req_node_path, 2)
                        return
                    elif(taskName == 'cleanmesh'):
                        mve_cleanmesh_function(req_node_path, 2)
                        return
                    elif(taskName == 'odm_filterpoints'):
                        odm_filterpoints_function(req_node_path,2)
                        return
                    elif(taskName == 'odm_mesh'):
                        odm_mesh_function(req_node_path, 2)
                        return
                    elif(taskName == 'odm_texturing'):
                        odm_texturing_function(req_node_path)
                        return
                    
                    
    

                except Exception as e:
                        print(e.message)
                        print(traceback.print_exc())

                        return

                            

                    









                #metadata use image name 
                #use node id 

                #opensfm compute

                # detect feature

                # 


                # if(taskName == "compute_image_feature"):

                # elif(taskName == 'compute_matching_two_images'):0
               


                # elif(taskName == 'compute_'):

                # elif(taskName == ''):

                


                

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=4), options = [
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024)
        ])

        #self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        sendFile_pb2_grpc.add_FileServiceServicer_to_server(Servicer(), self.server)


        neighbor_ip = ['50001', '50002']
        self.has_neighbor = defaultdict(lambda: "Node not present.")

        # tuple (false as any response from neighbor, filelocation)
        neighbor_response = 0 #increment neighbors response as each neighbor respond
        for each in neighbor_ip:
            self.has_neighbor[each] = (False, "")
        
        self.leader = True

        # if(self.leader):
        #     while(neighbor_response != len(neighbor_ip)):
                # wait for all the neighbors to respond 

            #finish waiting 

            #send compute task to each node

            #send images to all nodes
        
        


            

        # port 50001
        # port 50002

    def start(self, port):
        print(port)
        self.server.add_insecure_port('[::]:'+str(port))
        self.server.start()

        print("end of init")

        try:
            while True:
                time.sleep(60*60*24)
        except KeyboardInterrupt:
            self.server.stop(0)
