import heapq
import math
from itertools import count
from typing import List, Optional, Tuple, Any


class Point:
    # Represents a point in 2D space with optional associated data.
    def __init__(self, x: float, y: float, data: Any = None):
        self.x = float(x)
        self.y = float(y)
        self.data = data
    # Calculates the Euclidean distance from this point to another point.
    def distance_to(self, other: 'Point') -> float:
        return math.hypot(self.x - other.x, self.y - other.y)
    # Returns a string representation of the point with coordinates formatted to two decimal places.
    def __repr__(self) -> str:
        return f"Point({self.x:.2f}, {self.y:.2f})"


class Rectangle:
    # Represents an axis-aligned rectangle in 2D space, defined by its minimum and maximum x and y coordinates.
    def __init__(self, xmin: float, ymin: float, xmax: float, ymax: float):
        self.xmin = float(xmin)
        self.ymin = float(ymin)
        self.xmax = float(xmax)
        self.ymax = float(ymax)
    # Checks if a given point is contained within the rectangle.
    def contains(self, point: Point) -> bool:
        return (self.xmin <= point.x <= self.xmax and
                self.ymin <= point.y <= self.ymax)
    # Calculates the minimum distance from the rectangle to a given point, returning 0 if the point is inside the rectangle.
    def distance_to_point(self, point: Point) -> float:
        x_mid = (self.xmin + self.xmax) / 2.0
        y_mid = (self.ymin + self.ymax) / 2.0
        half_w = (self.xmax - self.xmin) / 2.0
        half_h = (self.ymax - self.ymin) / 2.0

        dx = max(0.0, abs(point.x - x_mid) - half_w)
        dy = max(0.0, abs(point.y - y_mid) - half_h)
        return math.hypot(dx, dy)


class QuadtreeNode:
 # Represents a node in the Quadtree, which can contain points and subdivide into child quadrants.
    def __init__(self, boundary: Rectangle, capacity: int = 4, depth: int = 0, max_depth: int = 10):
        self.boundary = boundary
        self.capacity = capacity
        self.depth = depth
        self.max_depth = max_depth
        self.points: List[Point] = []
        self.divided: bool = False
        # Child quadrants (NW, NE, SW, SE) initialized to None until subdivision occurs.
        self.northwest: Optional['QuadtreeNode'] = None
        self.northeast: Optional['QuadtreeNode'] = None
        self.southwest: Optional['QuadtreeNode'] = None
        self.southeast: Optional['QuadtreeNode'] = None

    def subdivide(self):
        # Subdivides the current node into four child quadrants (NW, NE, SW, SE).
        x_mid = (self.boundary.xmin + self.boundary.xmax) / 2.0
        y_mid = (self.boundary.ymin + self.boundary.ymax) / 2.0
        nd = self.depth + 1

        # NW: [xmin, x_mid] x [y_mid, ymax]
        self.northwest = QuadtreeNode(
            Rectangle(self.boundary.xmin, y_mid, x_mid, self.boundary.ymax),
            self.capacity, nd, self.max_depth
        )
        # NE: [x_mid, xmax] x [y_mid, ymax]
        self.northeast = QuadtreeNode(
            Rectangle(x_mid, y_mid, self.boundary.xmax, self.boundary.ymax),
            self.capacity, nd, self.max_depth
        )
        # SW: [xmin, x_mid] x [ymin, y_mid]
        self.southwest = QuadtreeNode(
            Rectangle(self.boundary.xmin, self.boundary.ymin, x_mid, y_mid),
            self.capacity, nd, self.max_depth
        )
        # SE: [x_mid, xmax] x [ymin, y_mid]
        self.southeast = QuadtreeNode(
            Rectangle(x_mid, self.boundary.ymin, self.boundary.xmax, y_mid),
            self.capacity, nd, self.max_depth
        )
        self.divided = True
    # Inserts a point into the Quadtree node, subdividing if necessary, and returns True if successful, False otherwise.
    def insert(self, point: Point) -> bool:
        if not self.boundary.contains(point):
            return False
        # If the node has space and is not divided, or if it has reached max depth, add the point here.
        if (len(self.points) < self.capacity and not self.divided) or self.depth >= self.max_depth:
            self.points.append(point)
            return True
        # If the node is at capacity and not divided, subdivide and redistribute points.
        if not self.divided:
            self.subdivide()
            existing_points = self.points
            self.points = []
            for p in existing_points:
                self._insert_into_children(p)

        return self._insert_into_children(point)
    # Helper method to insert a point into the appropriate child quadrant.
    def _insert_into_children(self, point: Point) -> bool:
        return (self.northwest.insert(point) or
                self.northeast.insert(point) or
                self.southwest.insert(point) or
                self.southeast.insert(point))
    # Removes a point from the Quadtree, returning True if successful, False otherwise.
    def remove(self, point: Point) -> bool:
        if not self.boundary.contains(point):
            return False
        # Attempt to remove the point from the current node's points list.
        for idx, p in enumerate(self.points):
            if p is point:
                self.points.pop(idx)
                return True
        # If the node is divided, attempt to remove the point from child quadrants.
        if self.divided:
            if (self.northwest.remove(point) or
                self.northeast.remove(point) or
                self.southwest.remove(point) or
                self.southeast.remove(point)):
                return True

        return False


class Quadtree:
    # Represents the Quadtree data structure for efficient spatial indexing and querying.
    def __init__(self, boundary: Rectangle, capacity: int = 4, max_depth: int = 10):
        self.boundary = boundary
        self.capacity = capacity
        self.max_depth = max_depth
        self.root = QuadtreeNode(boundary, capacity, depth=0, max_depth=max_depth)
    # Inserts a point into the Quadtree, returning True if successful, False otherwise.
    def insert(self, point: Point) -> bool:
        return self.root.insert(point)
    # Removes a point from the Quadtree, returning True if successful, False otherwise.
    def remove(self, point: Point) -> bool:
        return self.root.remove(point)
    # Finds the k nearest points to a given query point using a priority queue for efficient searching.
    def find_k_nearest(self, query_point: Point, k: int = 5) -> List[Point]:
        if k <= 0:
            return []

        candidate_heap: List[Tuple[float, int, Point]] = []
        tie_breaker = count()
        # Recursive search function to traverse the Quadtree and find nearest neighbors.
        def _search(node: Optional[QuadtreeNode]):
            if node is None:
                return
            # Calculate the minimum distance from the node's boundary to the query point
            min_dist = node.boundary.distance_to_point(query_point)
            if len(candidate_heap) == k:
                max_dist = -candidate_heap[0][0]
                if min_dist >= max_dist:
                    return

            # Check points in the current node
            for p in node.points:
                dist = query_point.distance_to(p)
                if len(candidate_heap) < k:
                    heapq.heappush(candidate_heap, (-dist, next(tie_breaker), p))
                else:
                    max_dist = -candidate_heap[0][0]
                    if dist < max_dist:
                        heapq.heappushpop(candidate_heap, (-dist, next(tie_breaker), p))

            if not node.divided:
                return
            # Sort child nodes based on their distance to the query point to prioritize closer quadrants
            children = [node.northwest, node.northeast, node.southwest, node.southeast]
            children.sort(key=lambda child: child.boundary.distance_to_point(query_point))

            for child in children:
                _search(child)

        _search(self.root)
        # Sort the candidate heap to return the nearest points in ascending order of distance
        sorted_heap = sorted([(-item[0], item[2]) for item in candidate_heap], key=lambda x: x[0])
        return [p for _, p in sorted_heap]