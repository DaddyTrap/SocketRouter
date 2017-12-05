import route_node

def handler(obj):
    print(obj)

if __name__ == "__main__":
    node = route_node.LSRouteNode('tests/node_conf_1.json', handler)
    node.start()
    node.stop()

    del node

    node = route_node.DVRouteNode('tests/node_conf_1.json', handler)
    node.start()
    node.stop()