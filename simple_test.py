import route_node

def handler(obj):
    print(obj)

if __name__ == "__main__":
    node = route_node.LSRouteNode('node_conf.json', handler)
    node.start()
    node.stop()

    del node

    node = route_node.DVRouteNode('node_conf.json', handler)
    node.start()
    node.stop()