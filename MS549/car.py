# Car Class 
class Car:
     # Constructor to initialize the car with an ID and initial location
    def __init__(self, car_id, driver_name, initial_location):

        self.id = car_id
        self.driver_name = driver_name
        self.location = initial_location
        self.status = 'available'
        self.passengers = []
        self.destination = None
        print(f"Car {self.id} created at location {self.location}.")

    # Function to display the current details of the car
    def display_info(self):
        """
        Prints the current details of the car.
        """
        print(f"--- Car ID: {self.id} ---")
        print(f"  Status: {self.status}")
        print(f"  Location: {self.location}")
        print(f"  Passengers: {len(self.passengers)}")
        print(f"  Destination: {self.destination}")
        print("--------------------")


