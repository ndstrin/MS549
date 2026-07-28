
# import the Car and Rider classes from their respective modules
from car import Car
from rider import Rider


# Simulation class to manage riders and cars
class Simulation:
    # Initialize the simulation with empty dictionaries for riders and cars
    def __init__(self):
        self.riders = {}
        self.cars = {}
    # Function to add a rider to the simulation
    def add_rider(self, rider):
        self.riders[rider.id] = rider
        print(f"Rider {rider.name} added at pick up location: {rider.pickup_location}.")
    # Function to add a car to the simulation
    def add_car(self, car):
        self.cars[car.id] = car
        print(f"Driver {car.driver_name} is online at {car.location}.")


Sim = Simulation()

# Creates the Cars for the simulation
Car1 = Car(car_id=100, driver_name="Alice", initial_location=(40.7, -74.0))
Car2 = Car(car_id=101, driver_name="Bob", initial_location=(40.8, -73.9))
Car3 = Car(car_id=102, driver_name="Charlie", initial_location=(40.9, -73.8))

# Creates the Riders for the simulation
Rider1 = Rider(rider_id=1, name="John", pickup_location=(50.5, -68.0), destination=(40.8, -73.9))
Rider2 = Rider(rider_id=2, name="Jane", pickup_location=(40.8, -73.9), destination=(40.9, -73.8))
Rider3 = Rider(rider_id=3, name="Mike", pickup_location=(40.9, -73.8), destination=(40.7, -74.0))


# Adds the cars to the simulation
Sim.add_car(Car1)
Sim.add_car(Car2)
Sim.add_car(Car3)

# Adds the riders to the simulation
Sim.add_rider(Rider1)
Sim.add_rider(Rider2)
Sim.add_rider(Rider3)   

# Assigns the rider 1 to the car 100
Sim.cars[100].passengers.append(Sim.riders[1])
Sim.cars[100].status = "En route"
Sim.cars[100].destination = Sim.riders[1].pickup_location
Sim.riders[1].status = "Assigned to Car 100"

# Displays the information of the cars and riders
Sim.cars[100].display_info()
Sim.cars[101].display_info()
Sim.riders[1].display_info()