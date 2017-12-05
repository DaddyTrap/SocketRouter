def dv_algo(other_node, other_cost,source,source_cost,forward):
    changeFlag = False
    for k,v in other_cost.items():
        if k not in source_cost or source_cost[k] > source_cost[other_node] + other_cost[k]:
            source_cost[k] = source_cost[other_node]+other_cost[k]
            forward[k] = other_node
            changeFlag = True
    return changeFlag