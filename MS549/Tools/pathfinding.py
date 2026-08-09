import heapq


def find_shortest_path(graph, start_node, end_node):

    # Handle the case where the start or end node is not in the graph
    if start_node not in graph.adjacency_list:
        return (None, float("inf"))

    # Initialize the priority queue with the starting node and a distance of 0
    priorityQueue = [(0, start_node)]
    # Initialize distances dictionary with infinite distance for all nodes
    distances = {node: float("inf") for node in graph.adjacency_list}
    distances[start_node] = 0

    # Initialize predecessors dictionary to reconstruct the shortest path
    predecessors = {node: None for node in graph.adjacency_list}

    while priorityQueue:
        current_dist, current_node = heapq.heappop(priorityQueue)
        # If we reached the destination node stop the search
        if current_node == end_node:
            break
        # Skip if we already found a shorter path to this node
        if current_dist > distances[current_node]:
            continue
        # Check all neighbors of the current node
        for neighbor, weight in graph.adjacency_list.get(current_node, []):
            distance = current_dist + weight

            # If a shorter path to neighbor is found
            if distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = distance
                predecessors[neighbor] = current_node
                heapq.heappush(priorityQueue, (distance, neighbor))

    # Reconstruct path if destination was reached
    if distances.get(end_node, float("inf")) == float("inf"):
        return (None, float("inf"))

    path = []
    curr = end_node
    # Reconstruct the path from end_node to start_node using predecessors
    while curr is not None:
        path.append(curr)
        curr = predecessors[curr]
    # Reverse the path to get it from start to end
    path.reverse()  
    return (path, distances[end_node])