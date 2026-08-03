
# import the Car and Rider classes from their respective modules
from re import S

from car import Car
from rider import Rider
from graph import Graph


# Simulation class to manage riders and cars
class Simulation:
    # Initialize the simulation with empty dictionaries for riders and cars
    def __init__(self):
        self.riders = {}
        self.cars = {}
        # Initialize the graph for the simulation
        self.map = Graph()
        self.map.load_from_file("map.csv")
        print("Simulation initialized with map data.")
    # Function to add a rider to the simulation
    def add_rider(self, rider):
        self.riders[rider.id] = rider
        print(f"Rider {rider.name} added at pick up location: {rider.pickup_location}.")
    # Function to add a car to the simulation
    def add_car(self, car):
        self.cars[car.id] = car
        print(f"Driver {car.driver_name} is online at {car.location}.")


Sim = Simulation()

#print(Sim.map) # Print the graph to verify it has been loaded correctly

# Creates the Cars for the simulation
Car1 = Car(car_id=100, driver_name="Alice", initial_location=('Pine St'))
Car2 = Car(car_id=101, driver_name="Bob", initial_location=('Park Ave'))
Car3 = Car(car_id=102, driver_name="Charlie", initial_location=('Main St'))

# Creates the Riders for the simulation
Rider1 = Rider(rider_id=1, name="John", pickup_location=('Walnut St'), destination=('Park Ave'))
Rider2 = Rider(rider_id=2, name="Jane", pickup_location=('Park Ave'), destination=('Oak Ave'))
Rider3 = Rider(rider_id=3, name="Mike", pickup_location=('Main St'), destination=('Market St'))


# Adds the cars to the simulation
Sim.add_car(Car1)
Sim.add_car(Car2)
Sim.add_car(Car3)

# Adds the riders to the simulation
Sim.add_rider(Rider1)
Sim.add_rider(Rider2)

# Assigns the rider 1 to the car 100
Sim.riders[1] = Sim.cars[100].pickup_passenger(Rider1, Sim.map)
Sim.riders[2] = Sim.cars[100].pickup_passenger(Rider2, Sim.map)
Sim.cars[100].display_info()
Sim.cars[100].goto_dropoff_location(Sim.map)
Sim.cars[100].display_info()
Sim.riders[1] = Sim.cars[100].dropoff_passenger(Rider1, Sim.map)
Sim.cars[100].display_info()

