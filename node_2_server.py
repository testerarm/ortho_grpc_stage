import lib 




if __name__ == '__main__':
    port = 8080
    node_id = 2
    datapath = '/node2'


    lib.FileServer(port, node_id, datapath).start(8080)