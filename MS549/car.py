# Car Class 

from Tools.pathfinding import find_shortest_path
from rider import Rider


class Car:
     # Constructor to initialize the car with an ID and initial location
    def __init__(self, car_id, driver_name, initial_location):

        self.id = car_id
        self.driver_name = driver_name
        self.location = initial_location
        self.status = 'available'
        self.passengers = []
        self.destination = None
        self.route = []
        self.route_time = 0.0
        print(f"Car {self.id} created at location {self.location}.")

    # Function to calculate the shortest route to a destination using Dijkstra's algorithm
    def calculate_route(self, destination, graph):
        path, travelTime = find_shortest_path(graph, self.location, destination)
        # Update the car's route and route time based on the calculated path
        self.route = path
        self.route_time = travelTime
        self.destination = destination
        return self.route, self.route_time

    # Function to pick up a passenger and update the car's status and route
    def pickup_passenger(self, rider: Rider, graph):
        if rider not in self.passengers:
            self.passengers.append(rider)
            self.status = "En route to Pickup"
            self.destination = rider.pickup_location
            rider.status = f"Assigned to Car {self.id}"
            self.calculate_route(destination=rider.pickup_location, graph=graph)
            return rider

    # Function to set the car's destination to the dropoff location of the first passenger
    def goto_dropoff_location(self, graph):
        if self.passengers:
            # Set the destination to the first passenger's destination
            self.destination = self.passengers[0].destination
            self.calculate_route(destination=self.destination, graph=graph)
            self.status = "En route to Dropoff"
            return self.destination

    # Function to drop off a passenger and update the car's status and route
    def dropoff_passenger(self, rider: Rider, graph):
        if rider in self.passengers:
            self.location = rider.destination
            self.passengers.remove(rider)
            rider.status = "Dropped off"
            if self.passengers:
                # If there are still passengers, set the next destination to the first passenger's destination
                self.destination = self.passengers[0].destination
                self.calculate_route(destination=self.destination, graph=graph)
            else:
                # If no passengers left, set status to available and clear destination
                self.status = "available"
                self.destination = None
                self.route = []
                self.route_time = 0.0
            return rider

    # Function to display the current details of the car
    def display_info(self):
        print(
            # Display the car's ID, driver name, current location, status, and destination
            f"Car ID: {self.id} | Driver: {self.driver_name} | Location: {self.location} | "
            f"Status: {self.status} | Destination: {self.destination}"
        )
        if self.route:
            # Display the planned route and estimated time if a route has been calculated
            print(
                f"  Planned Route: {' -> '.join(self.route)} (Est. Time: {self.route_time} mins)"
            )


