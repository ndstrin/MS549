import argparse
import heapq
import math
import os
import random
from itertools import count
from typing import Dict, List, Optional, Any

import matplotlib.pyplot as plt

# Import modular components
from car import Car
from rider import Rider
from Tools.quadtree import Quadtree, Rectangle, Point
from Tools.graph import Graph

# Constants for simulation configuration
num_cars = 20
num_riders = 30
graph_file = "Data/graph_xy.csv"
seed = 42
max_time = 100.0
candidate_count = 5

class Simulation:
    # Represents the discrete-event ride-share simulation environment, managing cars, riders, and events.
    def __init__(
        self,
        graph: Graph,
        candidate_count: int = candidate_count,
        max_time: Optional[float] = None,
        num_riders: Optional[int] = None,
        map_bounds: Optional[Rectangle] = None,
                         
    ):
        # Initializes the simulation with the provided graph, candidate count, maximum time, and rider limit.
        self.graph = graph
        self.candidate_count = candidate_count
        self.max_time = max_time
        self.num_riders_limit = num_riders
        self.current_time = 0.0

        # Dynamically compute Quadtree boundary from graph nodes if map_bounds is not provided
        if map_bounds is None:
            xs = [coord[0] for coord in self.graph.node_coordinates.values()]
            ys = [coord[1] for coord in self.graph.node_coordinates.values()]
            PAD = 100.0  # Generous padding buffer around map extremes

            boundary = Rectangle(
                xmin=min(xs) - PAD,
                ymin=min(ys) - PAD,
                xmax=max(xs) + PAD,
                ymax=max(ys) + PAD
            )
        else:
            boundary = map_bounds

        # Event Queue and Sequence Tracking
        self.event_sequence = count()
        self.events: List[tuple] = []

        # Available Car Index Structures
        self.available_cars: Dict[str, Car] = {}
        self.available_car_points: Dict[str, Point] = {}
        self.available_car_quadtree = Quadtree(boundary)
        # Global Registries & Tracking
        self.all_cars: Dict[str, Car] = {}
        self.all_riders: List[Rider] = []
        self.riders_generated_count = 0
        self.completed_riders: List[Rider] = []
        self.unmatched_riders: List[Rider] = []

    def schedule_event(self, timestamp: float, event_type: str, data: Any) -> None:
        # Schedules an event in the priority queue with a unique sequence number to maintain order for simultaneous events.
        heapq.heappush(
            self.events,
            (timestamp, next(self.event_sequence), event_type, data)
        )

    def add_available_car(self, car: Car) -> None:
        # Adds a car to the availability registries and Quadtree index, ensuring no duplicates.
        if car.id in self.available_cars or car.id in self.available_car_points:
            raise ValueError(f"Car {car.id} is already registered as available.")

        pt = Point(car.location[0], car.location[1], data=car)
        inserted = self.available_car_quadtree.insert(pt)

        if not inserted:
            raise ValueError(f"Failed to insert Car {car.id} into Quadtree bounds.")

        self.available_cars[car.id] = car
        self.available_car_points[car.id] = pt
        car.status = "available"

    def remove_available_car(self, car: Car) -> None:
        # Removes car from availability registries and Quadtree index by exact Point identity.
        if car.id not in self.available_car_points:
            raise KeyError(f"Car {car.id} not found in available car tracking.")

        pt = self.available_car_points[car.id]
        removed = self.available_car_quadtree.remove(pt)

        if not removed:
            raise RuntimeError(f"Quadtree failed to remove exact Point object for Car {car.id}.")

        del self.available_car_points[car.id]
        del self.available_cars[car.id]

    def generate_rider_request(self) -> None:
        # Generates dynamic random rider requests up to configured limits.
        if self.num_riders_limit is not None and self.riders_generated_count >= self.num_riders_limit:
            return

        self.riders_generated_count += 1
        r_id = f"R{self.riders_generated_count}"
        # Randomly select start and destination locations from graph nodes, ensuring they are distinct.
        nodes = list(self.graph.node_coordinates.values())
        start_loc = random.choice(nodes)
        dest_loc = random.choice(nodes)
        while dest_loc == start_loc:
            dest_loc = random.choice(nodes)

        rider = Rider(r_id, start_loc, dest_loc)
        self.all_riders.append(rider)

        if self.riders_generated_count == 1:
            req_time = 0.0
        else:
            req_time = self.current_time + random.expovariate(1.0 / 5.0)

        if self.max_time is not None and req_time > self.max_time:
            return

        self.schedule_event(req_time, "RIDER_REQUEST", rider)

    def handle_rider_request(self, rider: Rider) -> None:
        # Handles a rider request event by finding the nearest available car and scheduling pickup.
        if rider.request_time is None:
            rider.request_time = self.current_time

        print(f"[{self.current_time:.2f}] RIDER_REQUEST: {rider.id} at {rider.start_location} -> {rider.destination}")

        # Schedule next request before processing
        self.generate_rider_request()

        query_pt = Point(rider.start_location[0], rider.start_location[1])
        candidate_points = self.available_car_quadtree.find_k_nearest(query_pt, k=self.candidate_count)

        if not candidate_points:
            print(f"  -> No available cars for {rider.id}.")
            rider.status = "unmatched"
            self.unmatched_riders.append(rider)
            return

        # Dijkstra calculation over Quadtree candidates
        rider_vertex = self.graph.find_nearest_vertex(rider.start_location)
        best_car = None
        best_route = None
        min_travel_time = float("inf")

        # Evaluate each candidate car for shortest travel time to rider
        for pt in candidate_points:
            car: Car = pt.data
            car_vertex = self.graph.find_nearest_vertex(car.location)
            route, travel_time = self.graph.dijkstra(car_vertex, rider_vertex)

            if route is not None and travel_time < min_travel_time:
                min_travel_time = travel_time
                best_car = car
                best_route = route

        # If no reachable car was found, mark rider as unmatched
        if best_car is None:
            print(f"  -> All candidates unreachable for {rider.id}.")
            rider.status = "unmatched"
            self.unmatched_riders.append(rider)
            return

        # Dispatch selected car
        self.remove_available_car(best_car)
        best_car.status = "en_route_to_pickup"
        best_car.assigned_rider = rider
        best_car.route = best_route
        best_car.route_time = min_travel_time
        best_car.busy_start_time = self.current_time
        rider.status = "waiting"

        # Schedule pickup arrival event based on calculated travel time
        pickup_arrival_time = self.current_time + min_travel_time
        self.schedule_event(pickup_arrival_time, "PICKUP_ARRIVAL", best_car)
        print(f"  -> Assigned Car {best_car.id} (ETA: {min_travel_time:.2f} units)")

    def handle_pickup_arrival(self, car: Car) -> None:
        # Handles the pickup arrival event, updating car and rider statuses, and scheduling dropoff.
        rider = car.assigned_rider
        if not rider:
            return

        print(f"[{self.current_time:.2f}] PICKUP_ARRIVAL: Car {car.id} picked up Rider {rider.id}")
        car.location = rider.start_location
        car.status = "en_route_to_destination"
        rider.status = "in_car"
        rider.pickup_time = self.current_time

        p_vertex = self.graph.find_nearest_vertex(rider.start_location)
        d_vertex = self.graph.find_nearest_vertex(rider.destination)
        trip_route, trip_time = self.graph.dijkstra(p_vertex, d_vertex)

        # If the trip route is unreachable, mark the rider as unsuccessful and return the car to availability.
        if trip_route is None or math.isinf(trip_time):
            print(f"  -> Destination unreachable! Recovering Car {car.id}.")
            rider.status = "unsuccessful"
            self.unmatched_riders.append(rider)

            if car.busy_start_time is not None:
                car.total_busy_time += (self.current_time - car.busy_start_time)
            car.assigned_rider = None
            self.add_available_car(car)
            return
        # Schedule dropoff arrival event based on calculated trip time
        car.route = trip_route
        car.route_time = trip_time
        dropoff_time = self.current_time + trip_time
        self.schedule_event(dropoff_time, "DROPOFF_ARRIVAL", car)

    def handle_dropoff_arrival(self, car: Car) -> None:
        # Handles the dropoff arrival event, updating car and rider statuses, and returning the car to availability.
        rider = car.assigned_rider
        if not rider:
            return

        print(f"[{self.current_time:.2f}] DROPOFF_ARRIVAL: Car {car.id} dropped off Rider {rider.id}")
        car.location = rider.destination
        rider.status = "completed"
        rider.dropoff_time = self.current_time

        # Update car's busy time and trip count
        if car.busy_start_time is not None:
            car.total_busy_time += (self.current_time - car.busy_start_time)
        car.trips_completed += 1
        car.assigned_rider = None

        self.completed_riders.append(rider)
        self.add_available_car(car)

    def run(self) -> None:
            # Executes the simulation loop, processing events in chronological order until all events are handled.
        print("=== SIMULATION STARTED ===")
        self.generate_rider_request()

        # Process events in chronological order
        while self.events:
            timestamp, seq, event_type, data = heapq.heappop(self.events)
            self.current_time = timestamp

            # Dispatch event to appropriate handler based on event type
            if event_type == "RIDER_REQUEST":
                self.handle_rider_request(data)
            elif event_type == "PICKUP_ARRIVAL":
                self.handle_pickup_arrival(data)
            elif event_type == "DROPOFF_ARRIVAL":
                self.handle_dropoff_arrival(data)
            else:
                raise ValueError(f"Unknown event type: {event_type}")

        print("=== SIMULATION COMPLETED ===")


def render_analytical_summary(sim: Simulation, output_filename: str = "simulation_summary.png") -> None:
   # Generates a visual summary of the simulation, including the city road map with car positions and a bar chart of completed trips per vehicle.
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    ax_map = axes[0]
    ax_map.set_title("City Road Map & Final Fleet Spatial Positions")
    # Draw the road map edges based on the graph's adjacency list
    for u, neighbors in sim.graph.adjacency_list.items():
        ux, uy = sim.graph.node_coordinates[u]
        for v, _ in neighbors:
            vx, vy = sim.graph.node_coordinates[v]
            ax_map.plot([ux, vx], [uy, vy], color="#cccccc", linewidth=1, zorder=1)
    # Plot the final positions of all cars, color-coded by availability status
    for car in sim.all_cars.values():
        cx, cy = car.location
        ax_map.scatter(cx, cy, color="blue" if car.status == "available" else "red", s=50, zorder=3)
        ax_map.annotate(car.id, (cx, cy), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=8)
    # Set axis limits and labels for the map
    ax_map.set_xlabel("X Coordinate")
    ax_map.set_ylabel("Y Coordinate")
    # Set axis limits based on the graph's node coordinates
    ax_chart = axes[1]
    car_ids = list(sim.all_cars.keys())
    trips = [sim.all_cars[cid].trips_completed for cid in car_ids]
    # Create a bar chart showing the number of completed trips per vehicle
    ax_chart.bar(car_ids, trips, color="#2b5c8f")
    ax_chart.set_title("Completed Trips per Vehicle")
    ax_chart.set_xlabel("Car ID")
    ax_chart.set_ylabel("Trips Completed")
    # Add a grid for better readability
    total_riders = sim.riders_generated_count
    completed_count = len(sim.completed_riders)
    unmatched_count = len(sim.unmatched_riders)
    # Calculate average wait time for riders who were successfully picked up
    wait_times = [(r.pickup_time - r.request_time) for r in sim.completed_riders if r.pickup_time and r.request_time]
    avg_wait = (sum(wait_times) / len(wait_times)) if wait_times else 0.0
    # Calculate driver utilization as a percentage of time spent busy versus total simulation time
    span = sim.current_time if sim.current_time > 0 else 1.0
    total_busy = sum(car.total_busy_time for car in sim.all_cars.values())
    driver_utilization = (total_busy / (len(sim.all_cars) * span)) * 100 if sim.all_cars else 0.0
    # Prepare a summary text block with key metrics for display on the chart
    metrics_text = (
        f"--- METRICS SUMMARY ---\n"
        f"Span: {span:.2f} time units\n"
        f"Total Riders: {total_riders}\n"
        f"Completed Trips: {completed_count}\n"
        f"Unmatched/Failed: {unmatched_count}\n"
        f"Avg Wait Time: {avg_wait:.2f} units\n"
        f"Driver Utilization: {driver_utilization:.1f}%"
    )
    # Add the metrics summary text to the figure with a styled bounding box 
    fig.text(
        0.51, 0.55, metrics_text, fontsize=11, family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f4f4f4", edgecolor="#aaaaaa")
    )

    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    print(f"Saved summary chart to: {os.path.abspath(output_filename)}")



def main() -> None:

    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Discrete-Event Ride-Share Simulation Engine")
    parser.add_argument("--num-cars", type=int, default=num_cars, help="Total fleet vehicle count")
    parser.add_argument("--num-riders", type=int, default=num_riders, help="Maximum number of riders to generate")
    parser.add_argument("--candidate-count", type=int, default=candidate_count, help="Quadtree k-nearest candidate pool size")
    parser.add_argument("--graph-file", type=str, default=graph_file, help="Path to CSV road map dataset")
    parser.add_argument("--max-time", type=float, default=max_time, help="Maximum simulation time cutoff")
    parser.add_argument("--seed", type=int, default=seed, help="Seed for pseudorandom reproducibility")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Set the random seed for reproducibility and load the graph data from the specified file
    random.seed(args.seed)
    graph = Graph()
    graph.load_map_data(args.graph_file)
    # Initialize the simulation with the loaded graph and specified parameters
    sim = Simulation(
        graph=graph,
        candidate_count=args.candidate_count,
        max_time=args.max_time,
        num_riders=args.num_riders,
    )
    # Create and register cars with random initial locations from the graph's node coordinates
    node_coords = list(graph.node_coordinates.values())
    for idx in range(1, args.num_cars + 1):
        c_id = f"C{idx}"
        init_loc = random.choice(node_coords)
        car = Car(c_id, init_loc)
        sim.all_cars[c_id] = car
        sim.add_available_car(car)
    # Run the simulation and render the analytical summary upon completion
    sim.run()
    render_analytical_summary(sim)


if __name__ == "__main__":
    main()