import heapq


def find_shortest_path(graph: Any, start_node: str, end_node: str) -> Tuple[Optional[List[str]], float]:
    # Implements Dijkstra's algorithm to find the shortest path from start_node to end_node in the given graph.
    if start_node not in graph.adjacency_list or end_node not in graph.adjacency_list:
        return None, float("inf")

    # Handle trivial case where start and end are identical
    if start_node == end_node:
        return [start_node], 0.0
    # Initialize tracking structures across all known graph nodes
    all_nodes = set(graph.adjacency_list.keys()).union(getattr(graph, "node_coordinates", {}).keys())
    distances = {node: float("inf") for node in all_nodes}
    predecessors = {node: None for node in all_nodes}
    distances[start_node] = 0.0
    priority_queue: List[Tuple[float, str]] = [(0.0, start_node)]
    while priority_queue:
        current_dist, current_node = heapq.heappop(priority_queue)

        # Early exit if target destination node is reached
        if current_node == end_node:
            break

        # Skip processing if a shorter path to current_node was already processed
        if current_dist > distances[current_node]:
            continue

        # Explore adjacent neighbors
        for neighbor, weight in graph.adjacency_list.get(current_node, []):
            new_distance = current_dist + weight

            if new_distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_distance
                predecessors[neighbor] = current_node
                heapq.heappush(priority_queue, (new_distance, neighbor))

    # Return None if target end node was unreachable
    if distances.get(end_node, float("inf")) == float("inf"):
        return None, float("inf")

    # Reconstruct shortest path by backtracking from end_node
    path = []
    curr: Optional[str] = end_node
    while curr is not None:
        path.append(curr)
        curr = predecessors.get(curr)

    path.reverse()
    return path, distances[end_node]