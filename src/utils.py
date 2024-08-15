from dataclasses import dataclass
from typing import List
import math
from specklepy.objects.base import Base
import sys
from pathlib import Path

def find_project_root():
    if getattr(sys, 'frozen', False):
        application_path = Path(sys.executable).parent
    else:
        application_path = Path(__file__).resolve().parent

    print(f"Initial application path: {application_path}")

    # Look for the 'data' directory, which should always be present
    while not (application_path / 'data').exists():
        parent = application_path.parent
        if parent == application_path:
            raise Exception("Project root not found")
        application_path = parent

    print(f"Final project root: {application_path}")
    return application_path

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