from typing import Tuple, Optional

class Rider:
    # Constructor to initialize the rider with an ID, start location, and destination
    def __init__(self, rider_id: str, start_location: Tuple[float, float], destination: Tuple[float, float]):
        self.id: str = rider_id
        self.start_location: Tuple[float, float] = start_location
        self.destination: Tuple[float, float] = destination
        self.status: str = "waiting"  # Options: 'waiting', 'in_car', 'completed', 'unmatched', 'unsuccessful'
        self.request_time: Optional[float] = None
        self.pickup_time: Optional[float] = None
        self.dropoff_time: Optional[float] = None
    # Function to display the current details of the rider
    def __repr__(self) -> str:
        return f"Rider({self.id}, start={self.start_location}, dest={self.destination})"
