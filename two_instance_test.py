import route_node
import time

def handler(obj):
    print(obj)

if __name__ == "__main__":
    node1 = route_node.LSRouteNode('tests/node_conf_1.json', handler)
    node2 = route_node.LSRouteNode('tests/node_conf_2.json', handler)
    node1.start()
    node2.start()

    packet = {
        "packet_type": route_node.BaseRouteNode.PACKET_DATA,
        "data_type": route_node.BaseRouteNode.DATA_TXT,
        "data": b'Hey guy!'
    }

    time.sleep(5)
    node1.send(packet, 2)
    node2.send(packet, 1)
    time.sleep(1)

    node1.stop()
    node2.stop()