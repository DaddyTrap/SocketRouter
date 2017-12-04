# -- coding: utf-8 --
import socket
import io
import json
import threading
import select
import queue
import time

class RouteNode:

    node_id = -1
    forward_table = {}
    cost_table = {}
    id_to_addr = {}
    neighbors = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    on_recv = None # on recv callback

    running = False

    PACKET_DATA = "DATA"
    # PACKET_ROUTE = "ROUTE"
    DATA_TXT = "TXT"
    DATA_JPEG = "JPEG"
    DATA_PNG = "PNG"

    def __init__(self, node_file, *args, **kwargs):
        with open(node_file) as f:
            obj = json.load(f)
        self.node_id = obj['node_id']
        self.sock.bind((obj['ip'], obj['port']))
        for k, v in obj['topo'].items():
            self.cost_table[k] = v['cost']
            self.forward_table[k] = k
            self.id_to_addr[k] = (v['real_ip'], v['real_port'])
            self.neighbors.append(k)

    @staticmethod
    def raw_to_obj(raw_proto_data):
        text = raw_proto_data.decode('utf-8', 'ignore')
        # for better performance
        text_io = io.StringIO()
        
        src_id = None
        dst_id = None
        seq_num = None
        packet_type = None
        data_type = None
        data = None
        
        try:
            data_begin = 0
            # SRC_ID
            line = text_io.readline()
            data_begin += len(line)
            split_res = line.split(' ')
            src_id = int(split_res[1])
            # DST_ID
            line = text_io.readline()
            data_begin += len(line)
            split_res = line.split(' ')
            dst_id = int(split_res[1])
            if dst_id == -1:
                # it's a broadcast, get seq number
                seq_num = int(split_res[2])
            # packet type and data type
            line = text_io.readline()
            data_begin += len(line)
            split_res = line.split(' ')
            packet_type = split_res[0]
            data_type = split_res[1]
            # DATA
            data = raw_proto_data[data_begin:]
        except Exception as e:
            print(e)

        ret = {
            src_id: "src_id",
            dst_id: "dst_id",
            seq_num: "seq_num",
            packet_type: "packet_type",
            data_type: "data_type",
            data: "data",
        }

        return ret

    @staticmethod
    def obj_to_raw(packet, dst_node_id):
        # TODO: implement obj_to_raw()
        return {}

    def thread_func(self):
        while self.running:
            # TODO: a select thread
            pass

    def start(self):
        # start thread to select socket
        self.running = True
        threading.Thread(target=self.thread_func).start()

    def stop(self):
        self.running = False

    # packet: {
    #     "packet_type": RouteNode.PACKET_DATA,
    #     "data_type": RouteNode.DATA_TXT,
    #     "data": "Hello example txt"
    # }
    # dst_node_id: Destination node id
    def send(self, packet, dst_node_id):
        # build seq num in obj_to_raw()
        raw_data = RouteNode.obj_to_raw(packet, dst_node_id)
        if (dst_node_id == -1):
            # broadcast
            # TODO: broadcast
            pass
        else:
            if not dst_node_id in self.forward_table:
                print("No such id in forward_table yet")
                return 0
            else:
                next_node_id = self.forward_table[dst_node_id]
                return self.sock.sendto(raw_data, self.id_to_addr[next_node_id])
