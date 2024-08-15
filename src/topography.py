import xlwings as xw
import json
import numpy as np
from scipy.interpolate import griddata
import math
from src.utils import find_project_root


def distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def open_surface_file(path):
    with open(path, 'r') as json_file:
        json_data = json.load(json_file)
    return json_data

def transform_surface_to_points(json_data, start_point, end_point, num_sampling_points):
    X = json_data['x']
    Y = json_data['y']
    Z = json_data['z']

    # Ensure that the start and end points are within the valid range
    if (min(X) <= start_point[0] <= max(X)) and (min(X) <= end_point[0] <= max(X)) and \
            (min(Y) <= start_point[1] <= max(Y)) and (min(Y) <= end_point[1] <= max(Y)):
        # Calculate the 'X' and 'Y' coordinates of the sampling points
        x_sampling_points = np.linspace(start_point[0], end_point[0], num_sampling_points)
        y_sampling_points = np.linspace(start_point[1], end_point[1], num_sampling_points)
        # Initialize a list to store the 'Z' values at the sampling points
        z_sampling_points = []
        # Interpolate and extract 'Z' values for each sampling point
        for x, y in zip(x_sampling_points, y_sampling_points):
            z = griddata((X, Y), Z, (x, y), method='cubic')
            z_sampling_points.append(float(z))
        # Print the 'Z' values at the sampling points
        profile = list(zip(x_sampling_points, y_sampling_points, z_sampling_points))
        print(profile)
    else:
        print("The start and/or end points are outside the valid range.")
    return profile

def normalise_topography(profile):
    normalised_topography = []
    for x, y, z in profile:
        normalised_distance = distance((x,y), (profile[0][0], profile[0][1]))
        normalised_topography.append((normalised_distance, z))
    return normalised_topography

def generate_topography_from_json(start_point, end_point, path, num_sampling_points):
    json_data = open_surface_file(path)
    profile = transform_surface_to_points(json_data, start_point, end_point, num_sampling_points)
    normalised_topography = normalise_topography(profile)
    return normalised_topography


def get_input_file_path(file_name='Input Template.xlsx'):
    # Get the path to the project root directory
    project_root = find_project_root()

    # Construct the path to the input Excel file
    file_path = project_root / 'data' / 'input' / 'excel' / file_name

    print(f"Looking for Excel file at: {file_path}")

    return file_path

def generate_topography_direct(file_name='Input Template.xlsx'):
    file_path = get_input_file_path(file_name)

    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    WB = xw.Book(str(file_path))
    WS = WB.sheets["Input"]  # Ensure this sheet name matches your Excel file
    start_row = 24
    points = []

    # Read data until you encounter an empty cell in column B (assuming column B has X coordinates)
    row = start_row
    while WS.range(f"B{row}").value is not None:  # Check if X coordinate is not empty
        X = float(WS.range(f"B{row}").value)
        Y = float(WS.range(f"C{row}").value)
        points.append((X, Y))
        row += 1

    WB.close()
    return points
