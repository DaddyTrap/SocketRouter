# import route_node
import route_node.route_node as route_node
import sys
import time
import signal
import json

def obj_handler(node_instance, obj):
    print("{}: {}".format(node_instance.name, obj['data'].decode()))

def data_change_handler(node_instance):
    print("\n{} New Tables:\n---Cost Table---\n{}\n---End Cost Table---\n\n---Forward Table---\n{}\n---End Forward Table---\n".format(
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
    elif mode == "CLS":
        ret = route_node.CentralNormalNode(
                node_filename,
                obj_handler=obj_handler,
                data_change_handler=data_change_handler,
                name=node_filename,
                verbose=False
                )
    elif mode == "CLSC":
        ret = route_node.CentralControlNode(
                node_filename,
                obj_handler=obj_handler,
                data_change_handler=data_change_handler,
                name=node_filename,
                verbose=False
                )
    return ret

def gen_nodes(mode, test_base_dir):
    ret = []
    for i in range(1, 6):
        if mode == "CLS":
            if i == 5:
                node = gen_node(mode+"C", 'tests/{}/node{}.json'.format(test_base_dir, i))
                ret.append(node)
                continue
        node = gen_node(mode, 'tests/{}/node{}.json'.format(test_base_dir, i))
        if node == None:
            print("Seems that mode `{}` does not exist".format(mode))
            return None
        ret.append(node)
    return ret

nodes = []
base_dir = 'five_node_test_0'

def snapshot(dump_filename):
    global nodes
    
    dump_info = ''
    for node in nodes:
        # Dump tables to file
        dump_info += '[{} infos]\n'.format(node.name)
        dump_info += 'Cost Table:\n{}\n\n'.format(json.dumps(node.cost_table, sort_keys=True, indent=4))
        dump_info += 'Forward Table:\n{}\n\n'.format(json.dumps(node.forward_table, sort_keys=True, indent=4))
        if isinstance(node, route_node.LSRouteNode):
            dump_info += 'Topo:\n{}\n\n'.format(json.dumps(node.topo, sort_keys=True, indent=4))
        dump_info += '\n'

    with open(dump_filename, 'w') as f:
        f.write(dump_info)

def stop(sig_num=signal.SIGINT, frame=None):
    global nodes

    print("Stopping...")

    for node in nodes:
        node.stop()

    snapshot('stop.dump.txt')

    del nodes
    sys.exit(0)

def simple_test():
    global nodes

    for node in nodes:
        node.start()
        print("{} started.".format(node.name))
        time.sleep(0.5)

    print("[Going to do Simple Test]")

    time.sleep(route_node.BaseRouteNode.BEAT_TIME * 3)

    stop()

    snapshot('simple-test.dump.txt')

def dynamic_test():
    global nodes

    for node in nodes:
        node.start()
        print("{} started.".format(node.name))
        time.sleep(0.5)

    print("[Going to do Dynamic Test]")
    time.sleep(route_node.BaseRouteNode.BEAT_TIME * 2.5) # wait for the tables to be stable

    snapshot('first-stable.dump.txt')

    # test cost change
    print("\n--- Cost Change Test: Change node 3 cost ---")
    with open('tests/{}/node3.json'.format(base_dir)) as f:
        obj = json.load(f)
    obj['topo']['1']['cost'] = 2
    nodes[2].change_neighbors_cost(obj)

    with open('tests/{}/node1.json'.format(base_dir)) as f:
        obj = json.load(f)
    obj['topo']['3']['cost'] = 2
    nodes[0].change_neighbors_cost(obj)
    
    time.sleep(route_node.BaseRouteNode.BEAT_TIME * 1.5) # wait for the tables to be stable
    print("--- Cost Change Test: Finished ---\n")

    snapshot('cost-change.dump.txt')

    # test down check
    # make node 2 down
    print("\n--- Down Test: Stopped node 2 (Will cost {} seconds in default to notice a node was down) ---".format(route_node.BaseRouteNode.BEAT_TIME * 3))
    nodes[1].stop()
    time.sleep(route_node.BaseRouteNode.BEAT_TIME * 3) # wait for the tables to be stable
    print("--- Down Test: Finished ---\n")

    stop()

    snapshot('node-down.dump.txt')

def send_something_test():
    global nodes

    def send_something_obj_handler(node_instance, obj):
        if obj['data_type'] == route_node.BaseRouteNode.DATA_PNG:
            with open("{}-got-from-{}.png".format(node_instance.name, obj['src_id']), 'wb') as f:
                f.write(obj['data'])
            print('{} got a png from {}.'.format(node_instance.name, obj['src_id']))
        elif obj['data_type'] == route_node.BaseRouteNode.DATA_TXT:
            print('{} got a txt from {}: {}'.format(node_instance.name, obj['src_id'], obj['data'].decode()))
        else:
            print('{} got an unknown type message from {}'.format(node_instance.name, obj['src_id']))

    for node in nodes:
        node.data_obj_handler = send_something_obj_handler
        node.start()
        print("{} started.".format(node.name))
        time.sleep(0.5)

    print("[Going to do Send Something Test]")

    time.sleep(route_node.BaseRouteNode.BEAT_TIME * 1.5)

    png_packet = {
        'packet_type': route_node.BaseRouteNode.PACKET_DATA,
        'data_type': route_node.BaseRouteNode.DATA_PNG
    }
    with open('tests/test_file/santa.png', 'rb') as f:
        data = f.read()
    png_packet['data'] = data

    nodes[0].send(png_packet, 5)

    txt_packet = {
        'packet_type': route_node.BaseRouteNode.PACKET_DATA,
        'data_type': route_node.BaseRouteNode.DATA_TXT,
        'data': b'Hello Boy!'
    }
    # broadcast
    nodes[3].send(txt_packet, -1)

    print("--- Send Something Test: Finished ---")

    stop()

def main():
    global nodes
    route_node.BaseRouteNode.BEAT_TIME = 10
    test_type = ''
    if len(sys.argv) <= 1:
        print("One argument representing the node mode is needed.")
        sys.exit(0)
    if len(sys.argv) > 2:
        test_type = sys.argv[2]
    global base_dir
    base_dir = 'five_node_test_0'
    if len(sys.argv) > 3:
        base_dir = sys.argv[3]

    mode = sys.argv[1]
    nodes = gen_nodes(mode, base_dir)
    signal.signal(signal.SIGINT, stop)
    if not nodes:
        print("Generating nodes error")
        sys.exit(1)

    if test_type == 'dynamic':
        dynamic_test()
    elif test_type == 'send_something':
        send_something_test()
    else:
        simple_test()

if __name__ == '__main__':
    main()