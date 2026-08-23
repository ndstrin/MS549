import argparse
import heapq
import math
import os
import random
import sys  
from itertools import count
from tracemalloc import Snapshot
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
snapshot_interval = 15.0  # Time units between periodic snapshots


class LogConsole:
    # Redirects console output to both a log file and the standard output for real-time monitoring.
    def __init__(self, filename):
        self.file = open(filename, "w", encoding="utf-8")
        self.stdout = sys.stdout
    # Overrides the write method to send output to both the log file and standard output.
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data) 
    # Overrides the flush method to ensure both the log file and standard output are flushed.
    def flush(self):
        self.file.flush()
        self.stdout.flush()


class Simulation:
    # Represents the discrete-event ride-share simulation environment, managing cars, riders, and events.
    def __init__(
        self,
        graph: Graph,
        candidate_count: int = candidate_count,
        max_time: Optional[float] = None,
        num_riders: Optional[int] = None,
        map_bounds: Optional[Rectangle] = None,
        snapshot_interval: float = snapshot_interval
                         
    ):
        # Initializes the simulation with the provided graph, candidate count, maximum time, and rider limit.
        self.graph = graph
        self.candidate_count = candidate_count
        self.max_time = max_time
        self.num_riders_limit = num_riders
        self.current_time = 0.0
        # Initialize snapshot tracking for periodic spatial state recording
        self.snapshots: List[Dict[str, Any]] = []
        self.snapshot_interval: float = snapshot_interval
        self.last_snapshot_time: float = -snapshot_interval # Initialize to ensure the first snapshot is captured at time 0

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

    def capture_snapshot(self, event_label: str) -> None:
        # Records a snapshot of the current simulation state, including the positions and statuses of all cars and active riders.
        car_data = [(car.id, car.location, car.status) for car in self.all_cars.values()]
        rider_data = [
            (r.id, r.start_location, r.destination, r.status) 
            for r in self.all_riders 
            if r.status in ("waiting", "in_car")
        ]
        self.snapshots.append({
            "time": self.current_time,
            "event": event_label,
            "cars": car_data,
            "riders": rider_data
        })

    def add_available_car(self, car: Car) -> None:
        # Adds a car to the availability registries and Quadtree index, ensuring no duplicates.
        if car.id in self.available_cars or car.id in self.available_car_points:
            raise ValueError(f"Car {car.id} is already registered as available.")

        pt = Point(car.location[0], car.location[1], data=car)
        inserted = self.available_car_quadtree.insert(pt)
        # If insertion fails, raise an error indicating the car could not be added to the Quadtree.
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
        if self.num_riders_limit is not None and self.riders_generated_count >= self.num_riders_limit:
            return

        # Calculate proposed arrival time
        if self.riders_generated_count == 0:
            req_time = 0.0
        else:
            req_time = self.current_time + random.expovariate(1.0 / 5.0)

        # Increment the rider count and generate a unique rider ID
        self.riders_generated_count += 1
        r_id = f"R{self.riders_generated_count}"
        nodes = list(self.graph.node_coordinates.values())
        start_loc = random.choice(nodes)
        dest_loc = random.choice(nodes)
        while dest_loc == start_loc:
            dest_loc = random.choice(nodes)

        rider = Rider(r_id, start_loc, dest_loc)
        rider.request_time = req_time
        self.all_riders.append(rider)

        # Check if the request time exceeds the maximum allowed time for rider requests
        if self.max_time is not None and req_time > self.max_time:
            rider.status = "unmatched"
            if rider not in self.unmatched_riders:
                self.unmatched_riders.append(rider)
            print(f"[{req_time:.2f}] RIDER_REQUEST_EXCEEDED_MAX_TIME: {rider.id} rejected (exceeds max_time={self.max_time})")
            # Generate the next rider request
            self.generate_rider_request()
            return

        # Schedule event in heap only if within max_time window
        self.schedule_event(req_time, "RIDER_REQUEST", rider)

    def handle_rider_request(self, rider: Rider) -> None:
        # Handles a rider request event by finding the nearest available car, assigning it, and scheduling the pickup arrival.
        if rider.request_time is None:
            rider.request_time = self.current_time

        print(f"[{self.current_time:.2f}] RIDER_REQUEST: {rider.id} at {rider.start_location} -> {rider.destination}")

        self.generate_rider_request()

        query_pt = Point(rider.start_location[0], rider.start_location[1])
        candidate_points = self.available_car_quadtree.find_k_nearest(query_pt, k=self.candidate_count)

        if not candidate_points:
            print(f"  -> No available cars for {rider.id}.")
            rider.status = "unmatched"
            if rider not in self.unmatched_riders:
                self.unmatched_riders.append(rider)
            return

        # Find the best car among candidates based on shortest travel time using Dijkstra's algorithm
        rider_vertex = self.graph.find_nearest_vertex(rider.start_location)
        best_car = None
        best_route = None
        min_travel_time = float("inf")
        # Iterate through candidate cars to find the one with the shortest travel time to the rider's location
        for pt in candidate_points:
            car: Car = pt.data
            car_vertex = self.graph.find_nearest_vertex(car.location)
            route, travel_time = self.graph.dijkstra(car_vertex, rider_vertex)

            if route is not None and travel_time < min_travel_time:
                min_travel_time = travel_time
                best_car = car
                best_route = route
        # If no reachable car is found, mark the rider as unmatched and return
        if best_car is None:
            print(f"  -> All candidates unreachable for {rider.id}.")
            rider.status = "unmatched"
            if rider not in self.unmatched_riders:
                self.unmatched_riders.append(rider)
            return

        # Single dispatch execution
        self.remove_available_car(best_car)
        best_car.status = "en_route_to_pickup"
        best_car.assigned_rider = rider
        best_car.route = best_route
        best_car.route_time = min_travel_time
        best_car.busy_start_time = self.current_time
        rider.status = "waiting"

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

        # Compute the route and travel time from pickup to dropoff using Dijkstra's algorithm
        s_vertex = self.graph.find_nearest_vertex(rider.start_location)
        d_vertex = self.graph.find_nearest_vertex(rider.destination)
        trip_route, trip_time = self.graph.dijkstra(s_vertex, d_vertex)
        # If the trip route is None or the trip time is infinite, mark the rider as unsuccessful and return the car to availability
        if trip_route is None or math.isinf(trip_time):
            print(f"  -> Destination unreachable! Recovering Car {car.id}.")
            rider.status = "unsuccessful"
            if rider not in self.unmatched_riders:
                self.unmatched_riders.append(rider)

            if car.busy_start_time is not None:
                car.total_busy_time += (self.current_time - car.busy_start_time)
                car.busy_start_time = None
            car.assigned_rider = None
            self.add_available_car(car)
            return
        # Update car's route and schedule dropoff arrival event
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

            if self.current_time - self.last_snapshot_time >= self.snapshot_interval:
                self.capture_snapshot(event_type)
                self.last_snapshot_time = self.current_time

        # Finalize busy time for any cars still in transit at the end of the simulation
        for car in self.all_cars.values():
            if car.status != "available" and car.busy_start_time is not None:
                car.total_busy_time += (self.current_time - car.busy_start_time)
                car.busy_start_time = None

        # Finalize unmatched riders after all events are processed
        for rider in self.all_riders:
            if rider.status in ("unassigned", "waiting", "unmatched", "unsuccessful") and rider not in self.unmatched_riders:
                rider.status = "unmatched"
                self.unmatched_riders.append(rider)


        print("\n============== SIMULATION COMPLETED ============== ")


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
    total_riders = len(sim.all_riders)
    completed_count = len(sim.completed_riders)
    unmatched_count = len(sim.unmatched_riders)
    # Calculate average wait time for riders who were successfully picked up
    wait_times = [(r.pickup_time - r.request_time) for r in sim.completed_riders if r.pickup_time is not None and r.request_time is not None]
    avg_wait = (sum(wait_times) / len(wait_times)) if wait_times else 0.0
    # Calculate average trip duration for completed trips
    trip_durations = [(r.dropoff_time - r.pickup_time) for r in sim.completed_riders if r.dropoff_time is not None and r.pickup_time is not None]
    avg_trip_duration = (sum(trip_durations) / len(trip_durations)) if trip_durations else 0.0
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
        f"Avg Trip Duration: {avg_trip_duration:.2f} units\n"
        f"Driver Utilization: {driver_utilization:.1f}%"
    )
    print(metrics_text)
    # Add the metrics summary text to the figure with a styled bounding box 
    fig.text(
        0.51, 0.55, metrics_text, fontsize=11, family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f4f4f4", edgecolor="#aaaaaa")
    )

    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    print("\n============== File Outputs ==============")
    print(f"Saved summary chart to: {output_filename}")

def render_time_step_snapshots(
    snapshots: List[Dict[str, Any]], 
    graph: Any, 
    output_filename: str = "simulation_time_steps.png"
) -> None:
     # Generates a grid of time-step snapshots visualizing the positions of cars and riders at various simulation events
    if not snapshots:
        print("No snapshots recorded to render.")
        return

    num_snapshots = len(snapshots)
    cols = min(3, num_snapshots)
    rows = math.ceil(num_snapshots / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4.5 * rows))
    
    # Standardize axes array for uniform iteration
    if rows == 1 and cols == 1:
        axes_flat = [axes]
    elif rows == 1 or cols == 1:
        axes_flat = list(axes)
    else:
        axes_flat = [ax for row in axes for ax in row]

    # Pre-extract road network edge geometry
    edges = []
    for u, neighbors in graph.adjacency_list.items():
        ux, uy = graph.node_coordinates[u]
        for v, _ in neighbors:
            vx, vy = graph.node_coordinates[v]
            edges.append(((ux, vx), (uy, vy)))
    # Iterate through each snapshot and render the corresponding spatial positions of cars and riders
    for i, snap in enumerate(snapshots):
        ax = axes_flat[i]
        t = snap["time"]
        event_name = snap["event"]

        # 1. Draw city road network background
        for x_coords, y_coords in edges:
            ax.plot(x_coords, y_coords, color="#e0e0e0", linewidth=0.8, zorder=1)

        # 2. Draw Available Cars (Blue) & Busy/En-Route Cars (Red)
        for c_id, (cx, cy), status in snap["cars"]:
            color = "#2b5c8f" if status == "available" else "#d9534f"
            ax.scatter(cx, cy, color=color, s=40, zorder=3)
            ax.annotate(c_id, (cx, cy), textcoords="offset points", xytext=(0, 4), ha="center", fontsize=7)

        # 3. Draw Waiting/Active Riders (Green triangles) & Destinations (Purple crosses)
        for r_id, (rx, ry), (dx, dy), status in snap["riders"]:
            if status in ("waiting", "in_car"):
                ax.scatter(rx, ry, color="#2e7d32", marker="^", s=45, zorder=4)
                ax.scatter(dx, dy, color="#7b1fa2", marker="x", s=40, zorder=2)

        # Set axis limits based on graph node coordinates with padding
        ax.set_title(f"t = {t:.1f} ({event_name})", fontsize=10, fontweight="bold")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(True, linestyle=":", alpha=0.4)

    # Hide unused subplots in the grid
    for j in range(num_snapshots, len(axes_flat)):
        axes_flat[j].axis("off")
    # Set a super title for the entire figure and adjust layout
    plt.suptitle("Ride-Share Fleet & Rider Positions Across Simulation Time Steps", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches="tight")
    print(f"Saved time-step snapshots to: {output_filename}")

def print_simulation_settings(args: argparse.Namespace) -> None:
    """Prints a formatted summary of runtime configuration settings."""
    print("=" * 50)
    print("          SIMULATION CONFIGURATION SETTINGS       ")
    print("=" * 50)
    print(f"  Total Vehicles      (--num-cars)          : {args.num_cars}")
    print(f"  Total Riders        (--num-riders)        : {args.num_riders}")
    print(f"  Candidate Count     (--candidate-count)   : {args.candidate_count}")
    print(f"  Max Simulation Time (--max-time)          : {args.max_time} time units")
    print(f"  Snapshot Interval   (--snapshot-int)      : {args.snapshot_interval} time units")
    print(f"  Graph Dataset       (--graph-file)        : {args.graph_file}")
    print(f"  Seed                (--seed)              : {args.seed}")
    print("=" * 50 + "\n")


def main() -> None:

    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Discrete-Event Ride-Share Simulation Engine")
    parser.add_argument("--num-cars", type=int, default=num_cars, help="Total fleet vehicle count")
    parser.add_argument("--num-riders", type=int, default=num_riders, help="Maximum number of riders to generate")
    parser.add_argument("--candidate-count", type=int, default=candidate_count, help="Quadtree k-nearest candidate pool size")
    parser.add_argument("--graph-file", type=str, default=graph_file, help="Path to CSV road map dataset")
    parser.add_argument("--max-time", type=float, default=max_time, help="Maximum simulation time cutoff")
    parser.add_argument("--seed", type=int, default=seed, help="Seed for pseudorandom reproducibility")
    parser.add_argument("--snapshot-interval", type=float, default=snapshot_interval, help="Time units between periodic snapshots")

    # Parse the command-line arguments
    args = parser.parse_args()
    # Redirect console output to a log file while still displaying it in the terminal
    sys.stdout = LogConsole("simulation.log")

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
        snapshot_interval=args.snapshot_interval    
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
    print_simulation_settings(args)
    render_analytical_summary(sim)
    # Render time-step snapshots to visualize the evolution of the simulation over time
    render_time_step_snapshots(sim.snapshots, graph, output_filename="simulation_time_steps.png")
    print("Simulation completed. Check 'simulation.log' for detailed simulation logs.")


if __name__ == "__main__":
    main()