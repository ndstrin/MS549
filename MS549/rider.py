# Rider Class
class Rider:
     # Constructor to initialize the rider with an ID and pickup/destination locations
    def __init__(self, rider_id, name, pickup_location, destination):

        self.id = rider_id
        self.name = name
        self.pickup_location = pickup_location
        self.destination = destination
        self.status = 'waiting'  # Rider's status can be 'waiting', 'in_transit', or 'completed'
        print(f"Rider {self.name} ({self.id}) created at location {self.pickup_location}.")

    # Function to display the current details of the rider
    def display_info(self):
        """
        Prints the current details of the rider.
        """
        print(f"--- Rider ID: {self.id} ---")
        print(f"  Name: {self.name}")
        print(f"  Status: {self.status}")
        print(f"  Pickup Location: {self.pickup_location}")
        print(f"  Destination: {self.destination}")
        print("--------------------")

