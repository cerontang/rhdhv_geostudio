from dataclasses import dataclass
from typing import List
import math
from specklepy.objects.base import Base


@dataclass
class Point(Base):
    x: float = None
    y: float = None
    z: float = None

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return all([
            math.isclose(self.x or 0, other.x or 0),
            math.isclose(self.y or 0, other.y or 0),
            math.isclose(self.z or 0, other.z or 0)
        ])


def get_or_create_point(point_list: List[Point], x, y, z) -> Point:
    new_point = Point(x, y, z)
    for point in point_list:
        if new_point == point:
            return point
    return new_point