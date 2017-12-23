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
import traceback


class BaseRouteNode:

    send_sock = None
    recv_sock = None

    PACKET_DATA = "DATA"
    PACKET_ROUTE = "ROUTE"
    PACKET_BEAT = "BEAT"
    
    DATA_TXT = "TXT"
    DATA_JPEG = "JPEG"
    DATA_PNG = "PNG"

    ROUTE_LS = "LS"
    ROUTE_DV = "DV"
    ROUTE_C_LS = 'CLS' # for central route
    ROUTE_REQ = "REQ"

    BEAT_BEAT = "BEAT"

    TIMEOUT = 2
    BUFFER_SIZE = 1024 * 1024 * 10
    SEQ_LIFETIME = 60
    BEAT_TIME = 30
    TICK_TIME = 1

    def build_logger(self, name, verbose=True):
        # create logger with 'RouteNode'
        self.logger = logging.Logger(name)
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler('{}.log'.format(name))
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('[%(filename)s:%(lineno)s - %(funcName)s()] %(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the self.logger
        self.logger.addHandler(fh)
        if verbose:
            self.logger.addHandler(ch)

        self.logger.info("LOGGER INITIALIZED!!!!")

    def change_neighbors_cost(self, obj):
        self.forward_table = {}
        self.cost_table = {}
        self.id_to_addr = {}
        self.neighbors = []
        self.down_check_table = {}
        for k, v in obj['topo'].items():
            node_id = int(k)
            self.cost_table[node_id] = v['cost']
            self.forward_table[node_id] = node_id
            self.id_to_addr[node_id] = (v['real_ip'], v['real_port'])
            self.neighbors.append(node_id)
            self.down_check_table[node_id] = {
                "last_recved_time": time.time(),
                "origin_cost": v['cost'],
                "downed": False
            }
        self.cost_table[self.node_id] = 0
        self.forward_table[self.node_id] = self.node_id
        self.send_self_info()
        self.send_route_req()

    def __init__(self, node_file, obj_handler, data_change_handler, name='RouteNode', *args, **kwargs):
        self.forward_table = {}
        self.cost_table = {}
        self.id_to_addr = {}
        self.neighbors = []
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_seq_num = random.randint(0, sys.maxsize)
        self.data_obj_handler = obj_handler

        # called when [forward_table, cost_table] changed
        self.data_change_handler = data_change_handler

        self.running = False
        self.broadcast_seq_num = 0
        self.recved_id_seq_tuples = []
        self.down_check_table = {}

        if isinstance(node_file, dict):
            obj = node_file
        else:
            with open(node_file) as f:
                obj = json.load(f)

        self.node_id = int(obj['node_id'])
        self.recv_sock.bind((obj['ip'], obj['port']))
        for k, v in obj['topo'].items():
            node_id = int(k)
            self.cost_table[node_id] = v['cost']
            self.forward_table[node_id] = node_id
            self.id_to_addr[node_id] = (v['real_ip'], v['real_port'])
            self.neighbors.append(node_id)
            self.down_check_table[node_id] = {
                "last_recved_time": time.time(),
                "origin_cost": v['cost'],
                "downed": False
            }
        self.name = obj['name']
        
        self.cost_table[self.node_id] = 0
        self.forward_table[self.node_id] = self.node_id
        
        if 'verbose' in kwargs:
            self.build_logger(self.name, kwargs['verbose'])
        else:
            self.build_logger(self.name)

        if isinstance(self.data_change_handler, collections.Callable):
            self.data_change_handler(self)

        self.send_route_req()

    def raw_to_obj(self, raw_proto_data):
        text = raw_proto_data.decode('utf-8', 'ignore')
        
        # for better performance
        text_io = io.StringIO(text)
        
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
            data_type = split_res[1][:-1] # cut '\n'
            # DATA
            data = raw_proto_data[data_begin:]
        except Exception as e:
            self.logger.error(e)

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

    def data_to_route_obj(self, data):
        ret = {}
        try:
            text = data.decode()
            lines = text.split('\n')
            for line in lines:
                if len(line) == 0:
                    continue
                split_res = line.split(' ')
                node_id = int(split_res[0])
                link_cost = int(split_res[1])
                ret[node_id] = link_cost
        except Exception as e:
            self.logger.error("Exception [{}] occurred!! Will stop parsing.".format(str(e)))
            self.logger.error("\n{}".format(traceback.format_exc()))
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
        self.logger.debug("Got packet from {}:\n{}".format(obj['src_id'], raw))
        src_id = obj['src_id']
        cur_time = time.time()

        # only neighbors in the down_check_table
        if src_id in self.down_check_table.keys():
            # update last_recved_time
            self.down_check_table[src_id]['last_recved_time'] = cur_time
            if self.down_check_table[src_id]['downed'] == True:
                # up again
                # TODO: Maybe this is not a good way to `up` it
                self.down_check_table[src_id]['downed'] = False
                self.cost_table[src_id] = self.down_check_table[src_id]['origin_cost']
                self.forward_table[src_id] = src_id
                self.neighbors.append(src_id)
                self.on_node_up(src_id)
                
                # if isinstance(self.data_change_handler, collections.Callable):
                #     self.data_change_handler(self)


        if obj['dst_id'] == -1 or obj['dst_id'] == self.node_id:
            # broadcast or self's
            if obj['dst_id'] == -1:
                # broadcast
                id_seq_tuple = ((src_id, obj['seq_num']), time.time())
                found = False
                will_recv = False

                # check if it is a broadcast that has been received
                for i in range(0, len(self.recved_id_seq_tuples)):
                    if self.recved_id_seq_tuples[i][0] == id_seq_tuple[0]:
                        found = True
                        if abs(self.recved_id_seq_tuples[i][1] - id_seq_tuple[1]) > BaseRouteNode.SEQ_LIFETIME:
                            will_recv = True
                            self.recved_id_seq_tuples.append(id_seq_tuple)

                if found == False:
                    will_recv = True
                    # append it into the recved list
                    self.recved_id_seq_tuples.append(id_seq_tuple)

                if not will_recv:
                    self.logger.debug("Drop duplicate broadcast")
                    return

                # broadcast it
                for node_id in self.neighbors:
                    if node_id != obj['src_id']:
                        self.raw_send(raw, node_id)

            # receive it
            if obj['packet_type'] == BaseRouteNode.PACKET_ROUTE:
                self.route_obj_handler(obj)
            elif obj['packet_type'] == BaseRouteNode.PACKET_DATA:
                if isinstance(self.data_obj_handler, collections.Callable):
                    self.data_obj_handler(self, obj)
            elif obj['packet_type'] == BaseRouteNode.PACKET_BEAT:
                pass
            else:
                self.logger.warn("Unknown packet type received")
        elif obj['dst_id'] != self.node_id:
            # not self's, forward it
            self.raw_send(raw, obj['dst_id'])

    def select_thread_func(self):
        inputs = [self.recv_sock]
        outputs = []
        
        while self.running:
            # self.logger.debug("Waiting for next event...")
            readable, writable, exceptional = select.select(inputs, outputs, inputs, self.TIMEOUT)
            if not (readable or writable or exceptional):
                # timeout
                # self.logger.warn("TIME OUT!!")
                pass
            for s in readable:
                if s is self.recv_sock:
                    raw, addr = s.recvfrom(self.BUFFER_SIZE)
                    # self.logger.debug("Recved raw from {}:\n{}".format(addr, raw))
                    obj = self.raw_to_obj(raw)
                    self.forward_obj(obj, raw)

            # for s in writable:
            #     if s is self.send_sock:
            #         while not self.send_queue.empty():
            #             try:
            #                 raw_data, addr = self.send_queue.get_nowait()
            #             except queue.Empty:
            #                 self.logger.debug('send_queue empty')
            #             else:
            #                 s.sendto(raw_data, addr)

            for s in exceptional:
                self.logger.error("Exception on {}".format(s.getpeername()))

    def check_down(self):
        # check down
        cur_time = time.time()
        down_nodes = []
        something_down = False
        for k, v in self.down_check_table.items():
            if not v['downed'] and cur_time - v['last_recved_time'] > BaseRouteNode.BEAT_TIME * 2:
                # think it's down
                self.logger.debug("{} seems downed: {} - {} = {}".format(k, cur_time, v['last_recved_time'], cur_time - v['last_recved_time']))
                down_nodes.append(k)
                # modify table to make it `down`
                self.down_check_table[k]['downed'] = True
                if k in self.cost_table:
                    del self.cost_table[k]
                if k in self.forward_table:
                    del self.forward_table[k]
                for forward_table_k, forward_table_v in [i for i in self.forward_table.items()]:
                    if forward_table_v == k:
                        del self.forward_table[forward_table_k]
                self.neighbors.remove(k)
                something_down = True
        
        if something_down and isinstance(self.data_change_handler, collections.Callable):
            self.data_change_handler(self)

        if len(down_nodes) > 0:
            self.logger.info("nodes: {} seem(s) downed".format(down_nodes))
            self.on_nodes_down(down_nodes)

    def tick_thread_func(self):
        while self.running:
            self.beat_func()
            self.on_tick()
            time.sleep(self.TICK_TIME)

    def on_tick(self):
        raise NotImplementedError

    _beat_count = 0
    def beat_func(self):
        if self._beat_count % int(BaseRouteNode.BEAT_TIME) == 0:
            self._beat_count = 0
            packet = {
                "packet_type": BaseRouteNode.PACKET_BEAT,
                "data_type": BaseRouteNode.BEAT_BEAT,
                "data": "ALIVE"
            }
            self.send(packet, -1)
            self.check_down()
        self._beat_count += 1

    def start(self):
        # start thread to select socket
        self.running = True
        self.select_thread = threading.Thread(target=self.select_thread_func)
        self.select_thread.start()
        self.tick_thread = threading.Thread(target=self.tick_thread_func)
        self.tick_thread.start()

    def stop(self):
        self.running = False
        self.select_thread.join()
        self.tick_thread.join()
        self.logger.debug("Stopped!!!")

    # packet: {
    #     "packet_type": BaseRouteNode.PACKET_DATA,
    #     "data_type": BaseRouteNode.DATA_TXT,
    #     "data": "Hello example txt"
    # }
    # dst_node_id: Destination node id
    def send(self, packet, dst_node_id):
        # build seq num in obj_to_raw()
        raw_data = self.obj_to_raw(packet, dst_node_id)
        # if (dst_node_id == -1):
        #     # broadcast
        #     for node in self.neighbors:
        #         self.raw_send(raw_data, dst_node_id)
        # else:
        self.raw_send(raw_data, dst_node_id)

    def raw_send(self, raw_data, dst_node_id):
        if not dst_node_id in self.forward_table and dst_node_id != -1:
            self.logger.warn("No such id in forward_table yet")
            return 0
        self.logger.info("Going to send to {}:\n{}".format(dst_node_id, raw_data))
        if dst_node_id == -1:
            for node_id in self.neighbors:
                if not node_id in self.forward_table:
                    self.logger.warn("node_id: {} not reachable".format(node_id))
                    continue
                    # raise Exception("node_id not reachable")
                next_node_id = self.forward_table[node_id]
                msg_tuple = (raw_data, self.id_to_addr[next_node_id])
                self.send_sock.sendto(msg_tuple[0], msg_tuple[1])
        else:
            if not dst_node_id in self.forward_table:
                self.logger.warn("node_id: {} not reachable".format(dst_node_id))
                return
                # raise Exception("node_id not reachable")
            next_node_id = self.forward_table[dst_node_id]
            msg_tuple = (raw_data, self.id_to_addr[next_node_id])
            self.send_sock.sendto(msg_tuple[0], msg_tuple[1])

    def send_route_req(self):
        packet = {
            "packet_type": BaseRouteNode.PACKET_ROUTE,
            "data_type": BaseRouteNode.ROUTE_REQ,
            "data": "REQ"
        }
        for node_id in self.neighbors:
            self.send(packet, node_id)
        
    def route_obj_handler(self, route_obj):
        # Should be override
        raise NotImplementedError

    def on_nodes_down(self, node_ids):
        # Should be override
        raise NotImplementedError

    def send_self_info(self):
        raise NotImplementedError

    def on_node_up(self, node_id):
        self.send_self_info()

class LSRouteNode(BaseRouteNode):

    BROADCAST_INFO_CD = 10

    def __init__(self, node_file, obj_handler, data_change_handler, name='RouteNode', *args, **kwargs):
        BaseRouteNode.__init__(self, node_file, obj_handler, data_change_handler, name, *args, **kwargs)
        if isinstance(node_file, dict):
            obj = node_file
        else:
            with open(node_file) as f:
                obj = json.load(f)
        topo = {}
        for k, v in obj['topo'].items():
            topo[int(k)] = v['cost']
        self.topo = {
            self.node_id: topo
        }
        # for k in self.topo[self.node_id]:
        #     del self.topo[self.node_id][k]['real_ip']
        #     del self.topo[self.node_id][k]['real_port']
        self.topo[self.node_id][self.node_id] = 0

        self.last_broadcast_time = time.time()

    def route_obj_handler(self, route_obj):
        self.logger.debug("Got route_obj:\n{}".format(route_obj))

        if route_obj['data_type'] == BaseRouteNode.ROUTE_REQ:
            self.send_self_info()
            return
        if route_obj['data_type'] != BaseRouteNode.ROUTE_LS:
            self.logger.warn("Wrong data_type for this node")
            return
        new_info = self.data_to_route_obj(route_obj['data'])

        topo_updated = False
        if route_obj['src_id'] in self.topo:
            old_info = self.topo[route_obj['src_id']]
            self.logger.debug(old_info)

            if set(old_info.keys()) != set(new_info.keys()):
                topo_updated = True
            else:
                topo_updated = False
                for k, v in old_info.items():
                    if old_info[k] != new_info[k]:
                        topo_updated = True
                        break   

            if topo_updated:
                self.topo[route_obj['src_id']] = new_info
                # for k, v in [i for i in self.forward_table.items()]:
                #     if v == route_obj['src_id'] and not k in new_info:
                #         del self.forward_table[k]

        else:
            self.topo[route_obj['src_id']] = new_info
            topo_updated = True

        # broadcast self info
        # if time.time() - self.last_broadcast_time >= LSRouteNode.BROADCAST_INFO_CD:
        #     self.broadcast_self_info()

        if topo_updated:
            self.cost_table = LSRouteNode.ls_algo(self.node_id, self.topo, self.forward_table)
            
            if isinstance(self.data_change_handler, collections.Callable):
                self.data_change_handler(self)
            self.logger.debug("cost_table changed:\n{}".format(self.cost_table))
            self.logger.debug("forward_table changed:\n{}".format(self.forward_table))
        else:
            self.logger.debug("Nothing changed.")
    
    def send_self_info(self):
        self_info = {}
        # only send neighbor info
        # for k in self.cost_table:
        #     if k in self.neighbors:
        #         self_info[k] = self.cost_table[k]
        for k, v in self.down_check_table.items():
            if not v['downed']:
                self_info[k] = v['origin_cost']
        data = BaseRouteNode.route_obj_to_data(self_info)
        packet = {
            "packet_type": BaseRouteNode.PACKET_ROUTE,
            "data_type": BaseRouteNode.ROUTE_LS,
            "data": data
        }
        self.send(packet, -1)

    def start(self):
        BaseRouteNode.start(self)
        self.send_self_info()

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
        forward_table.clear()
        for k, v in p.items():
            if v != source_node_id:
                tv = v
                while tv in p and p[tv] != source_node_id:
                    tv = p[tv]
                forward_table[k] = tv
            elif v != k:
                forward_table[k] = k
        forward_table[source_node_id] = source_node_id
        return D

    def on_nodes_down(self, node_ids):
        for node_id in node_ids:
            if node_id in self.topo:
                del self.topo[node_id]
            if node_id in self.topo[self.node_id]:
                del self.topo[self.node_id][node_id]
        self.cost_table = LSRouteNode.ls_algo(self.node_id, self.topo, self.forward_table)
        self.send_self_info()

    cur_count = 0
    def on_tick(self):
        if self.cur_count % int(self.BEAT_TIME / 2) == 0:
            self.cur_count = 0
            self.send_self_info()
        self.cur_count += 1

    def change_neighbors_cost(self, obj):
        self.forward_table = {}
        self.cost_table = {}
        self.id_to_addr = {}
        self.neighbors = []
        self.down_check_table = {}
        for k, v in obj['topo'].items():
            node_id = int(k)
            self.cost_table[node_id] = v['cost']
            self.forward_table[node_id] = node_id
            self.id_to_addr[node_id] = (v['real_ip'], v['real_port'])
            self.neighbors.append(node_id)
            self.down_check_table[node_id] = {
                "last_recved_time": time.time(),
                "origin_cost": v['cost'],
                "downed": False
            }
        self.cost_table[self.node_id] = 0
        self.forward_table[self.node_id] = self.node_id

        topo = {}
        for k, v in obj['topo'].items():
            topo[int(k)] = v['cost']
        self.topo = {
            self.node_id: topo
        }
        self.topo[self.node_id][self.node_id] = 0

        self.send_self_info()
        self.send_route_req()

    def on_node_up(self, node_id):
        self.topo[self.node_id][node_id] = self.down_check_table[node_id]['origin_cost']
        self.send_self_info()
        
class DVRouteNode(BaseRouteNode):
    def __init__(self, node_file, obj_handler, data_change_handler, name='RouteNode', *args, **kwargs):
        BaseRouteNode.__init__(self, node_file, obj_handler, data_change_handler, name, *args, **kwargs)

    def dv_algo(self,other_node_id, other_cost_table, source_cost_table, forward_table):
        changeFlag = False
        for k,v in [i for i in forward_table.items()]:
            if v == other_node_id and k not in other_cost_table and k != other_node_id:
                if k in self.down_check_table and not self.down_check_table[k]['downed']:
                    source_cost_table[k] = self.down_check_table[k]['origin_cost']
                else:
                    source_cost_table.pop(k)
                forward_table.pop(k)

        for k,v in other_cost_table.items():
            if k not in source_cost_table or source_cost_table[k] > source_cost_table[other_node_id] + other_cost_table[k]:
                source_cost_table[k] = source_cost_table[other_node_id] + other_cost_table[k]
                forward_table[k] = other_node_id
                changeFlag = True
        forward_table[self.node_id] = self.node_id
        return changeFlag

    def route_obj_handler(self, route_obj):
        self.logger.debug("Got route_obj:\n{}".format(route_obj))
        if route_obj['data_type'] == BaseRouteNode.ROUTE_REQ:
            self.send_self_info()
            return
        if route_obj['data_type'] != BaseRouteNode.ROUTE_DV:
            self.logger.warn("Wrong data_type for this node")
            return
        other_info = self.data_to_route_obj(route_obj['data'])
        changed = self.dv_algo(route_obj['src_id'], other_info, self.cost_table, self.forward_table)
        if changed:
            self.send_self_info()
            self.logger.debug("cost_table changed:\n{}".format(self.cost_table))
            self.logger.debug("forward_table changed:\n{}".format(self.forward_table))
            
            if isinstance(self.data_change_handler, collections.Callable):
                self.data_change_handler(self)
        else:
            self.logger.debug("Nothing changed.")

    def send_self_info(self):
        # send new cost table
        packet = {
            "packet_type": BaseRouteNode.PACKET_ROUTE,
            "data_type": BaseRouteNode.ROUTE_DV,
            "data": None
        }
        for i in self.neighbors:
            poison_reverse_packet = dict(packet)
            poison_reverse_route_obj = dict(self.cost_table)
            for k, v in self.forward_table.items():
                if v == i:
                    poison_reverse_route_obj[k] = sys.maxsize
            poison_reverse_packet['data'] = DVRouteNode.route_obj_to_data(poison_reverse_route_obj)
            self.send(poison_reverse_packet, i)

    def on_nodes_down(self, node_ids):
        self.send_self_info()

    def start(self):
        BaseRouteNode.start(self)
        self.send_self_info()

    cur_count = 0
    def on_tick(self):
        if self.cur_count % int(self.BEAT_TIME / 2) == 0:
            self.cur_count = 0
            self.send_self_info()
        self.cur_count += 1

class CentralControlNode(LSRouteNode):
    def __init__(self, node_file, obj_handler, data_change_handler, name='RouteNode', *args, **kwargs):
        LSRouteNode.__init__(self, node_file, obj_handler, data_change_handler, name, *args, **kwargs)
        self.control_forward_table = {}
        self.control_cost_table = {}

    def cls_route_to_data(self,cls):
        data = ''
        for k,v in cls.items():
            for k_,v_ in v.items():
                data += '{} {} {}\n'.format(k,k_,v_)
        return data.encode()


    def route_obj_handler(self, route_obj):
        self.logger.debug("Got route_obj:\n{}".format(route_obj))

        if route_obj['data_type'] == BaseRouteNode.ROUTE_REQ:
            self.send_self_info()
            return
        if route_obj['data_type'] != BaseRouteNode.ROUTE_LS:
            self.logger.warn("Wrong data_type for this node")
            return
        new_info = self.data_to_route_obj(route_obj['data'])

        topo_updated = False
        if route_obj['src_id'] in self.topo:
            old_info = self.topo[route_obj['src_id']]
            self.logger.debug(old_info)

            if set(old_info.keys()) != set(new_info.keys()):
                topo_updated = False
            else:
                topo_updated = False
                for k, v in old_info.items():
                    if old_info[k] != new_info[k]:
                        topo_updated = True
                        break   

            if topo_updated:
                # print(old_info)
                # print(new_info)
                self.topo[route_obj['src_id']] = new_info
        else:
            self.topo[route_obj['src_id']] = new_info
            topo_updated = True



        # if time.time() - self.last_broadcast_time >= LSRouteNode.BROADCAST_INFO_CD:
        #     self.broadcast_self_info()

           
        if topo_updated:
            self.control_cost_table = CentralControlNode.central_ls_algo(self.node_id, self.topo, self.control_forward_table)
            self.forward_table = self.control_forward_table[self.node_id]
            self.cost_table = self.control_cost_table[self.node_id]
            
            if isinstance(self.data_change_handler, collections.Callable):
                self.data_change_handler(self)
            self.logger.debug("cost_table changed:\n{}".format(self.cost_table))
            self.logger.debug("forward_table changed:\n{}".format(self.forward_table))
            self.broadcast_control_info()
        else:
            self.logger.debug("Nothing changed.")


    def broadcast_control_info(self):
        # only send neighbor info
        data = self.cls_route_to_data(self.control_forward_table)
        packet = {
            "packet_type": BaseRouteNode.PACKET_ROUTE,
            "data_type": BaseRouteNode.ROUTE_C_LS,
            "data": data
        }
        self.send(packet, -1)
    
    @staticmethod
    def central_ls_algo(source_node_id, topo, forward_table):
        if len(topo) == 0:
            return
        nodes = set()
        for key, val in topo.items():
            for k, v in val.items():
                nodes.add(k)
                nodes.add(k)
        D = {}
        p = {}

        for start_node_id in nodes:
            if start_node_id in topo:
                pass
            else:
                continue
            D[start_node_id]={}
            p[start_node_id]={}
            forward_table[start_node_id] = {}
            N_ = set()
            N_.add(start_node_id)


            for n in nodes:
                if n in topo[start_node_id]:
                    D[start_node_id][n] = topo[start_node_id][n]
                    p[start_node_id][n] = start_node_id
                else:
                    D[start_node_id][n] = sys.maxsize

            D[start_node_id][start_node_id] = 0
            while len(N_) != len(nodes):
                tmp_list = sorted(D[start_node_id].items(), key=lambda asd: asd[1])
                for k, v in tmp_list:
                    if k not in N_:
                        N_.add(k)
                        if k in topo:
                            for key, val in topo[k].items():
                                if (topo[k][key] + D[start_node_id][k] < D[start_node_id][key]):
                                    p[start_node_id][key] = k
                                    D[start_node_id][key] = topo[k][key] + D[start_node_id][k]
                        break
            for k, v in p[start_node_id].items():
                if v != start_node_id:
                    tv = v
                    while tv in p[start_node_id] and p[start_node_id][tv] != start_node_id:
                        tv = p[start_node_id][tv]
                    forward_table[start_node_id][k] = tv
                elif v != k:
                    forward_table[start_node_id][k] = k
            forward_table[start_node_id][start_node_id] = start_node_id
        return D


class CentralNormalNode(LSRouteNode):
    def __init__(self, node_file, obj_handler, data_change_handler, name='RouteNode', *args, **kwargs):
        LSRouteNode.__init__(self, node_file, obj_handler, data_change_handler, name, *args, **kwargs)
        self.central = None
    
    def data_to_cls_route(self,data):
        ret = {}
        try:
            text = data.decode()
            lines = text.split('\n')
            for line in lines:
                if len(line) == 0:
                    continue
                split_res = line.split(' ')
                node_id = int(split_res[0])
                start = int(split_res[1])
                via = int(split_res[2])
                if node_id not in ret:
                    ret[node_id] = {}
                ret[node_id][start] = via
        except Exception as e:
            self.logger.error("Exception [{}] occurred!! Will stop parsing.".format(str(e)))
            self.logger.error("\n{}".format(traceback.format_exc()))
            return None

        return ret

    def route_obj_handler(self,route_obj):
        if route_obj['data_type'] == BaseRouteNode.ROUTE_C_LS:
            self.central = route_obj['src_id']
            new_forward = self.data_to_cls_route(route_obj['data'])
            if self.node_id in new_forward:
                self.forward_table = new_forward[self.node_id]
                self.logger.debug("forward_table changed:\n{}".format(self.forward_table))
                if isinstance(self.data_change_handler, collections.Callable):
                    self.data_change_handler(self)
            return
        # elif route_obj['data_type'] != BaseRouteNode.ROUTE_LS:
        #     self.logger.warn("Wrong data_type for this node")
        #     return
        # self.logger.debug("Got route_obj:\n{}".format(route_obj))
        # new_info = self.data_to_route_obj(route_obj['data'])

        # updated = False        
        # if route_obj['src_id'] in self.topo:
        #     old_info = self.topo[route_obj['src_id']]
        #     for k, v in old_info.items():
        #         old_info[k] = v['cost']
        #     self.logger.debug(old_info)
        #     intersection = set(old_info.items()) & set(new_info.items())
        #     if len(intersection) > 0:
        #         self.topo[route_obj['src_id']] = new_info
        #         updated = True

        # broadcast self info
        # if time.time() - self.last_broadcast_time >= LSRouteNode.BROADCAST_INFO_CD:
        #     self.broadcast_self_info()

        # if updated:
        #     self.cost_table = LSRouteNode.ls_algo(self.node_id, self.topo, self.forward_table)
        #     self.logger.debug("cost_table changed:\n{}".format(self.cost_table))
        #     self.logger.debug("forward_table changed:\n{}".format(self.forward_table))
        # else:
        #     self.logger.debug("Nothing changed.")