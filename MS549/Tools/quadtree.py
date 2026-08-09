
import math

class Point:
    # Represents a point 
    def __init__(self, x: float, y: float, data=None):
        self.x = x
        self.y = y
        self.data = data
    # Calculates the distance to another point.
    def distance_to(self, other: 'Point') -> float:
        return math.hypot(self.x - other.x, self.y - other.y)
    # Returns a string representation of the point with two decimal places.
    def __repr__(self):
        return f"Point({self.x:.2f}, {self.y:.2f})"


class Rectangle:
    # Represents a rectangle 
    def __init__(self, x: float, y: float, w: float, h: float):
        self.x = x  
        self.y = y  
        self.w = w  
        self.h = h  
    # Checks if a point is contained within the rectangle.
    def contains(self, point: Point) -> bool:
        return (self.x - self.w <= point.x <= self.x + self.w and
                self.y - self.h <= point.y <= self.y + self.h)
    # Calculates the distance from the rectangle to a point
    def distance_to_point(self, point: Point) -> float:
        dx = max(0.0, abs(point.x - self.x) - self.w)
        dy = max(0.0, abs(point.y - self.y) - self.h)
        return math.hypot(dx, dy)


class QuadtreeNode:
    # Represents a node in the quadtree
    def __init__(self, boundary: Rectangle, capacity: int = 4):
        self.boundary = boundary
        self.capacity = capacity
        self.points = []
        self.divided = False
        
        self.northwest = None
        self.northeast = None
        self.southwest = None
        self.southeast = None
    # Subdivides the current node into four child nodes (quadrants).
    def subdivide(self):
        x, y = self.boundary.x, self.boundary.y
        w, h = self.boundary.w / 2.0, self.boundary.h / 2.0

        self.northwest = QuadtreeNode(Rectangle(x - w, y + h, w, h), self.capacity)
        self.northeast = QuadtreeNode(Rectangle(x + w, y + h, w, h), self.capacity)
        self.southwest = QuadtreeNode(Rectangle(x - w, y - h, w, h), self.capacity)
        self.southeast = QuadtreeNode(Rectangle(x + w, y - h, w, h), self.capacity)

        self.divided = True
    # Inserts a point into the quadtree node. If the node exceeds its capacity
    def insert(self, point: Point) -> bool:
        if not self.boundary.contains(point):
            return False
        # If the node has space and is not divided, add the point to this node.
        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point)
            return True
        # If the node is at capacity, subdivide and redistribute points to child nodes.
        if not self.divided:
            self.subdivide()
            existing_points = self.points
            self.points = []
            for p in existing_points:
                self._insert_into_children(p)

        return self._insert_into_children(point)
    # Helper method to insert a point into the appropriate child node.
    def _insert_into_children(self, point: Point) -> bool:
        return (self.northwest.insert(point) or
                self.northeast.insert(point) or
                self.southwest.insert(point) or
                self.southeast.insert(point))


class Quadtree:
    # Represents the quadtree structure
    def __init__(self, boundary: Rectangle, capacity: int = 4):
        self.boundary = boundary
        self.root = QuadtreeNode(boundary, capacity)
    # Inserts a point into the quadtree by delegating to the root node's insert method.
    def insert(self, point: Point) -> bool:
        return self.root.insert(point)
    # Finds the nearest point in the quadtree to a given query point
    def find_nearest(self, query_point: Point):
        best = {"point": None, "distance": float('inf')}
        self._find_nearest_recursive(self.root, query_point, best)
        return best["point"], best["distance"]
    # Recursive helper method to find the nearest point in the quadtree
    def _find_nearest_recursive(self, node: QuadtreeNode, query_point: Point, best: dict):
        if node is None:
            return
        # Calculate the minimum distance from the query point to the node's boundary
        min_rect_dist = node.boundary.distance_to_point(query_point)
        if min_rect_dist >= best["distance"]:
            return
        # Check the points in the current node
        for p in node.points:
            dist = query_point.distance_to(p)
            if dist < best["distance"]:
                best["distance"] = dist
                best["point"] = p
        # If the node is divided, recursively search its children
        if not node.divided:
            return

        children = [node.northwest, node.northeast, node.southwest, node.southeast]
        children.sort(key=lambda child: child.boundary.distance_to_point(query_point))
        # Recursively search the child nodes in order of proximity to the query point
        for child in children:
            self._find_nearest_recursive(child, query_point, best)