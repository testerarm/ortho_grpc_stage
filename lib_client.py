#import lib
import os 
import os.path
import collections


import threading import Thread
from multiprocessing import Queue



def do_task(job_queue):
    while True:
        task = job_queue.get() # returns a map 
        print("task: " + str(task))
        if task['title'] == 'upload_task':
            response = task['client'].upload(task['filepath'], task['list'])
            print(response)
        job_queue.task_done()

if __name__ == '__main__':
    
    #lib.FileServer().start(8888)


    job_queue = Queue()
    num_threads = 4
    for i in range(num_threads):
        worker = Thread(target=do_task, args=(job_queue,))
        worker.setDaemon(True)
        worker.start()


    nodeid = 1
    nodeid_list = [2, 3]
    nodeid_map = {2: '8080', 3: '50001'}
    node_client = {}
    for each_node in nodeid_map:
        client = lib.FileClient('localhost:' + nodeid_map[eachnode])
        node_client[each_node] = client

    images_filepath = '/home/j/ODM-master/grpc_stages/node1'  #file path of current node images
    active_number_of_nodes = 2
    photos_name = collections.defaultdict(lambda : "None")
    photo_list =  os.listdir('/home/j/ODM-master/grpc_stages/node1/images')
    print(photo_list)
    for name in photo_list:
        if os.path.isfile(name):
            photos_name[name] = 'not send'
    num_photos = len(photo_list)

    photos_per_node = num_photos / active_number_of_nodes 
    print(photos_per_node)
    photos_rem = num_photos % active_number_of_nodes

    current_photo_pointer = 0
    for eachnode in nodeid_list:
        if (photos_rem > 0):
            new_photos_for_node = photos_per_node + photos_rem
            photolist = photo_list[current_photo_pointer:new_photos_for_node]
            current_photo_pointer+=new_photos_for_node
            print(str(eachnode) + " : " + str(photolist))
            job_map = {'title': 'upload_image', 'client': node_client[each_node], 'list': photo_list, 'filepath': images_filepath+'/images'}
            job_queue.put(job_map)
            
            
            #esponse = client.upload(, is_dir=True)

            # send to this node 
        else:
            end_pointer = current_photo_pointer+photos_per_node
            if end_pointer > num_photos:
                 end_pointer = num_photos
            photolist = photo_list[current_photo_pointer:end_pointer]
            current_photo_pointer+=photos_per_node
            print(str(eachnode) + " : " + str(photolist))
            job_map = {'title': 'upload_image', 'client': node_client[each_node], 'list': photo_list, 'filepath': images_filepath+'/images'}
            job_queue.put(job_map)
            # send regular number of photos

    job_queue.join()
    # extract 


    # client = lib.FileClient('localhost:8080')
    # # demo for file uploading
    # in_file_name = 'IMG_2331.JPG'
    # response = client.upload('dataset/images/images/**', is_dir=True)
    # print("response" + str(response))




    #execute a task on the server





































