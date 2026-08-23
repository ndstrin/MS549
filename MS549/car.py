# Car Class 

from ast import List
from typing import List, Tuple, Optional, TYPE_CHECKING
from Tools.pathfinding import find_shortest_path
from rider import Rider

TRAVEL_SPEED_FACTOR = 0.05  # Time units per distance unit

class Car:
     # Constructor to initialize the car with an ID and initial location
    def __init__(self, car_id: str, location: Tuple[float, float]):
        self.id: str = car_id
        self.location: Tuple[float, float] = location
        self.status: str = "available"  # Options: 'available', 'en_route_to_pickup', 'en_route_to_destination'
        self.assigned_rider: Optional['Rider'] = None
        self.route: List[str] = []
        self.route_time: float = 0.0
        self.busy_start_time: Optional[float] = None
        self.total_busy_time: float = 0.0
        self.trips_completed: int = 0

    def __repr__(self) -> str:
        return f"Car({self.id}, loc={self.location}, status={self.status})"

    # Function to calculate the shortest route to a destination using Dijkstra's algorithm
    def calculate_route(self, destination: Tuple[float, float], graph: Any) -> Tuple[List[str], float]:

        # Map 2D spatial coordinates (x, y) to graph node string IDs
        start_vertex = graph.find_nearest_vertex(self.location)
        dest_vertex = graph.find_nearest_vertex(destination)

        # Execute Dijkstra's pathfinding using graph node IDs
        path, travel_time = graph.dijkstra(start_vertex, dest_vertex)

        # Update instance properties
        self.route = path if path is not None else []
        self.route_time = travel_time if travel_time is not None else float("inf")
        self.destination = destination

        return self.route, self.route_time

    # Function to calculate the travel time to a given end location based on Manhattan distance
    def calculate_travel_time(self, end_location: tuple[float, float]) -> float:
        x1, y1 = self.location
        x2, y2 = end_location
        distance = abs(x1 - x2) + abs(y1 - y2)
        return distance * TRAVEL_SPEED_FACTOR




