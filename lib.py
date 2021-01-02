import os
import io
import grpc
import time
import glob
import asyncio
from grpc import aio


from concurrent import futures



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



def get_file_chunks(filename):
    with open(filename, 'rb') as f:
        while True:
            piece = f.read(CHUNK_SIZE)
            if len(piece) == 0:
                return
            yield sendFile_pb2.Chunk(Content=piece)
       


def save_chunks_to_file(chunks, filename):
    print('save chuck size: ' + str(CHUNK_SIZE)+ ' Bytes  to filename: ' + str(filename))
    with open(filename, 'wb') as f:
        for chunk in chunks:
            f.write(chunk.Content)


class FileClient:
    def __init__(self, address, nodeid):
        # strongly typed for now
        self.nodeid = nodeid
        channel = grpc.insecure_channel(address) 
        self.stub = sendFile_pb2_grpc.FileServiceStub(channel)

    def upload(self, in_file_name_or_file_path,is_dir=False):
        

        #https://stackoverflow.com/questions/45071567/how-to-send-custom-header-metadata-with-python-grpc

        if not is_dir:
            chunks_generator = get_file_chunks(in_file_name_or_file_path)
            response, call = self.stub.upload.with_call(chunks_generator, metadata=(('node-id', self.nodeid),('filename', in_file_name_or_file_path)))
        else:
            images = glob.glob(in_file_name_or_file_path)
            #print(images)
            for each in images: 
                
                chunks_generator = get_file_chunks(each)
                filename = each.split('/')[-1]
                response, call = self.stub.upload.with_call(chunks_generator, metadata=(('node-id', self.nodeid),('filename', filename)))
                #print(response.length)

            # to do loop through the files 

        #assert response.length == os.path.getsize(in_file_name_or_file_path)
        return response

    def download(self, target_name, out_file_name):
        response = self.stub.download(sendFile_pb2.Request(name=target_name))
        save_chunks_to_file(response, out_file_name)


    def compute(self, request, context):
        # Send Compute Task


        #
        return 0





"""""

Server Compute Functions

"""""


def sfm_extract_metadata_one_image(image_file_path, opensfm_config):

    return 

def sfm_extract_features_one_image():

    return

def sfm_match_images():
    return 


def sfm_detect_features():
    return 

def sfm_feature_matching():
    return 

def sfm_create_tracks():
    return 


def sfm_opensfm_reconstruction():
    return 

def sfm_max_undistort_image_size():
    return 


def sfm_undistort_image():
    return 

def sfm_export_visual_sfm():
    return 


def sfm_compute_deptmaps():
    return 


def mve_dense_reconstruction():
    return 


def mve_makescene_function():

    return 


def mve_scene2pset_function():
    return 

def mve_cleanmesh_function():
    return 


def odm_filterpoints_function():

    return 

def odm_mesh_function():
    return 

def odm_texturing_function():
    return 


class FileServer(sendFile_pb2_grpc.FileServiceServicer):
    def __init__(self):
        self.nodeid = 1
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

        #extract metadata 

        camera_models = {}
        current_path = '/home/j/ODM-master/grpc_stages/node1/'

        ref_image = ['DJI_0019.JPG', 'DJI_0018.JPG','DJI_0020.JPG','DJI_0021.JPG','DJI_0022.JPG','DJI_0023.JPG','DJI_0024.JPG'
        ,'DJI_0025.JPG','DJI_0026.JPG','DJI_0027.JPG','DJI_0028.JPG','DJI_0029.JPG','DJI_0030.JPG','DJI_0031.JPG','DJI_0032.JPG','DJI_0033.JPG','DJI_0034.JPG','DJI_0035.JPG']
        cand_images = ['DJI_0019.JPG', 'DJI_0018.JPG','DJI_0020.JPG','DJI_0021.JPG','DJI_0022.JPG','DJI_0023.JPG','DJI_0024.JPG'
        ,'DJI_0025.JPG','DJI_0026.JPG','DJI_0027.JPG','DJI_0028.JPG','DJI_0029.JPG','DJI_0030.JPG','DJI_0031.JPG','DJI_0032.JPG','DJI_0033.JPG','DJI_0034.JPG','DJI_0035.JPG']

        for each in ref_image:
            d  = opensfm_interface.extract_metadata_image('/home/j/ODM-master/grpc_stages/node1/'+each, opensfm_config)
            if d['camera'] not in camera_models:
                camera = exif.camera_from_exif_metadata(d, opensfm_config)
                camera_models[d['camera']] = camera
            opensfm_interface.save_exif('/home/j/ODM-master/grpc_stages/node1/exif', each, d)
        opensfm_interface.save_camera_models('/home/j/ODM-master/grpc_stages/node1/', camera_models)
        
        #c  = opensfm_interface.extract_metadata_image('/home/j/ODM-master/grpc_stages/node1/DJI_0019.JPG', opensfm_config)
       

        print(d)
        print(camera_models)
        #opensfm_interface.save_exif('/home/j/ODM-master/grpc_stages/node1/', 'DJI_0019.JPG', c)
        
        #save the exif metadata to file in a folder
        # send extracted metedata and camera model back

 

        #feature extraction
        for each in ref_image:
            opensfm_interface.detect(current_path+'features', current_path+each,each ,opensfm_config)


        #opensfm_interface.detect(current_path+'features', current_path+'DJI_0019.JPG','DJI_0019.JPG' ,opensfm_config)




        #feature matching

       

        pairs_matches, preport = new_matching.match_images(current_path, ref_image, cand_images, opensfm_config)
        new_matching.save_matches(current_path, ref_image, pairs_matches)
        print('matching')
        



        #create tracks first

        features, colors = tracking.load_features(current_path+'features', ref_image, opensfm_config)
        matches = tracking.load_matches(current_path, ref_image)
        graph = tracking.create_tracks_graph(features, colors, matches,
                                             opensfm_config)

        opensfm_interface.save_tracks_graph(graph, current_path)



        #reconstruction


        # load tracks graph

        graph = opensfm_interface.load_tracks_graph(current_path)
        report, reconstructions = reconstruction.incremental_reconstruction(current_path, graph, opensfm_config)

        opensfm_interface.save_reconstruction(current_path,reconstructions)
        #opensfm_interface.save_report(io.json_dumps(report), 'reconstruction.json')
      
        outputs = {}
        photos = []
        from opendm import photo
        from opendm import types
        
        for each in ref_image:
            photos += [types.ODM_Photo(current_path+each)]
          
        
        # get match image sizes
        outputs['undist_image_max_size'] = max(
            gsd.image_max_size(photos, 5.0, current_path+'reconstruction.json'),
            0.1
        )        
        print(outputs)

        #undistort image dataset: 

        opensfm_interface.opensfm_undistort(current_path, opensfm_config)


        #export visualsfm

        opensfm_interface.open_export_visualsfm(current_path, opensfm_config)

        #compute depthmaps 

        opensfm_interface.open_compute_depthmaps(current_path, opensfm_config)

      
        #mve stage 1 makescene

        #input compute depthmaps file
        
        mve_file_path = '/home/j/ODM-master/grpc_stages/node1/mve'
        nvm_file = '/home/j/ODM-master/grpc_stages/node1/undistorted/reconstruction.nvm'
        mve_interface.mve_makescene(nvm_file, mve_file_path, 2)


        #mve stage 2 dense reconstruction

        mve_interface.mve_dense_recon(outputs['undist_image_max_size'], mve_file_path, 2)

        #mve stage 3 scene2pset_path
        mve_model = io.join_paths(mve_file_path, 'mve_dense_point_cloud.ply')
        mve_interface.mve_scene2pset(mve_file_path, mve_model,outputs['undist_image_max_size'],2)

        #mve stage 4 clean_mesh
        mve_interface.mve_cleanmesh(0.6, mve_model, 2)



        # filterpoint cloud
        odm_filterpoints = '/home/j/ODM-master/grpc_stages/node1/filterpoints'
        filterpoint_cloud = io.join_paths(odm_filterpoints, "point_cloud.ply")

        filterpoint_interface.filter_points(odm_filterpoints, mve_model, filterpoint_cloud,2)

        #meshing stage
        odm_mesh_folder= '/home/j/ODM-master/grpc_stages/node1/mesh'
        odm_mesh_ply = io.join_paths(odm_mesh_folder, "odm_mesh.ply")
        mesh_interface.mesh_3d(odm_mesh_folder, odm_mesh_ply, filterpoint_cloud, 2)

        #texturing stage

        mvs_folder= '/home/j/ODM-master/grpc_stages/node1/mvs'
        mvs_texturing.mvs_texturing(odm_mesh_ply, mvs_folder, nvm_file)       

        #https://stackoverflow.com/questions/45071567/how-to-send-custom-header-metadata-with-python-grpc


        class Servicer(sendFile_pb2_grpc.FileServiceServicer):
            def __init__(self):
                self.dataset_dir = './dataset'
                self.tmp_file_name = './dataset2/IMG_2359.JPG'


            async def upload(self, request_iterator, context):
                # client uploads images to this node
                #request iterator is the file iterator through the chuncks

                #self.tmp_file_name is the name to save the file chucks to 
                nodeid = ''
                filename = ''
                for key, value in context.invocation_metadata():
                    
                    if(key == 'node-id'):
                        nodeid = value
                        #check if there is a dir for the node id
                        system.mkdir_p(nodeid)
                    if key == 'filename':
                        filename = value

                 
                    print('Received initial metadata: key=%s value=%s' % (key, value))
                #print(os.path.dirname(os.path.abspath(__file__)))
                if (nodeid != '' and filename  != ''):
                    save_chunks_to_file(request_iterator, nodeid+'/images/'+filename)

                    return sendFile_pb2.UploadStatus(Message = " Successul ", Code=sendFile_pb2.UploadStatusCode.Ok) 
                else:
                    print('bad node id and bad filename')
                    # reply = sendFile_pb2.UploadStatus()
                    # reply.Message = " Failed "
                    # reply.c
                    return sendFile_pb2.UploadStatus(Message = " Failure ", Code=sendFile_pb2.UploadStatusCode.Failed)

            def download(self, request, context):
                if request.name:
                    return get_file_chunks(self.tmp_file_name)

            def compute(self, request, context):
                taskName = request.taskName

                #metadata use image name 
                #use node id 

                #opensfm compute

                # detect feature

                # 


                # if(taskName == "compute_image_feature"):

                # elif(taskName == 'compute_matching_two_images'):0
               


                # elif(taskName == 'compute_'):

                # elif(taskName == ''):

                


                return 0

        self.server = aio.server()

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
        self.server.add_insecure_port('[::]:'+str(port))
        self.server.start()

        print("end of init")

        try:
            while True:
                time.sleep(60*60*24)
        except KeyboardInterrupt:
            self.server.stop(0)
