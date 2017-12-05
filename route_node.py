# -- coding: utf-8 --
import socket
import io
import json
import threading
import select
import queue
import time
import random
import sys
import logging
import collections

# create logger with 'RouteNode'
route_node_logger = logging.getLogger('RouteNode')
route_node_logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('route_node.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the route_node_logger
route_node_logger.addHandler(fh)
route_node_logger.addHandler(ch)

class RouteNode:


    send_sock = None
    recv_sock = None

    PACKET_DATA = "DATA"
    PACKET_ROUTE = "ROUTE"
    DATA_TXT = "TXT"
    DATA_JPEG = "JPEG"
    DATA_PNG = "PNG"

    TIMEOUT = None
    BUFFER_SIZE = 1024 * 1024 * 10

    def __init__(self, node_file, obj_handler, *args, **kwargs):
        self.forward_table = {}
        self.cost_table = {}
        self.id_to_addr = {}
        self.neighbors = []
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_seq_num = random.randint(0, sys.maxsize)
        self.messages_queue = queue.Queue()
        self.data_obj_handler = obj_handler

        self.running = False
        self.broadcast_seq_num = 0
        self.send_queue = queue.Queue()

        with open(node_file) as f:
            obj = json.load(f)
        self.node_id = obj['node_id']
        self.send_sock.bind((obj['ip'], obj['port']))
        self.recv_sock.bind((obj['ip'], obj['port']))
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
            route_node_logger.error(e)

        ret = {
            src_id: "src_id",
            dst_id: "dst_id",
            seq_num: "seq_num",
            packet_type: "packet_type",
            data_type: "data_type",
            data: "data",
        }

        return ret

    def obj_to_raw(self, packet, dst_node_id):
        template = r'''SRC_ID {}
DST_ID {} {}
{} {}
'''
        if dst_node_id == -1:
            # broadcast
            seq_num = self.broadcast_seq_num
            self.broadcast_seq_num = (self.broadcast_seq_num + 1) % sys.maxsize
        header = template.format(self.node_id, dst_node_id, seq_num if dst_node_id == -1 else '', packet['packet_type'], packet['data_type'])
        ret = header.encode('utf-8')
        data = packet['data']
        if isinstance(data, str):
            data = data.encode('utf-8')
        ret += data
        return ret

    # check the obj type and forward
    # DATA -> data_obj_handler
    # ROUTE -> route_obj_handler
    def forward_obj(self, obj):
        if obj['packet_type'] == RouteNode.PACKET_ROUTE:
            self.route_obj_handler(obj)
        elif obj['packet_type'] == RouteNode.PACKET_DATA:
            if isinstance(self.data_obj_handler, collections.Callable):
                self.data_obj_handler(obj)
        else:
            route_node_logger.warn("Unknown packet type received")

    def thread_func(self):
        inputs = [self.recv_sock]
        outputs = [self.send_sock]
        
        while self.running:
            route_node_logger.debug("Waiting for next event...")
            readable, writable, exceptional = select.select(inputs, outputs, inputs, self.TIMEOUT)
            if not (readable or writable or exceptional):
                route_node_logger.warn("TIME OUT!!")
            for s in readable:
                if s is self.recv_sock:
                    raw, addr = s.recvfrom(self.BUFFER_SIZE)
                    obj = RouteNode.raw_to_obj(raw)
                    self.forward_obj(obj)

            for s in writable:
                if s is self.send_sock:
                    while not self.send_queue.empty():
                        try:
                            raw_data, addr = self.send_queue.get_nowait()
                        except queue.Empty:
                            route_node_logger.debug('send_queue empty')
                        else:
                            s.sendto(raw_data, addr)

            for s in exceptional:
                route_node_logger.error("Exception on {}".format(s.getpeername()))

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
        raw_data = self.obj_to_raw(packet, dst_node_id)
        if (dst_node_id == -1):
            # broadcast
            for node in self.neighbors:
                self.raw_send(raw_data, dst_node_id)
        else:
            self.raw_send(raw_data, dst_node_id)

    def raw_send(self, raw_data, dst_node_id):
        if not dst_node_id in self.forward_table:
            route_node_logger.warn("No such id in forward_table yet")
            return 0
        else:
            next_node_id = self.forward_table[dst_node_id]
            msg_tuple = (raw_data, self.id_to_addr[next_node_id])
            self.send_queue.put(msg_tuple)
        
    def route_obj_handler(self, route_obj):
        # Should be override
        raise NotImplementedError