
# Project Title: Ride Share Simulation Application

## Purpose/Design: 

This project is designed to simulate a ride-sharing application. The goal of this weeks project was to implement the graph using Dijkstra's algorithm to find the shortest path between two nodes in a network. The application reads a map of nodes and edges from a CSV file, where each edge has an associated travel time. The user can input a starting node and an ending node, and the application will calculate and display the shortest path along with the total travel time.

## Map Data Format:
Ensure map.csv is present in the working directory with your desired network connections and travel times. In the below format.

>start_node,end_node,travel_time<br>
>Main St,Broadway,5<br>
>Broadway,Main St,5<br>
>Main St,Oak Ave,3<br>

## How to Run: 
Currently, the project is designed to be run in a Python environment. To execute the application, follow these steps:

1. Ensure you have Python installed on your system.
2. Download or clone the project repository to your local machine.
3. Install any required dependencies listed in the requirements.txt file using the command: `pip install -r requirements.txt`.
4. Navigate to the project directory in your terminal or command prompt.
5. Ensure that the map.csv file is present in the working directory.
6. Run the main application script using the command: `python simulation.py`.

## Dependencies: 
A list of any Python libraries required will be include in the requirements.txt file. Currently, the project requires no libraries.
