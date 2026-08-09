# Imports
import random
import math
import time
from Tools.quadtree import Quadtree, Rectangle, Point

def brute_force_nearest(points, query_point):
    # Finds the nearest point to the query_point using a brute-force approach.
    best_point = None
    min_dist = float('inf')
    for p in points:
        dist = query_point.distance_to(p)
        if dist < min_dist:
            min_dist = dist
            best_point = p
    return best_point, min_dist

def run_test():
    # Set up the quadtree with a boundary and capacity
    boundary = Rectangle(500, 500, 500, 500)
    qt = Quadtree(boundary, capacity=4)

    # Generate random points and insert them into the quadtree
    num_points = 5000
    points_list = []
    random.seed(42)  
    for i in range(num_points):
        x = random.uniform(0, 1000)
        y = random.uniform(0, 1000)
        p = Point(x, y, data=f"Car_{i}")
        points_list.append(p)
        qt.insert(p)

    # Generate a random query point for nearest neighbor search
    query_p = Point(random.uniform(0, 1000), random.uniform(0, 1000))
    print(f"Query Location: ({query_p.x:.2f}, {query_p.y:.2f})")

    # Measure time for brute-force nearest neighbor search
    t0 = time.perf_counter()
    bf_match, bf_dist = brute_force_nearest(points_list, query_p)
    t_bf = (time.perf_counter() - t0) * 1000

    # Measure time for quadtree nearest neighbor search
    t0 = time.perf_counter()
    qt_match, qt_dist = qt.find_nearest(query_p)
    t_qt = (time.perf_counter() - t0) * 1000

    # Print results
    print("\n--- RESULTS ---")
    print(f"Brute Force Result: Point={bf_match}, Distance={bf_dist:.4f} | Time={t_bf:.3f} ms")
    print(f"Quadtree Result:    Point={qt_match}, Distance={qt_dist:.4f} | Time={t_qt:.3f} ms")

    # Verify that both methods yield the same nearest point and distance
    assert qt_match == bf_match, f"Mismatch! QT: {qt_match}, BF: {bf_match}"
    assert math.isclose(qt_dist, bf_dist, abs_tol=1e-6), "Distances do not match!"
    print("\n[SUCCESS] Quadtree implementation verified against Brute Force algorithm.")

if __name__ == "__main__":
    # Run the test function to validate the quadtree implementation
    run_test()
