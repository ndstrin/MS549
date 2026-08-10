
# import the Car and Rider classes from their respective modules
import heapq
from car import Car
from rider import Rider
from Tools.graph import Graph


# Simulation class to manage riders and cars
class Simulation:
    # Initialize the simulation with empty dictionaries for riders and cars
    def __init__(self):
        self.riders = {}
        self.cars = {}
        self.current_time = 0.0
        self.event_queue = []
        self.sequence_counter = 0
        # Initialize the graph for the simulation
        #self.map = Graph()
        #self.map.load_from_file("Data\\map.csv")
        #print("Simulation initialized with map data.")
    # Function to add a rider to the simulation
    def add_rider(self, rider):
        self.riders[rider.id] = rider
        print(f"Rider {rider.name} added at pick up location: {rider.pickup_location}.")
    # Function to add a car to the simulation
    def add_car(self, car):
        self.cars[car.id] = car
        print(f"Driver {car.driver_name} is online at {car.location}.")

    def find_closest_car_brute_force(self, rider_location: tuple[float, float]) -> Car | None:
        # Finds the closest available car to the rider's location using a brute-force approach.
        available_cars = [car for car in self.cars.values() if car.status == "available"]
        if not available_cars:
            return None

        # Initialize variables to track the closest car and minimum distance
        best_car = None
        min_distance = float("inf")

        rx, ry = rider_location
        # Iterate through all available cars to find the closest one
        for car in available_cars:
            cx, cy = car.location
            dist = abs(cx - rx) + abs(cy - ry)
            if dist < min_distance:
                min_distance = dist
                best_car = car

        return best_car



    def run(self):
        print("=== SIMULATION STARTED ===")
        while self.event_queue:
                # Pop the next event from the priority queue
                timestamp, _, event_type, data = heapq.heappop(self.event_queue)
            
                # Advance internal clock
                self.current_time = timestamp

                # Event Dispatcher
                if event_type == "RIDER_REQUEST":
                    self.handle_rider_request(data)
                elif event_type == "ARRIVAL":
                    self.handle_arrival(data)
                else:
                    raise ValueError(f"Unknown event type: {event_type}")

        print("=== SIMULATION COMPLETED ===")

    # --- Event Handlers ---

    def schedule_event(self, timestamp: float, event_type: str, data: object):
        # Schedules a new event in the simulation's event queue.
        self.sequence_counter += 1
        event_tuple = (timestamp, self.sequence_counter, event_type, data)
        heapq.heappush(self.event_queue, event_tuple)

    def handle_rider_request(self, rider: Rider):
        """Processes a new rider dispatch request."""
        print(f"TIME {self.current_time:.2f}: RIDER {rider.name} requested a ride at {rider.pickup_location}")
        # Find the closest available car to the rider's pickup location
        car = self.find_closest_car_brute_force(rider.pickup_location)
        # If no available car is found, log the event and return
        if car is None:
            print(f"TIME {self.current_time:.2f}: No available cars for RIDER {rider.name}")
            return

        # Link rider and car
        car.passengers = rider
        car.status = "en_route_to_pickup"

        # Calculate time and schedule future ARRIVAL event
        pickup_duration = Car.calculate_travel_time(car, rider.pickup_location)
        arrival_time = self.current_time + pickup_duration
        
        self.schedule_event(arrival_time, "ARRIVAL", car)
        print(f"TIME {self.current_time:.2f}: CAR {car.id} - {car.driver_name} dispatched to RIDER {rider.name} (ETA: {arrival_time:.2f})")

    def handle_arrival(self, car: Car):
        """Processes arrival events at pickup or destination coordinates."""
        rider = car.passengers

        # Determine if the car is arriving at the pickup location or the destination
        if car.status == "en_route_to_pickup":
            print(f"TIME {self.current_time:.2f}: CAR {car.id} - {car.driver_name} picked up RIDER {rider.name}")
            
            # State & coordinate transition
            car.location = rider.pickup_location
            car.status = "en_route_to_destination"
            rider.status = "in_car"

            # Calculate dropoff time and schedule future event
            
            dropoff_duration = Car.calculate_travel_time(car, rider.destination)
            destination_time = self.current_time + dropoff_duration
            
            self.schedule_event(destination_time, "ARRIVAL", car)

        elif car.status == "en_route_to_destination":
            print(f"TIME {self.current_time:.2f}: CAR {car.id} - {car.driver_name} dropped off RIDER {rider.name}")
            
            # State & coordinate transition
            car.location = rider.destination
            car.status = "available"
            rider.status = "completed"
            
            # Unlink
            car.passengers = None



# test code to run the simulation
if __name__ == "__main__":
    sim = Simulation()
    print("=== TEST SIMULATION ===")
    print("== Adding Cars ==")
    # 1. Setup initial fleet state 
    car1 = Car("101", "Alice", (10.0, 10.0))
    car2 = Car("105", "Bob", (100.0, 100.0))
    car3 = Car("110", "Charlie", (50.0, 50.0))
    sim.add_car(car1)
    sim.add_car(car2)
    sim.add_car(car3)

    # 2. Setup initial rider requests
    print("== Adding Riders ==")
    rider1 = Rider("R1", name="John", pickup_location=(15.0, 20.0), destination=(50.0, 80.0))
    rider2 = Rider("R2", name="Jane", pickup_location=(90.0, 95.0), destination=(10.0, 10.0))
    rider3 = Rider("R3", name="Mike", pickup_location=(60.0, 60.0), destination=(20.0, 20.0))
    sim.add_rider(rider1)
    sim.add_rider(rider2)
    sim.add_rider(rider3)

    # 3. Schedule initial demand events
    sim.schedule_event(timestamp=0.0, event_type="RIDER_REQUEST", data=rider1)
    sim.schedule_event(timestamp=2.0, event_type="RIDER_REQUEST", data=rider2)
    sim.schedule_event(timestamp=4.0, event_type="RIDER_REQUEST", data=rider3)

    # 4. Run discrete event loop
    sim.run()

