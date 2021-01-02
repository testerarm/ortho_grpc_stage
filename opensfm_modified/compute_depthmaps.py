import logging

#from opensfm import dataset
from opensfm import dense
import opensfm_interface

logger = logging.getLogger(__name__)


class ComputeDepthMapsCommand:
    name = 'compute_depthmaps'
    help = "Compute depthmap"

    def add_arguments(self, parser):
        parser.add_argument(
            'dataset',
            help='dataset to process',
        )
        parser.add_argument(
            '--subfolder',
            help='undistorted subfolder where to load and store data',
            default='undistorted'
        )
        parser.add_argument(
            '--interactive',
            help='plot results as they are being computed',
            action='store_true',
        )

    def run(self, file_path, opensfm_config):
       # data = dataset.DataSet(args.dataset)
        udata = opensfm_interface.UndistortedDataSet(file_path, opensfm_config, 'undistorted')
        reconstructions = udata.load_undistorted_reconstruction()
        graph = udata.load_undistorted_tracks_graph()

     
        #opensfm_config['interactive'] = 
    

        dense.compute_depthmaps(udata, graph, reconstructions[0])
