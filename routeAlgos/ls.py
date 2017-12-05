from sys import maxsize


def ls_algo(source_node, topo, forward_table):
    if len(topo) == 0:
        return

    if source_node in topo:
        pass
    else:
        return
    N_ = set()
    N_.add(source_node)
    D = {}
    p = {}
    nodes = set()
    for key, val in topo.items():
        for k, v in val.items():
            nodes.add(key)
            nodes.add(k)
    for n in nodes:
        if n in topo[source_node]:
            D[n] = topo[source_node][n]
            p[n] = source_node
        else:
            D[n] = maxsize
    D[source_node] = 0
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
        if v == source_node:
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


