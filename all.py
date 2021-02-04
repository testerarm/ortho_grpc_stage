


import lib
import config
from stages import dataset

if __name__ == '__main__':
    print('starting server at port 8080')



    lib.FileServer().start(8080)

    # configuration of parameter values
    # args = config.config()

    # # load the dataset , extract photo metadata such as gps, camera, 

    # dataset = ODMLoadDatasetStage('dataset', args, progress=5.0,
    #                                       verbose=args.verbose)
    # # run the dataset layer
    # dataset.run()

    #now we have photo metadata such as gps, camera,

    #need configuration of IP address of clients

    #https://stackoverflow.com/questions/45071567/how-to-send-custom-header-metadata-with-python-grpc
























