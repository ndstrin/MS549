import math
import random
import time
from Tools.quadtree import Quadtree, Rectangle, Point


def brute_force_k_nearest(points, query_point, k=5):
    # Finds the k nearest points using brute-force search.
    sorted_points = sorted(points, key=lambda p: query_point.distance_to(p))
    k_nearest = sorted_points[:k]
    return k_nearest, [query_point.distance_to(p) for p in k_nearest]


def run_test():
    # 1. Initialize Quadtree Boundary & Instance
    boundary = Rectangle(0, 0, 1000, 1000)
    qt = Quadtree(boundary, capacity=4, max_depth=10)

    # 2. Populate Random Test Fleet
    num_points = 5000
    points_list = []
    random.seed(42)
    # Generate random points and insert them into the Quadtree
    for i in range(num_points):
        x = random.uniform(0, 1000)
        y = random.uniform(0, 1000)
        p = Point(x, y, data=f"Car_{i}")
        points_list.append(p)
        qt.insert(p)
    query_p = Point(random.uniform(0, 1000), random.uniform(0, 1000))
    # 3. Test Nearest Neighbor Search
    k_val = 5
    t0 = time.perf_counter()
    bf_k_matches, _ = brute_force_k_nearest(points_list, query_p, k=k_val)
    t_bf_k = (time.perf_counter() - t0) * 1000
    # 4. Test Quadtree k-Nearest Neighbor Search
    t0 = time.perf_counter()
    qt_k_matches = qt.find_k_nearest(query_p, k=k_val)
    t_qt_k = (time.perf_counter() - t0) * 1000

    print(f"\n--- {k_val}-NEAREST NEIGHBORS ({k_val}-NN) TEST ---")
    print(f"Brute Force {k_val}-NN Time: {t_bf_k:.3f} ms")
    print(f"Quadtree {k_val}-NN Time:    {t_qt_k:.3f} ms")
    print(f"Retrieved Candidates: {len(qt_k_matches)}")
    # Verify that both methods return the same number of matches and that the matches are identical
    assert len(qt_k_matches) == len(bf_k_matches), f"Count mismatch! QT: {len(qt_k_matches)}, BF: {len(bf_k_matches)}"
    for idx, (qt_p, bf_p) in enumerate(zip(qt_k_matches, bf_k_matches)):
        assert qt_p == bf_p, f"Mismatch at index {idx}! QT: {qt_p}, BF: {bf_p}"

    # 5. Test Exact Point Deletion & Duplicate Co-location
    print("\n--- EXACT POINT DELETION TEST ---")
    p_co1 = Point(500.0, 500.0, data="Car_A")
    p_co2 = Point(500.0, 500.0, data="Car_B")
    
    qt.insert(p_co1)
    qt.insert(p_co2)

    removed = qt.remove(p_co1)
    assert removed, "Failed to remove exact Point p_co1"

    # Verify p_co2 is still present
    query_exact = Point(500.0, 500.0)
    match_after_removal = qt.find_k_nearest(query_exact, k=5)
    assert match_after_removal[0] is p_co2, f"Expected p_co2, got {match_after_removal[0]}"
    print("[SUCCESS] Exact object removal verified for co-located points.")

    print("\n[ALL TESTS PASSED] Quadtree implementation verified successfully.")


if __name__ == "__main__":
    run_test()