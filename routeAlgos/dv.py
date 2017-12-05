def dv_algo(other_node, other_cost,source,source_cost,forward):
    for k,v in other_cost.items():
        if k not in source_cost:
            source_cost[k] = source_cost[other_node]+other_cost[k]
            forward[k] = other_node
        elif source_cost[k] > source_cost[other_node] + other_cost[k]:
            source_cost[k] = source_cost[other_node] + other_cost[k]
            forward[k] = other_node
