import os
from concurrent import futures

import grpc
import time

import chunk_pb2, chunk_pb2_grpc

CHUNK_SIZE = 1024 * 1024  # 1MB

from geopy import distance

from opendm import log
from opendm import config
from opendm import system
from opendm import io
from opendm.progress import progressbc
from stages.dataset_grpc import ODMLoadDatasetStage
import stages.run_opensfm
from opendm import config

import stages

#from stages.dataset_grpcdataset import ODMLoadDatasetStage
from stages.run_opensfm import ODMOpenSfMStage
from stages.mve import ODMMveStage
from stages.odm_slam import ODMSlamStage
from stages.odm_meshing import ODMeshingStage
from stages.mvstex import ODMMvsTexStage
from stages.odm_georeferencing import ODMGeoreferencingStage
from stages.odm_orthophoto import ODMOrthoPhotoStage
from stages.odm_dem import ODMDEMStage
from stages.odm_filterpoints import ODMFilterPoints
from stages.splitmerge import ODMSplitStage, ODMMergeStage
from stages.odm_report import ODMReport


import numpy as np
from collections import defaultdict

from opensfm import dataset
from opensfm.large import metadataset
from opensfm.large import tools


from opensfm.commands import create_submodels

def get_file_chunks(filename):
    with open(filename, 'rb') as f:
        while True:
            piece = f.read(CHUNK_SIZE);
            if len(piece) == 0:
                return
            yield chunk_pb2.Chunk(buffer=piece)
       


def save_chunks_to_file(chunks, filename):
    print('save chuck' + str(filename))
    with open(filename, 'wb') as f:
        for chunk in chunks:
            f.write(chunk.buffer)

def point_within_radius(test_point, array_of_points , radius):
    print('point radius')
    center_point = [{'lat': -7.7940023, 'lng': 110.3656535}]
    test_point = [{'lat': -7.79457, 'lng': 110.36563}]
    radius = 5 # in kilometer

    center_point_tuple = tuple(center_point[0].values()) # (-7.7940023, 110.3656535)
    test_point_tuple = tuple(test_point[0].values()) # (-7.79457, 110.36563)

    dis = distance.distance(center_point_tuple, test_point_tuple).m
    print("Distance: {}".format(dis)) # Distance: 0.0628380925748918

    if dis <= radius:
        print("{} point is inside the {} km radius from {} coordinate".format(test_point_tuple, radius, center_point_tuple))
    else:
        print("{} point is outside the {} km radius from {} coordinate".format(test_point_tuple, radius, center_point_tuple))



def detect(args):
    # data = dataset.DataSet(args.dataset)
    #    images = data.images()
    #   arguments = [(image, data) for image in images]
    #

    image, data = args

    log.setup()

    need_words = data.config['matcher_type'] == 'WORDS' or data.config['matching_bow_neighbors'] > 0
    has_words = not need_words or data.words_exist(image)
    has_features = data.features_exist(image)

    if has_features and has_words:
        logger.info('Skip recomputing {} features for image {}'.format(
            data.feature_type().upper(), image))
        return

    logger.info('Extracting {} features for image {}'.format(
        data.feature_type().upper(), image))

    start = timer()

    p_unmasked, f_unmasked, c_unmasked = features.extract_features(
        data.load_image(image), data.config)

    fmask = data.load_features_mask(image, p_unmasked)

    p_unsorted = p_unmasked[fmask]
    f_unsorted = f_unmasked[fmask]
    c_unsorted = c_unmasked[fmask]

    if len(p_unsorted) == 0:
        logger.warning('No features found in image {}'.format(image))
        return

    size = p_unsorted[:, 2]
    order = np.argsort(size)
    p_sorted = p_unsorted[order, :]
    f_sorted = f_unsorted[order, :]
    c_sorted = c_unsorted[order, :]
    data.save_features(image, p_sorted, f_sorted, c_sorted)

    if need_words:
        bows = bow.load_bows(data.config)
        n_closest = data.config['bow_words_to_match']
        closest_words = bows.map_to_words(
            f_sorted, n_closest, data.config['bow_matcher_type'])
        data.save_words(image, closest_words)

    end = timer()
    report = {
        "image": image,
        "num_features": len(p_sorted),
        "wall_time": end - start,
    }
    data.save_report(io.json_dumps(report), 'features/{}.json'.format(image))







def run_opensfm_g(args):
        data = dataset.DataSet(args.dataset)
        meta_data = metadataset.MetaDataSet(args.dataset)

        meta_data.remove_submodels()
        data.invent_reference_lla()
        create_submodels._create_image_list(data, meta_data)

        if meta_data.image_groups_exists():
            create_submodels._read_image_groups(meta_data)
        else:
            create_submodels._cluster_images(meta_data, data.config['submodel_size'])

        create_submodels._add_cluster_neighbors(meta_data, data.config['submodel_overlap'])
        create_submodels._save_clusters_geojson(meta_data)
        create_submodels._save_cluster_neighbors_geojson(meta_data)

        meta_data.create_submodels(
            meta_data.load_clusters_with_neighbors())



def configuration():
    args = config.config()
    args_dict = vars(args)
    args.split = 5
    args.split_overlap = 10
    args.rerun_all = True

    for k in sorted(args_dict.keys()):
        # Skip _is_set keys
        if k.endswith("_is_set"):
            continue

        # Don't leak token
        if k == 'sm_cluster' and args_dict[k] is not None:
            log.ODM_INFO('%s: True' % k)
        else:
            log.ODM_INFO('%s: %s' % (k, args_dict[k]))


    args.project_path = io.join_paths(args.project_path, args.name)
    print(args.project_path)
    args.project_path='/home/j/ODM-master/dataset/images'
    if not io.dir_exists(args.project_path):
        log.ODM_WARNING('Directory %s does not exist. Creating it now.' % args.name)
        system.mkdir_p(os.path.abspath(args.project_path))


    dataset = ODMLoadDatasetStage('dataset', args, progress=5.0,
                                          verbose=args.verbose)

    



    dataset.run()


    #upload images to server 2

    
    #blocking call
    #run distance measuremeants


    #exchange images that are required by 2 and images required by 1

    #opensfm in map reduce mode


    

    opensfm = ODMOpenSfMStage('opensfm', args, progress=25.0)
    opensfm.run()


   







class FileClient:
    def __init__(self, address):
        channel = grpc.insecure_channel(address) 
        self.stub = chunk_pb2_grpc.FileServerStub(channel)

    def upload(self, in_file_name):
        chunks_generator = get_file_chunks(in_file_name)
        response = self.stub.upload(chunks_generator)
        assert response.length == os.path.getsize(in_file_name)
        return response

    def download(self, target_name, out_file_name):
        response = self.stub.download(chunk_pb2.Request(name=target_name))
        save_chunks_to_file(response, out_file_name)


class FileServer(chunk_pb2_grpc.FileServerServicer):
    def __init__(self):

        class Servicer(chunk_pb2_grpc.FileServerServicer):
            def __init__(self):
                self.tmp_file_name = './temp/IMG_2359.JPG'

            def upload(self, request_iterator, context):
                save_chunks_to_file(request_iterator, self.tmp_file_name)
                return chunk_pb2.Reply(length=os.path.getsize(self.tmp_file_name))

            def download(self, request, context):
                if request.name:
                    return get_file_chunks(self.tmp_file_name)

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        chunk_pb2_grpc.add_FileServerServicer_to_server(Servicer(), self.server)

    def start(self, port):
        self.server.add_insecure_port('[::]:'+str(port))
        self.server.start()

        try:
            while True:
                time.sleep(60*60*24)
        except KeyboardInterrupt:
            self.server.stop(0)
