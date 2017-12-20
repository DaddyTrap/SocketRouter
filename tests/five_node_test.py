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

def gen_nodes(mode):
    ret = []
    for i in range(1, 6):
        node = gen_node(mode, 'tests/five_node_test/node{}.json'.format(i))
        if mode == "CLS":
            if i == 5:
                node = gen_node(mode+"C", 'tests/five_node_test/node{}.json'.format(i))
                ret.append(node)
                continue
        if node == None:
            print("Seems that mode `{}` does not exist".format(mode))
            return None
        ret.append(node)
    return ret

nodes = []

def stop(sig_num=signal.SIGINT, frame=None):
    global nodes

    dump_info = ''

    print("Stopping...")
    for node in nodes:
        node.stop()
        # Dump tables to file
        dump_info += '[{} infos]\n'.format(node.name)
        dump_info += 'Cost Table:\n{}\n\n'.format(json.dumps(node.cost_table, sort_keys=True, indent=4))
        dump_info += 'Forward Table:\n{}\n\n'.format(json.dumps(node.forward_table, sort_keys=True, indent=4))
        dump_info += '\n'

    with open('test_dump_info.txt', 'w') as f:
        f.write(dump_info)

    del nodes
    sys.exit(0)

def simple_test():
    global nodes

    for node in nodes:
        node.start()
        print("{} started.".format(node.name))
        time.sleep(0.5)

    print("[Going to do Simple Test]")

    time.sleep(60)

    stop()

def dynamic_test():
    global nodes

    for node in nodes:
        node.start()
        print("{} started.".format(node.name))
        time.sleep(0.5)

    print("[Going to do Dynamic Test]")

    # test cost change
    print("\n--- Cost Change Test: Change node 3 cost ---")
    with open('tests/five_node_test/node3.json') as f:
        obj = json.load(f)
    obj['topo']['1']['cost'] = 2
    nodes[2].change_neighbors_cost(obj)
    time.sleep(30) # wait for the tables to be stable
    print("--- Cost Change Test: Finished ---\n")

    # test down check
    time.sleep(30) # wait for the tables to be stable
    # make B down
    print("\n--- Down Test: Stopped node 2 (Will cost 60 seconds in default to notice a node was down) ---")
    nodes[1].stop()
    time.sleep(route_node.BaseRouteNode.BEAT_TIME * 2 + 10) # wait for the
    print("--- Down Test: Finished ---\n")

    stop()

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

    time.sleep(15)

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
    test_type = ''
    if len(sys.argv) <= 1:
        print("One argument representing the node mode is needed.")
        sys.exit(0)
    if len(sys.argv) > 2:
        test_type = sys.argv[2]

    mode = sys.argv[1]
    nodes = gen_nodes(mode)
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