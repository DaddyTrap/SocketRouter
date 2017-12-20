import route_node.route_node as route_node

forward_table = {}
topo = {
    1: {
        1: 0,
        3: 20,
        4: 10
    },
    3: {
        1: 20,
        4: 5,
        5: 5
    },
    4: {
        1: 10,
        3: 5,
        5: 5
    },
    5: {
        3: 5,
        4: 5
    }
}

ret = route_node.LSRouteNode.ls_algo(1, topo, forward_table)

print(forward_table)