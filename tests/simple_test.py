import route_node

def handler(obj):
    print(obj)

if __name__ == "__main__":
    node = route_node.LSRouteNode('simple_test/node_conf_1.json', obj_handler=handler)
    node.start()
    node.stop()

    del node

    node = route_node.DVRouteNode('simple_test/node_conf_1.json', obj_handler=handler)
    node.start()
    node.stop()