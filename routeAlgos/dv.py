def dv_algo(other_node, other_cost,source,source_cost,forward):
    changeFlag = False
    for k,v in forward_table.items():
        if v == other_node_id and k not in other_cost_table:
            source_cost_table.pop(k)
            forward_table.pop(k)

    for k,v in other_cost.items():
        if k not in source_cost or source_cost[k] > source_cost[other_node] + other_cost[k]:
            source_cost[k] = source_cost[other_node]+other_cost[k]
            forward[k] = other_node
            changeFlag = True
    return changeFlag