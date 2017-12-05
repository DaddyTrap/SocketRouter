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

class BaseRouteNode:

    send_sock = None
    recv_sock = None

    PACKET_DATA = "DATA"
    PACKET_ROUTE = "ROUTE"
    DATA_TXT = "TXT"
    DATA_JPEG = "JPEG"
    DATA_PNG = "PNG"
    ROUTE_LS = "LS"
    ROUTE_DV = "DV"

    TIMEOUT = None
    BUFFER_SIZE = 1024 * 1024 * 10
    SEQ_LIFETIME = 60

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
        self.recved_id_seq_tuples = []

        with open(node_file) as f:
            obj = json.load(f)
        self.node_id = obj['node_id']
        # self.send_sock.bind((obj['ip'], obj['port']))
        self.recv_sock.bind((obj['ip'], obj['port']))
        for k, v in obj['topo'].items():
            node_id = int(k)
            self.cost_table[node_id] = v['cost']
            self.forward_table[node_id] = node_id
            self.id_to_addr[node_id] = (v['real_ip'], v['real_port'])
            self.neighbors.append(node_id)

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
            "src_id": src_id,
            "dst_id": dst_id,
            "seq_num": seq_num,
            "packet_type": packet_type,
            "data_type": data_type,
            "data": data,
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

    @staticmethod
    def data_to_route_obj(data):
        ret = {}
        try:
            text = data.decode()
            lines = text.split('\n')
            for line in lines:
                split_res = line.split(' ')
                node_id = int(line[0])
                link_cost = int(line[1])
                ret[node_id] = link_cost
        except Exception as e:
            route_node_logger.error("Exception [{}] occurred!! Will stop parsing.".format(str(e)))
            return None
        return ret

    @staticmethod
    def route_obj_to_data(route_obj):
        ret = ''
        for k, v in route_obj.items():
            ret += '{} {}\n'.format(k, v)
        return ret.encode()

    # check the obj type and forward
    # DATA -> data_obj_handler
    # ROUTE -> route_obj_handler
    # raw is for forwarding
    def forward_obj(self, obj, raw):
        if obj['dst_id'] == -1 or obj['dst_id'] == self.node_id:
            # broadcast or self's
            if obj['dst_id'] == -1:
                # broadcast
                id_seq_tuple = ((obj['src_id'], obj['seq_num']), time.time())
                found = False
                will_recv = False
                for i in range(0, len(self.recved_id_seq_tuples)):
                    if self.recved_id_seq_tuples[i][0] == id_seq_tuple[0]:
                        found = True
                        if abs(self.recved_id_seq_tuples[i][1] - id_seq_tuple[1]) > BaseRouteNode.SEQ_LIFETIME:
                            will_recv = True
                            self.recved_id_seq_tuples.append(id_seq_tuple)

                if found == False:
                    will_recv = True
                    self.recved_id_seq_tuples.append(id_seq_tuple)

                if not will_recv:
                    route_node_logger.debug("Drop duplicate broadcast")
                    return

                # broadcast it
                for node_id in self.neighbors:
                    self.raw_send(raw, node_id)

            # receive it
            if obj['packet_type'] == BaseRouteNode.PACKET_ROUTE:
                self.route_obj_handler(obj)
            elif obj['packet_type'] == BaseRouteNode.PACKET_DATA:
                if isinstance(self.data_obj_handler, collections.Callable):
                    self.data_obj_handler(obj)
            else:
                route_node_logger.warn("Unknown packet type received")
        elif obj['dst_id'] != self.node_id:
            # not self's, forward it
            self.raw_send(raw, obj['dst_id'])

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
                    obj = BaseRouteNode.raw_to_obj(raw)
                    self.forward_obj(obj, raw)

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
    #     "packet_type": BaseRouteNode.PACKET_DATA,
    #     "data_type": BaseRouteNode.DATA_TXT,
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

class LSRouteNode(BaseRouteNode):

    BROADCAST_INFO_CD = 10

    def __init__(self, node_file, obj_handler, *args, **kwargs):
        BaseRouteNode.__init__(self, node_file, obj_handler, *args, **kwargs)
        with open(node_file) as f:
            obj = json.load(f)
        self.topo = {
            self.node_id: obj['topo']
        }
        for k in self.topo[self.node_id]:
            del self.topo[self.node_id][k]['real_ip']
            del self.topo[self.node_id][k]['real_port']

        self.last_broadcast_time = time.time()

    def route_obj_handler(self, route_obj):
        if route_obj['packet_type'] != 'LS':
            route_node_logger.warn("Wrong packet_type for this node")
            return
        new_info = BaseRouteNode.data_to_route_obj(route_obj['data'])

        updated = False        
        if route_obj['src_id'] in self.topo:
            old_info = self.topo[route_obj['src_id']]
            intersection = set(old_info.items()) & set(new_info.items())
            if len(intersection) > 0:
                self.topo[route_obj['src_id']] = new_info
                updated = True

        # broadcast self info
        if time.time() - self.last_broadcast_time >= LSRouteNode.BROADCAST_INFO_CD:
            self.broadcast_self_info()

        if updated:
            self.cost_table = LSRouteNode.ls_algo(self.node_id, self.topo, self.forward_table)
    
    def broadcast_self_info(self):
        self_info = {}
        # only send neighbor info
        for k in self.cost_table:
            if k in self.neighbors:
                self_info[k] = self.cost_table[k]
        data = BaseRouteNode.route_obj_to_data(self_info)
        packet = {
            "packet_type": BaseRouteNode.PACKET_ROUTE,
            "data_type": BaseRouteNode.ROUTE_LS,
            "data": data
        }
        self.send(packet, -1)

    def start(self):
        BaseRouteNode.start(self)
        self.broadcast_self_info()

    @staticmethod
    def ls_algo(source_node_id, topo, forward_table):
        if len(topo) == 0:
            return

        if source_node_id in topo:
            pass
        else:
            return
        N_ = set()
        N_.add(source_node_id)
        D = {}
        p = {}
        nodes = set()
        for key, val in topo.items():
            for k, v in val.items():
                nodes.add(key)
                nodes.add(k)
        for n in nodes:
            if n in topo[source_node_id]:
                D[n] = topo[source_node_id][n]
                p[n] = source_node_id
            else:
                D[n] = sys.maxsize
        D[source_node_id] = 0
        while len(N_) != len(nodes):
            tmp_list = sorted(D.items(), key=lambda asd: asd[1])
            for k, v in tmp_list:
                if k not in N_:
                    N_.add(k)
                    if k in topo:
                        for key, val in topo[k].items():
                            if (topo[k][key] + D[k] < D[key]):
                                p[key] = k
                                D[key] = topo[k][key] + D[k]
                    break
        for k, v in p.items():
            if v == source_node_id:
                tk = k
                last = v
                while tk != last:
                    last = tk
                    forward_table[tk] = k
                    for key, val in p.items():
                        if val == tk:
                            tk = key
                            break
        return D

class DVRouteNode(BaseRouteNode):

    @staticmethod
    def dv_algo(other_node_id, other_cost_table, source_cost_table, forward_table):
        changeFlag = False
        for k,v in other_cost_table.items():
            if k not in source_cost_table or source_cost_table[k] > source_cost_table[other_node_id] + other_cost_table[k]:
                source_cost_table[k] = source_cost_table[other_node_id] + other_cost_table[k]
                forward_table[k] = other_node_id
                changeFlag = True
        return changeFlag

    def __init__(self, node_file, obj_handler, *args, **kwargs):
        BaseRouteNode.__init__(self, node_file, obj_handler, *args, **kwargs)

    def route_obj_handler(self, route_obj):
        if route_obj['packet_type'] != 'DV':
            route_node_logger.warn("Wrong packet_type for this node")
            return
        other_info = BaseRouteNode.data_to_route_obj(route_obj['data'])
        changed = DVRouteNode.dv_algo(route_obj['src_id'], other_info, self.cost_table, self.forward_table)
        if changed:
            # send new cost table
            packet = {
                "packet_type": BaseRouteNode.PACKET_ROUTE,
                "data_type": BaseRouteNode.ROUTE_DV,
                "data": DVRouteNode.route_obj_to_data(self.cost_table)
            }
            for i in self.neighbors:
                self.send(packet, i)
