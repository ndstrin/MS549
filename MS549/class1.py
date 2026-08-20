import argparse
import heapq
import math
import random
from itertools import count

import matplotlib.pyplot as plt

from car import Car
from rider import Rider
# Import quadtree & graph tools from your project structure
from Tools.graph import Graph
from Tools.pathfinding import find_nearest_vertex
from Tools.quadtree import Point, Quadtree, Rect


FIRST_NAMES = [
    "Alex", "Aria", "Ben", "Carlos", "Diana", "Ethan", "Fiona", 
    "Gabe", "Hannah", "Ian", "Julia", "Kevin", "Laura", "Marcus", 
    "Nina", "Omar", "Paula", "Quinn", "Rachel", "Sam"
]

class Simulation:
    """Central discrete-event simulation engine for ride-sharing dispatch."""

    def __init__(
        self,
        city_map_file: str = "Data\\graph_xy.csv",
        max_time: float = 1000.0,
        num_riders: int = 50,
        num_cars: int = 100,
        candidate_count: int = 5,
        seed: int = 42,
    ):
        random.seed(seed)
        self.max_time = max_time
        self.max_riders = num_riders
        self.candidate_count = candidate_count
        self.current_time = 0.0

        # Deterministic event heap setup
        self.event_queue = []
        self.event_sequence = count()

        # Load Map & Graph Topology
        self.graph = Graph()
        self.graph.load_map_data(city_map_file)

        # Build Quadtree Bounding Box based on Graph Coordinates
        xs = [coord[0] for coord in self.graph.node_coordinates.values()]
        ys = [coord[1] for coord in self.graph.node_coordinates.values()]
        PAD = 50.0  
        boundary = Rect(
            xmin=min(xs) - PAD, 
            ymin=min(ys) - PAD, 
            xmax=max(xs) + PAD, 
            ymax=max(ys) + PAD
        )

        # Centralized Availability Structures
        self.available_cars = {}
        self.available_car_points = {}
        self.available_car_quadtree = Quadtree(boundary)

        # Metrics Tracking
        self.all_cars = []
        self.all_riders = []
        self.unmatched_riders = []
        self.completed_riders = []
        self.riders_generated_count = 0

        # Initialize Car Fleet
        nodes = list(self.graph.node_coordinates.keys())
        for i in range(num_cars):
            start_node = random.choice(nodes)
            loc = self.graph.node_coordinates[start_node]
            driver_name = f"{random.choice(FIRST_NAMES)} {chr(65 + (i % 26))}."
            car = Car(car_id=i+1, initial_location=loc, driver_name=driver_name)
            self.all_cars.append(car)
            self.add_available_car(car)

    # --- Centralized Availability Invariants ---

    def add_available_car(self, car: Car) -> None:
        """Adds a car to Quadtree and availability dicts. Sets status to available."""
        car_key = str(car.id)
        if car_key in self.available_cars or car_key in self.available_car_points:
            raise RuntimeError(f"Car {car_key} already exists in availability index.")

        pt = Point(car.location[0], car.location[1], data=car)
        if not self.available_car_quadtree.insert(pt):
            raise RuntimeError(f"Failed to insert Car {car_key} into Quadtree at {car.location}.")

        self.available_cars[car_key] = car
        self.available_car_points[car_key] = pt
        car.status = "available"

    def remove_available_car(self, car: Car) -> None:
        """Removes a car from Quadtree and availability dicts using exact Point identity."""
        car_key = str(car.id)
        if car_key not in self.available_car_points:
            raise KeyError(f"Car {car_key} not found in availability index.")

        pt = self.available_car_points[car_key]
        if not self.available_car_quadtree.remove(pt):
            raise RuntimeError(f"Quadtree removal failed for Car {car_key}.")

        del self.available_car_points[car_key]
        del self.available_cars[car_key]

    # --- Event Queue Management ---

    def schedule_event(self, timestamp: float, event_type: str, data: object) -> None:
        """Schedules a 4-field tuple: (timestamp, sequence_number, event_type, data)."""
        heapq.heappush(
            self.event_queue,
            (timestamp, next(self.event_sequence), event_type, data),
        )

    # --- Dynamic Demand Generation ---

    def generate_rider_request(self) -> None:
        """Seeds the initial dynamic rider request at time 0.0."""
        if self.riders_generated_count >= self.max_riders:
            return

        nodes = list(self.graph.node_coordinates.keys())
        s_node, d_node = random.sample(nodes, 2)
        start_loc = self.graph.node_coordinates[s_node]
        dest_loc = self.graph.node_coordinates[d_node]

        self.riders_generated_count += 1
        rider_name = f"{random.choice(FIRST_NAMES)} {chr(65 + (self.riders_generated_count % 26))}."
        
        rider = Rider(
            rider_id=f"Rider_{self.riders_generated_count}",
            pickup_location=start_loc,
            destination=dest_loc,
            name=rider_name
        )
        self.all_riders.append(rider)
        
        # Schedule first RIDER_REQUEST event at time 0.0
        self.schedule_event(self.current_time, "RIDER_REQUEST", rider)

    # --- Event Handlers ---

    def handle_rider_request(self, rider: Rider) -> None:
        """Processes rider dispatch AND dynamically schedules the next rider request."""
        if rider.request_time is None:
            rider.request_time = self.current_time

        print(f"[TIME {self.current_time:.2f}] REQUEST: {rider.name} ({rider.id}) at {rider.pickup_location}")

        # 1. Dynamically schedule next rider request into the future
        if self.riders_generated_count < self.max_riders:
            interval = random.expovariate(1.0 / 15.0)  # Mean interval = 15s
            next_time = self.current_time + interval
            
            if next_time <= self.max_time:
                nodes = list(self.graph.node_coordinates.keys())
                s_node, d_node = random.sample(nodes, 2)
                self.riders_generated_count += 1
                rider_name = f"{random.choice(FIRST_NAMES)} {chr(65 + (self.riders_generated_count % 26))}."
                
                next_rider = Rider(
                    rider_id=f"Rider_{self.riders_generated_count}",
                    pickup_location=self.graph.node_coordinates[s_node],
                    destination=self.graph.node_coordinates[d_node],
                    name=rider_name 
                )
                self.all_riders.append(next_rider)
                self.schedule_event(next_time, "RIDER_REQUEST", next_rider)

        # 2. Quadtree candidate lookup
        query_point = Point(rider.pickup_location[0], rider.pickup_location[1])
        candidate_points = self.available_car_quadtree.find_k_nearest(
            query_point, k=self.candidate_count
        )

        if not candidate_points:
            print(f"  -> UNMATCHED: No available cars in Quadtree for {rider.name}.")
            rider.status = "unmatched"
            self.unmatched_riders.append(rider)
            return

        # 3. Dijkstra pathfinding optimization
        rider_vertex = find_nearest_vertex(rider.pickup_location, self.graph.node_coordinates)
        best_car = None
        best_pickup_time = float("inf")
        best_route = None

        for pt in candidate_points:
            car = pt.data
            car_vertex = find_nearest_vertex(car.location, self.graph.node_coordinates)
            route, t_time = self.graph.dijkstra(car_vertex, rider_vertex)

            if route is not None and t_time < best_pickup_time:
                best_pickup_time = t_time
                best_car = car
                best_route = route

        if best_car is None or math.isinf(best_pickup_time):
            print(f"  -> UNMATCHED: All candidate routes unreachable for {rider.name}.")
            rider.status = "unmatched"
            self.unmatched_riders.append(rider)
            return

        # 4. Dispatch car & schedule pickup arrival
        self.remove_available_car(best_car)
        best_car.status = "en_route_to_pickup"
        best_car.assigned_rider = rider
        best_car.route = best_route
        best_car.route_time = best_pickup_time
        best_car.busy_start_time = self.current_time

        rider.status = "waiting"
        
        pickup_timestamp = self.current_time + best_pickup_time
        self.schedule_event(pickup_timestamp, "PICKUP_ARRIVAL", best_car)
        
        print(f"  -> DISPATCHED: Car {best_car.id} ({best_car.driver_name}) to {rider.name}. Pickup ETA: {pickup_timestamp:.2f}s")

    def handle_pickup_arrival(self, car: Car) -> None:
        """Handles vehicle arrival at pickup location."""
        rider = car.assigned_rider
        if rider is None:
            return

        car.location = rider.pickup_location
        car.status = "en_route_to_destination"
        rider.status = "in_car"
        rider.pickup_time = self.current_time

        wait_time = rider.pickup_time - rider.request_time
        print(f"[TIME {self.current_time:.2f}] PICKUP: Car {car.id} ({car.driver_name}) picked up {rider.name}. Wait time: {wait_time:.2f}s")

        # Calculate Dijkstra trip to passenger destination
        pickup_vertex = find_nearest_vertex(rider.pickup_location, self.graph.node_coordinates)
        dest_vertex = find_nearest_vertex(rider.destination, self.graph.node_coordinates)
        trip_route, trip_time = self.graph.dijkstra(pickup_vertex, dest_vertex)

        if trip_route is None or math.isinf(trip_time):
            # Recovery policy for unreachable destination
            print(f"  -> ABORTED: Destination unreachable for {rider.name}. Re-indexing Car {car.id}.")
            rider.status = "unmatched"
            self.unmatched_riders.append(rider)
            car.total_busy_time += self.current_time - car.busy_start_time
            car.assigned_rider = None
            self.add_available_car(car)
            return

        car.route = trip_route
        car.route_time = trip_time
        dropoff_timestamp = self.current_time + trip_time
        
        print(f"  -> TRIP STARTED: En route to {rider.destination}. Dropoff ETA: {dropoff_timestamp:.2f}s")
        self.schedule_event(dropoff_timestamp, "DROPOFF_ARRIVAL", car)

    def handle_dropoff_arrival(self, car: Car) -> None:
        """Handles vehicle arrival at passenger drop-off destination."""
        rider = car.assigned_rider
        if rider is None:
            return

        car.location = rider.destination
        rider.status = "completed"
        rider.dropoff_time = self.current_time

        trip_duration = rider.dropoff_time - rider.pickup_time
        car.total_busy_time += self.current_time - car.busy_start_time
        car.trips_completed += 1

        print(f"[TIME {self.current_time:.2f}] DROPOFF: Car {car.id} ({car.driver_name}) dropped off {rider.name} at {rider.destination}. Trip Duration: {trip_duration:.2f}s")

        car.assigned_rider = None
        self.completed_riders.append(rider)
        self.add_available_car(car)  # Reinsert into index at destination

    # --- Analytical Dashboard Visualization ---

    def generate_analytical_visualization(self, output_file: str = "simulation_summary.png") -> None:
        """Generates an integrated analytical dashboard containing map geometry and key metrics."""
        fig = plt.figure(figsize=(16, 10), dpi=300)
        grid = fig.add_gridspec(2, 2, width_ratios=[1.2, 1.0], height_ratios=[1.0, 1.0])

        # 1. Map Panel
        ax_map = fig.add_subplot(grid[:, 0])
        for u, edges in self.graph.adjacency_list.items():
            ux, uy = self.graph.node_coordinates[u]
            for v, _ in edges:
                vx, vy = self.graph.node_coordinates[v]
                ax_map.plot([ux, vx], [uy, vy], color="#cccccc", linewidth=0.8, zorder=1)

        car_xs = [c.location[0] for c in self.all_cars]
        car_ys = [c.location[1] for c in self.all_cars]
        ax_map.scatter(car_xs, car_ys, c="#1f77b4", s=35, label="Final Car Locations", zorder=2)

        ax_map.set_title("City Road Network & Final Vehicle Distribution", fontsize=13, fontweight="bold")
        ax_map.set_xlabel("X Coordinate")
        ax_map.set_ylabel("Y Coordinate")
        ax_map.legend(loc="upper right")
        ax_map.grid(True, linestyle="--", alpha=0.4)

        # 2. Wait Time Distribution Histogram
        ax_wait = fig.add_subplot(grid[0, 1])
        wait_times = [(r.pickup_time - r.request_time) for r in self.completed_riders if r.pickup_time and r.request_time]
        if wait_times:
            ax_wait.hist(wait_times, bins=12, color="#2ca02c", edgecolor="black", alpha=0.75)
        ax_wait.set_title("Rider Wait Time Distribution", fontsize=12, fontweight="bold")
        ax_wait.set_xlabel("Wait Time (seconds)")
        ax_wait.set_ylabel("Number of Riders")
        ax_wait.grid(True, linestyle="--", alpha=0.4)

        # 3. Core Metrics Summary Panel
        ax_metrics = fig.add_subplot(grid[1, 1])
        ax_metrics.axis("off")

        span = self.current_time if self.current_time > 0 else 1.0
        total_busy = sum(c.total_busy_time for c in self.all_cars)
        avg_utilization = (total_busy / (len(self.all_cars) * span)) * 100.0 if self.all_cars else 0.0
        avg_wait = (sum(wait_times) / len(wait_times)) if wait_times else 0.0
        
        durations = [(r.dropoff_time - r.pickup_time) for r in self.completed_riders if r.dropoff_time and r.pickup_time]
        avg_duration = (sum(durations) / len(durations)) if durations else 0.0

        metrics_text = (
            "=== SYSTEM PERFORMANCE SUMMARY ===\n\n"
            f"• Total Riders Generated : {self.riders_generated_count}\n"
            f"• Total Trips Completed  : {len(self.completed_riders)}\n"
            f"• Total Unmatched Riders : {len(self.unmatched_riders)}\n"
            f"• Simulation Duration    : {span:.2f} s\n\n"
            f"• Average Wait Time      : {avg_wait:.2f} s\n"
            f"• Average Trip Duration  : {avg_duration:.2f} s\n"
            f"• Driver Utilization     : {avg_utilization:.2f}%\n"
            f"• Avg Trips / Car        : {(len(self.completed_riders) / len(self.all_cars)):.2f}\n"
        )

        ax_metrics.text(
            0.05, 0.95, metrics_text, transform=ax_metrics.transAxes, fontsize=11,
            family="monospace", verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.8", facecolor="#f8f9fa", edgecolor="#1f77b4")
        )

        plt.tight_layout()
        plt.savefig(output_file, bbox_inches="tight")
        plt.close()
        print(f"Analytical visualization saved to {output_file}")

    # --- Main Event Engine Loop ---

    def run(self) -> None:
        """Runs the event loop until the priority queue is empty."""
        print("=== SIMULATION STARTED ===")
        self.generate_rider_request()  # Seed initial rider request

        while self.event_queue:
            timestamp, seq, event_type, data = heapq.heappop(self.event_queue)
            self.current_time = timestamp

            if event_type == "RIDER_REQUEST":
                self.handle_rider_request(data)
            elif event_type == "PICKUP_ARRIVAL":
                self.handle_pickup_arrival(data)
            elif event_type == "DROPOFF_ARRIVAL":
                self.handle_dropoff_arrival(data)
            else:
                raise ValueError(f"Unknown event type: {event_type}")

        print("=== SIMULATION COMPLETED ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discrete Event Ride Share Engine")
    parser.add_argument("--max-time", type=float, default=1000.0)
    parser.add_argument("--num-riders", type=int, default=200)
    parser.add_argument("--num-cars", type=int, default=100)
    parser.add_argument("--candidate-count", type=int, default=5)
    parser.add_argument("--map-file", type=str, default="Data\\graph_xy.csv")
    parser.add_argument("--output-img", type=str, default="simulation_summary.png")
    args = parser.parse_args()

    sim = Simulation(
        city_map_file=args.map_file,
        max_time=args.max_time,
        num_riders=args.num_riders,
        num_cars=args.num_cars,
        candidate_count=args.candidate_count,
    )
    sim.run()
    sim.generate_analytical_visualization(args.output_img)