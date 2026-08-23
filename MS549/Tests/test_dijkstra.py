from car import Car
from Tools.graph import Graph
from Tools.pathfinding import find_shortest_path

# Test cases for the Dijkstra's algorithm and Car class integration
def test_dijkstra_integration():
    
    # Load the graph from the CSV file
    graph = Graph()
    graph.load_map_data("Data\\graph_xy.csv")

    print("Dijkstra's Algorithm Test:")
    
    # Test Shortest path from (50, 50) to (75, 25)
    start = (50, 50)
    end = (75, 25)
    start_node = graph.find_nearest_vertex(start)
    end_node = graph.find_nearest_vertex(end)

    path, travel_time = find_shortest_path(graph, start_node, end_node)
    print(f"Shortest path from '{start}' to '{end}':")
    print(f"  Path: {path}")
    print(f"  Total Time: {travel_time}\n")
    
    # Setup car object 
    print("Creating Car Object:")
    car1 = Car(car_id=100, location=start)

    # Calculate route to Park Ave
    car1.calculate_route(destination=end, graph=graph)

    # Verify car object state
    print(f"Car {car1.id} stored route: {car1.route}")
    print(f"Car {car1.id} stored route time: {car1.route_time}")


if __name__ == "__main__":
    test_dijkstra_integration()


