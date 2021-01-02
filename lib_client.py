import lib
import os 
import os.path
import collections


import threading
from queue import Queue


if __name__ == '__main__':
    
    lib.FileServer().start(8888)

    job_queue = Queue()

    nodeid = 1
    nodeid_list = [2, 3]
    nodeid_map = {2: '8080', 3: '50001'}

    images_filepath = ''  #file path of current node images
    active_number_of_nodes = 2
    photos_name = collections.defaultdict(lambda : "None")
    for name in os.listdir('/home/j/ODM-master/grpc_stages/node1/images'):
        if os.path.isfile(name):
            photos_name[name] = 'not send'
    num_photos = len(photos_name)

    photos_per_node = number_of_photos / active_number_of_nodes 
    photos_rem = number_of_photos % active_number_of_nodes

    for eachnode in nodeid_list:
        if (photos_rem > 0):
            new_photos_for_node = photos_per_node + photos_rem
            
            client = lib.FileClient('localhost:' + nodeid_map[eachnode])
            
            

            esponse = client.upload(, is_dir=True)

            # send to this node 
        else:
            # send regular number of photos


    # extract 


    # client = lib.FileClient('localhost:8080')
    # # demo for file uploading
    # in_file_name = 'IMG_2331.JPG'
    # response = client.upload('dataset/images/images/**', is_dir=True)
    # print("response" + str(response))




    #execute a task on the server


