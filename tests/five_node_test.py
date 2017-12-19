# import route_node
import route_node.route_node as route_node
import sys
import time
import signal
import json

def obj_handler(node_instance, obj):
    print("{}: {}".format(node_instance.name, obj['data'].decode()))

def data_change_handler(node_instance):
    print("{}: New Tables:\n---Cost Table---\n{}\n---End Cost Table---\n\n---Forward Table---\n{}\n---End Forward Table---\n".format(
                node_instance.name,
                json.dumps(node_instance.cost_table, sort_keys=True, indent=2),
                json.dumps(node_instance.forward_table, sort_keys=True, indent=2)
                ))

def gen_node(mode, node_filename):
    ret = None
    if mode == 'LS':
        ret = route_node.LSRouteNode(
                node_filename,
                obj_handler=obj_handler,
                data_change_handler=data_change_handler,
                name=node_filename,
                verbose=False
                )
    elif mode == 'DV':
        ret = route_node.DVRouteNode(
                node_filename,
                obj_handler=obj_handler,
                data_change_handler=data_change_handler,
                name=node_filename,
                verbose=False
                )
    return ret

def gen_nodes(mode):
    ret = []
    for i in range(1, 6):
        node = gen_node(mode, 'tests/five_node_test/node{}.json'.format(i))
        if node == None:
            print("Seems that mode `{}` does not exist".format(mode))
            return None
        ret.append(node)
    return ret

nodes = []

def stop(sig_num, frame):
    global nodes

    print("Stopping...")
    for node in nodes:
        node.stop()

    del nodes
    sys.exit(0)

if __name__ == '__main__':
    # global nodes
    
    if len(sys.argv) <= 1:
        print("One argument representing the node mode is needed.")
        sys.exit(0)
    mode = sys.argv[1]
    nodes = gen_nodes(mode)
    signal.signal(signal.SIGINT, stop)
    if not nodes:
        print("Generating nodes error")
        sys.exit(1)

    for node in nodes:
        node.start()
        print("{} started.".format(node.name))
        time.sleep(0.5)

    time.sleep(60)

