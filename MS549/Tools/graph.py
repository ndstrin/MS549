import collections
import heapq
from typing import Dict, List, Tuple, Optional


class Graph:
    # Represents a weighted, undirected graph using an adjacency list and node coordinates.

    def __init__(self):
        # Initializes the graph with an empty adjacency list and node coordinates dictionary.
        self.adjacency_list: Dict[str, List[Tuple[str, float]]] = collections.defaultdict(list)
        self.node_coordinates: Dict[str, Tuple[float, float]] = {}

    def load_map_data(self, filename: str) -> None:
        # Loads graph data from a CSV file, populating the adjacency list and node coordinates.
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("#") or not line.strip():
                    continue
                # Split the line into parts and unpack them into variables
                parts = line.strip().split(",")
                (
                    start_id,
                    start_x,
                    start_y,
                    end_id,
                    end_x,
                    end_y,
                    weight,
                ) = parts
                # Store the coordinates of the start and end nodes
                self.node_coordinates[start_id] = (float(start_x), float(start_y))
                self.node_coordinates[end_id] = (float(end_x), float(end_y))
                # Add the edge to the adjacency list for both directions (undirected graph)
                self.adjacency_list[start_id].append((end_id, float(weight)))
                self.adjacency_list[end_id].append((start_id, float(weight)))

    def find_nearest_vertex(self, point: Tuple[float, float]) -> str:
        # Compares an (x, y) coordinate tuple against graph node coordinates
        # and returns the vertex ID with the smallest squared Euclidean distance.
        if not self.node_coordinates:
            raise ValueError("Cannot snap coordinate: Graph node coordinates are empty.")

        px, py = point
        best_node = None
        min_sq_dist = float("inf")

        # Iterate through all nodes to find the nearest vertex
        for node_id, (nx, ny) in self.node_coordinates.items():
            sq_dist = (nx - px) ** 2 + (ny - py) ** 2
            if sq_dist < min_sq_dist:
                min_sq_dist = sq_dist
                best_node = node_id

        return best_node

    def dijkstra(self, start_node: str, end_node: str) -> Tuple[Optional[List[str]], float]:
       # Implements Dijkstra's algorithm to find the shortest path from start_node to end_node.
        if start_node not in self.adjacency_list or end_node not in self.adjacency_list:
            return None, float("inf")

        distances: Dict[str, float] = {node: float("inf") for node in self.node_coordinates}
        previous: Dict[str, str] = {}
        distances[start_node] = 0.0

        pq: List[Tuple[float, str]] = [(0.0, start_node)]

        # Dijkstra's algorithm main loop
        while pq:
            current_dist, u = heapq.heappop(pq)
            # If the current distance is greater than the recorded distance, skip processing this node
            if current_dist > distances[u]:
                continue

            if u == end_node:
                break
            # Explore neighbors of the current node
            for v, weight in self.adjacency_list[u]:
                alt = current_dist + weight
                if alt < distances[v]:
                    distances[v] = alt
                    previous[v] = u
                    heapq.heappush(pq, (alt, v))

        if distances[end_node] == float("inf"):
            return None, float("inf")

        # Reconstruct path from start_node to end_node
        path = []
        curr = end_node
        # Backtrack from the end node to the start node using the previous dictionary
        while curr in previous:
            # Append the current node to the path and move to the previous node
            path.append(curr)
            curr = previous[curr]
        path.append(start_node)
        path.reverse()

        return path, distances[end_node]