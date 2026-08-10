import csv


class Graph:
    # Initializes an empty graph with an adjacency list representation.

    def __init__(self):
        self.adjacency_list = {}

   # Adds a directed edge from start_node to end_node with the given weight.
    def add_edge(self, start_node, end_node, weight):
        if start_node not in self.adjacency_list:
            self.adjacency_list[start_node] = []
        if end_node not in self.adjacency_list:
            self.adjacency_list[end_node] = []

        self.adjacency_list[start_node].append((end_node, float(weight)))
    # Loads graph data from a CSV file and populates the adjacency list.
    def load_from_file(self, filename):
        with open(filename, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                start = row["start_node"].strip()
                end = row["end_node"].strip()
                weight = float(row["travel_time"])
                self.add_edge(start, end, weight)

    # Returns a string representation of the graph's adjacency list for easy visualization.
    def __str__(self):
        lines = ["Graph Adjacency List:"]
        for node, neighbors in self.adjacency_list.items():
            neighbor_str = ", ".join(
                [f"{nbr} (weight: {w})" for nbr, w in neighbors]
            )
            lines.append(f"  {node} -> [{neighbor_str}]")
        return "\n".join(lines)


# Example usage of the Graph class
if __name__ == "__main__":
    graph = Graph()
    graph.load_from_file("Data\\graph_xy.csv")
    print(graph)