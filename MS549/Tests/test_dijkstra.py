from car import Car
from Tools.graph import Graph
from Tools.pathfinding import find_shortest_path

## Test cases for the Dijkstra's algorithm and Car class integration
def test_dijkstra_integration():
    
    ## Load the graph from the CSV file
    graph = Graph()
    graph.load_from_file("Data\\map.csv")

    print("Dijkstra's Algorithm Test:")
    # Find the shortest path from Pine St to Park Ave
    start = "Pine St"
    end = "Park Ave"

    path, travel_time = find_shortest_path(graph, start, end)
    print(f"Shortest path from '{start}' to '{end}':")
    print(f"  Path: {path}")
    print(f"  Total Time: {travel_time}\n")
    
    # Setup car object 
    print("Creating Car Object:")
    car1 = Car(car_id=100, driver_name="Alice", initial_location=start)

    # Calculate route to Park Ave
    car1.calculate_route(destination=end, graph=graph)

    # Verify car object state
    print(f"Car {car1.id} stored route: {car1.route}")
    print(f"Car {car1.id} stored route time: {car1.route_time}")
    print("\nCar Info display:")
    car1.display_info()


if __name__ == "__main__":
    test_dijkstra_integration()


