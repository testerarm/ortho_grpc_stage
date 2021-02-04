import lib
import os 
import os.path
import collections


from threading import Thread
from Queue import Queue
import opensfm_interface


from opensfm_modified import new_pairs_selection
import threading
import sys

from timeit import default_timer as timer

def do_task(job_queue):


    while True:
        
        try:
            task = job_queue.get() # returns a map 
            print("task: " + str(task))
            if 'self' in task:

                response = False
                
                if task['title'] == 'extract_exif':

                    #image path, opensfm_config, node_file_path
                  
                    response = lib.sfm_extract_metadata_list_of_images(task['image_path'], task['opensfm_config'], task['node_file_path'])

                elif task['title'] == 'detect_features':

                    print('detect features in task queue')
                    # needs images 

                    # current path, ref images, opensfm_config
                    current_path = task['node_file_path']

                    ref_image = os.listdir(current_path + '/images')

                    response = lib.sfm_detect_features(ref_image, current_path  ,task['opensfm_config'])
                    
                    
                elif task['title'] == 'feature_matching':
                    print('feature matching')

                    # needs images
                    # image path
                    # list of images 
                    # candidate images
                    # opensfm config


                    response = lib.sfm_feature_matching(task['node_file_path'], task['ref_image'], task['cand_images'], task['opensfm_config'] )
                    
                elif task['title'] == 'create_tracks':
                    # needs images
                    # current path
                    
                    response = lib.create_tracks(task['node_file_path'], task['ref_image'],task['opensfm_config'])
                    
                elif task['title'] == 'opensfm_reconstruction':

                    # needs create tracks . csv
                    # return reconstruction.json

                    response = lib.sfm_opensfm_reconstruction(task['node_file_path'], task['opensfm_config'])
                    
                elif task['title'] == 'sfm_undistort_image':

                    response = lib.sfm_undistort_image(task['node_file_path'], task['opensfm_config'])
                    
                    
                elif task['title'] == 'export_visual_sfm':
                    #nvm file
                   
                    response = lib.sfm_export_visual_sfm(task['node_file_path'],task['opensfm_config'])

                elif task['title'] == 'compute_depthmaps':
                   
                   response = lib.sfm_compute_depthmaps(task['node_file_path']. task['opensfm_config'])
                    
                elif task['title'] == 'dense_reconstruction':

                   response = lib.mve_dense_reconstruction(task['node_file_path'])
                    
                    
                elif task['title'] == 'makescene_function':
                   response = lib.mve_makescene_function(task['node_file_path'], task['max_concurreny'])
                    
                elif task['title'] == 'scene2pset':
                    response = lib.mve_scene2pset_function(task['node_file_path'], task['max_concurreny'])
                    
                    
                elif task['title'] == 'cleanmesh':
                   response = lib.mve_cleanmesh_function(task['node_file_path'], task['max_concurreny'])
                    
                elif task['title'] == 'filterpoints':
                   response = lib.odm_filterpoints_function(task['node_file_path'], task['max_concurreny'])
                    
                elif task['title'] == 'mesh':
                   response = lib.odm_mesh_function(task['node_file_path'], task['max_concurreny'])
                                        
                elif task['title'] == 'texturing':
                    response = lib.odm_texturing_function(task['node_file_path'])
                    
            else:

                if task['title'] == 'upload_image':
                    print('upload')
                    response = task['client'].upload(task['filepath'], task['list'])
                    print(response)
                elif task['title'] == 'extract_exif':
                    print(str(task))
                    print('extract exif ')
                    response = task['client'].sendTask('exif', task['nodeid'], '/exif')
                    print(response)
                elif task['title'] == 'detect_features':

                    print('detect features in task queue')
                    # needs images 
                    response = task['client'].sendTask('detect_features', task['nodeid'], '/features')
                elif task['title'] == 'feature_matching':
                    print('feature matching')

                    # needs images
                    respone = task['client'].sendTask('feature_matching', task['nodeid'], '/matches')
                    
                elif task['title'] == 'create_tracks':
                    #needs images
                    respone = task['client'].sendTask('create_tracks', task['nodeid'], '/')
                    
                elif task['title'] == 'opensfm_reconstruction':

                    # needs create tracks . csv
                    # return reconstruction.json
                    respone = task['client'].sendTask('opensfm_reconstruction', task['nodeid'], '/')
                    
                elif task['title'] == 'sfm_undistort_image':
                    respone = task['client'].sendTask('undistort_image', task['nodeid'], '/undistorted')
                    
                elif task['title'] == 'export_visual_sfm':
                    #nvm file
                    respone = task['client'].sendTask('export_visual_sfm', task['nodeid'], '/undistorted')
                    
                elif task['title'] == 'compute_depthmaps':
                    respone = task['client'].sendTask('compute_depthmaps', task['nodeid'], '/depthmaps')
                    
                elif task['title'] == 'dense_reconstruction':
                    respone = task['client'].sendTask('dense_reconstrution', task['nodeid'], '/mve')
                    
                elif task['title'] == 'makescene_function':
                    respone = task['client'].sendTask('makescene_function', task['nodeid'], '/mve')
                    
                elif task['title'] == 'scene2pset':
                    respone = task['client'].sendTask('scene2pset', task['nodeid'], '/mve')
                    
                elif task['title'] == 'cleanmesh':
                    respone = task['client'].sendTask('cleanmesh', task['nodeid'], '/mve')
                    
                elif task['title'] == 'filterpoints':
                    respone = task['client'].sendTask('odm_filterpoints', task['nodeid'], '/filterpoints')
                    
                elif task['title'] == 'mesh':
                    respone = task['client'].sendTask('odm_mesh', task['nodeid'], '/mesh')
                    
                elif task['title'] == 'texturing':
                    respone = task['client'].sendTask('odm_texturing', task['nodeid'], '/mvs')
                    
                elif task['title'] == 'feature_matching_pairs':
                    # send over the pair feature files and exif files

                    print('in task here ' + str(task['pair']))

                    pair = task['pair']

                    #send the pair of feature files

                    feature_0 = 'features/' + pair[0] + '.features.npz'
                    feature_1 = 'features/' + pair[1] + '.features.npz'


                    response = task['client'].upload(task['filepath'], [feature_0, feature_1])

                    exif_0 = 'exif/' + pair[0] + '.exif'
                    exif_1 = 'exif/' + pair[1] + '.exif'


                    response = task['client'].upload(task['filepath'], [exif_0, exif_1])

                    response = task['client'].sendTask('feature_match_pairs', task['nodeid'], '/matches', [pair[0], pair[1]])

                    filename =  pair[0]+'-'+pair[1] 
                    matches = opensfm_interface.load_matches(task['filepath'],filename)
                    print('load matches')
                    print(matches)
                    task['lock'].acquire()
                    try:
                        tup = (pair[0], pair[1])
                        task['results'].update(matches)
                    except Exception as e:
                        print(e.message)
                        sys.exit(0)
                    finally:
                        task['lock'].release()
                    
                        


                print('done')
            
        except Exception as e:
            print(e.message)
            sys.exit(0)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            sys.exit(0)
        finally:
            job_queue.task_done()
        

        

if __name__ == '__main__':
    
    #lib.FileServer(8888, 1, 'node1').start(8888)

    thread_lock = threading.Lock()

    try:


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




        nodes_available = {2: True, 3: True}


        for each_node in nodeid_map:
            client = lib.FileClient('localhost:' + nodeid_map[each_node], nodeid)
            node_client[each_node] = client

        images_filepath = '/home/j/ODM-master/grpc_stages/node1'  #file path of current node images
        file_path = images_filepath + '/'
        active_number_of_nodes = 2
        photos_name = collections.defaultdict(lambda : "None")
        photo_list =  os.listdir(os.path.join(images_filepath, 'images'))
        print(photo_list)

        image_sent_nodes = collections.defaultdict(lambda : 'none')

      


        #group images by distance
       








        for name in photo_list:
            if os.path.isfile(name):
                photos_name[name] = 'not send'
        num_photos = len(photo_list)

        photos_per_node = num_photos / active_number_of_nodes 
        print(photos_per_node)
        photos_rem = num_photos % active_number_of_nodes

        current_photo_pointer = 0

        start = timer()



        for eachnode in nodeid_list:
            if (photos_rem > 0):
                new_photos_for_node = photos_per_node + photos_rem
                photolist = photo_list[current_photo_pointer:new_photos_for_node]
                current_photo_pointer+=new_photos_for_node
                print(str(eachnode) + " : " + str(photolist))
                job_map = {'title': 'upload_image', 'client': node_client[eachnode], 'list': photolist, 'filepath': images_filepath+'/images'}
                job_queue.put(job_map)
                photos_rem = 0
                
                #esponse = client.upload(, is_dir=True)

                # send to this node 
            else:
                end_pointer = current_photo_pointer+photos_per_node
                if end_pointer > num_photos:
                    end_pointer = num_photos
                photolist = photo_list[current_photo_pointer:end_pointer]
                current_photo_pointer+=photos_per_node
                print(str(eachnode) + " : " +  str(photolist))
                job_map = {'title': 'upload_image', 'client': node_client[eachnode], 'list': photolist, 'filepath': images_filepath+'/images'}
                job_queue.put(job_map)
           
               
                #send regular number of photos

        job_queue.join()

        end = timer()
        upload_image_time = end - start

        #extract sift

        print('here in extract exif')

        start = timer()

        for each in nodeid_list:
            job_task_extract_exif = {'title': 'extract_exif', 'client': node_client[each], 'nodeid': nodeid}
            job_queue.put(job_task_extract_exif)
        

    #    #call join to wait
        job_queue.join()

        end = timer()
        exif_extraction_time = end - start

        

        print('here in dectect feature')

    
        # detect_features


        start = timer()

        #for each
        for each in nodeid_list:
            job_task_detect = {'title': 'detect_features', 'client': node_client[each], 'nodeid': nodeid}
            job_queue.put(job_task_detect)

      
        job_queue.join()

        end = timer()
        detect_features_time = end - start

        print('matching features')


        # match features 

        # job_task_detect = {'title': 'feature_matching', 'client': node_client[2], 'nodeid': 1}
        # job_queue.put(job_task_detect)
        # job_task_detect = {'title': 'feature_matching', 'client': node_client[3], 'nodeid': 1}
        # job_queue.put(job_task_detect)

        #// feature matching 


        # for each image 

        # generate pairs 
        # loop through the task for the pairs 

        
       

        # match through the pairs
        # save the results
        # append to the file





        #job_queue.join()

        start = timer()
         

        print('after queue join filepath')
  

        ref_images = os.listdir(file_path +'/images')
        print(ref_images)
        cand_images = ref_images
        exifs = {im: opensfm_interface.load_exif(file_path,im) for im in ref_images}

        print(exifs)
        opensfm_config = opensfm_interface.setup_opensfm_config(file_path)

        print(file_path)
        

        pairs, preport = new_pairs_selection.match_candidates_from_metadata( file_path, 
        ref_images, cand_images, exifs, opensfm_config)

        print('here')
        print(pairs)

        results = {}
        #for each pair 
        #for each node

        #go through all the nodes


        # start value for the client number
        node_client_num = 2
        for each in pairs:
            job_task = {'title': 'feature_matching_pairs', 'client': node_client[node_client_num], 'nodeid': 1, 'pair': each, 'filepath': file_path, 'results': results, 'lock': thread_lock}
            node_client_num = ((node_client_num + 1) % 2) + 2  
            job_queue.put(job_task)
            



        job_queue.join()
        print('results in the end')
        print(results)

        end = timer()
        feature_matching_time = end - start
            



        #file_path
        #opensfm_config
        #exifs
        #need to send the features




        #match image with paris 





        # create tracks 
        # have to be single computation

        # tracks graph // add_node in union find 
        # get all the tracks then merge them

        print('create tracks')

        start = timer()

        lib.sfm_create_tracks(images_filepath , ref_images, opensfm_config, results)


        #distributed approach
        # uf = UnionFind()
        # for im1, im2 in matches:
        #     for f1, f2 in matches[im1, im2]:
        #         uf.union((im1, f1), (im2, f2))

        # sets = {}
        # for i in uf:
        #     p = uf[i]
        #     if p in sets:
        #         sets[p].append(i)
        #     else:
        #         sets[p] = [i]

        # min_length = config['min_track_length']
        # tracks = [t for t in sets.values() if _good_track(t, min_length)]
        # logger.debug('Good tracks: {}'.format(len(tracks)))


        # tracks_graph = nx.Graph()
        # for track_id, track in enumerate(tracks):
        #     for image, featureid in track:
        #         if image not in features:
        #             continue
        #         x, y, s = features[image][featureid]
        #         r, g, b = colors[image][featureid]
        #         tracks_graph.add_node(str(image), bipartite=0)
        #         tracks_graph.add_node(str(track_id), bipartite=1)
        #         tracks_graph.add_edge(str(image),
        #                             str(track_id),
        #                             feature=(float(x), float(y)),
        #                             feature_scale=float(s),
        #                             feature_id=int(featureid),
        #                             feature_color=(float(r), float(g), float(b)))





        end = timer()
        create_tracks_time = end - start

        # nx compose (two graphs)
        print('finished')
        # same 


        # load camera models 
        # reconstruction

        # same 

        # compute image pairs 
        # for each pairs 
        # reconstruction base on image pairs shots
        
        start = timer()


        # need the exifs 

        lib.sfm_opensfm_reconstruction(file_path, opensfm_config)


        end = timer()
        sfm_opensfm_reconstruction_time = end - start

        start = timer()

        lib.sfm_undistort_image(file_path, opensfm_config)

        end = timer()
        sfm_undistort_image_time = end - start


        start = timer()
        
        lib.sfm_export_visual_sfm(file_path, opensfm_config)


        end = timer()
        sfm_export_visualsfm_time = end - start


        start = timer()

        lib.sfm_compute_depthmaps(file_path, opensfm_config)


        end = timer()
        sfm_compute_depthmaps_time = end - start


        # split merge here no problem


        start = timer()


        lib.mve_makescene_function(file_path, 2)

        end = timer()
        mve_makescene_function_time = end - start

        start = timer()

        lib.mve_dense_reconstruction(file_path, 2)

        end = timer()
        mve_dense_reconstruction_time = end - start

        start = timer()

        lib.mve_scene2pset_function(file_path, 2)

        end = timer()
        mve_mve_scene2pset_time = end - start

        start = timer()

        lib.mve_cleanmesh_function(file_path,2)

        end = timer()
        mve_mve_cleanmesh_time = end - start


        start = timer()


        lib.odm_filterpoints_function(file_path, 2)


        end = timer()
        odm_filterpoint_time = end - start
        
        start = timer()
        lib.odm_mesh_function(file_path,2)
        end = timer()
        odm_mesh_time = end - start
        
        
        start = timer()

        lib.odm_texturing_function(file_path)

        end = timer()
        odm_texturing_time = end - start




        # needs features _load 
        # needs feature matching 
        # needs list of images 




        #undistort , # load reconstruction
        # load images 
        # for each shot in reconstruction shot values 
        # #for each subshots 
        # undistort detection






        #export visual sfm 

        # 


        # compute depthmaps

        




        

        # need exif file
        # images 
        #  

        # job_task_detect = {'title': 'detect_features', 'client': node_client[2], 'nodeid': 1}
        # job_queue.put(job_task_detect)



        # job_task_detect = {'title': 'detect_features', 'client': node_client[3], 'nodeid': 1}
        # job_queue.put(job_task_detect)

        # job_queue.join()



        #feature matching





        # client = lib.FileClient('localhost:8080')
        # # demo for file uploading
        # in_file_name = 'IMG_2331.JPG'
        # response = client.upload('dataset/images/images/**', is_dir=True)
        # print("response" + str(response))


        #lib.mve_dense_reconstruction(images_filepath)
        



        print('########################')

        print('End Results: ')
        print('Upload Image Total Time: ' + str(upload_image_time))
        print('Exif Extraction Total Time: ' + str(exif_extraction_time))
        print('Detect Features Total Time: ' + str(detect_features_time))
        print('Feature Matching Total Time: ' + str(feature_matching_time))

        print('Create Tracks Total Time: ' + str(create_tracks_time))
        print('OpenSfm Reconstruction Total Time: ' + str(sfm_opensfm_reconstruction_time))
        print('OpenSfm Undistort Image Total Time: ' + str(sfm_undistort_image_time))
        print('OpenSfm Export Visual Sfm Total Time: ' + str(sfm_export_visualsfm_time))
        print('OpenSfm Compute DepthMaps Sfm Total Time: ' + str(sfm_compute_depthmaps_time))
        print('Mve Makescene Sfm Total Time: ' + str(mve_makescene_function_time))
        print('Mve Dense Reconstruction Sfm Total Time: ' + str(mve_dense_reconstruction_time))
        print('Mve Scene 2 Pset Sfm Total Time: ' + str(mve_mve_scene2pset_time))
        print('Mve Cleanmesh Sfm Total Time: ' + str(mve_mve_cleanmesh_time))
        print('ODM Filterpoints Total Time: ' + str(odm_filterpoint_time))
        print('ODM Mesh Total Time: ' + str(odm_mesh_time))
        print('ODM Texturing Total Time: ' + str(odm_texturing_time))
        
        
        print('#######################')


        #execute a task on the server
    except Exception as e:
        print(e.message)

    except KeyboardInterrupt:
        print('keyboard interrupt')
        sys.exit(0)







































