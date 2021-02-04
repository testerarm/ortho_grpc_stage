import lib

if __name__ == '__main__':
    port = 50001
    node_id = 3
    datapath = '/node3'


    lib.FileServer(port, node_id, datapath).start(50001)
  