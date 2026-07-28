import csv

class Graph:
    pass
    # Initializes the graph with an empty adjacency list.
    def __init__(self):
            self.adjacency_list = {}
    # Adds a directed edge to the graph with a specified weight.
    def add_edge(self, start_node, end_node, weight):
           
            if start_node not in self.adjacency_list:
                # If the start node is not in the adjacency list, initialize it with an empty list.
                self.adjacency_list[start_node] = []
            # If the end node is not in the adjacency list, initialize it with an empty list.
            self.adjacency_list[start_node].append((end_node, float(weight)))
    # Reads the graph data from a CSV file and populates the adjacency list.
    def load_from_file(self, filename):
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                start = row['start_node'].strip()
                end = row['end_node'].strip()
                weight = float(row['travel_time'])
                self.add_edge(start, end, weight)
    # Returns a formatted string representation of the adjacency list.
    def __str__(self):
        lines = ["Graph Adjacency List:"]
        for node, neighbors in self.adjacency_list.items():
            # Create String of the Neighbors and their weights for each node in the adjacency list
            neighbor_str = ", ".join([f"{nbr} (weight: {w})" for nbr, w in neighbors])
            # Adds the Node with the Neighbor String to the Lins list 
            lines.append(f"  {node} -> [{neighbor_str}]")
            # Returns the Output to the the lines list as a String with new lines between each line
        return "\n".join(lines)

# Example usage of the Graph class
if __name__ == "__main__":
    graph = Graph()
    graph.load_from_file("map.csv")
    print(graph)


