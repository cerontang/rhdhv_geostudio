import json
import pandas as pd
from src.topography import generate_topography_from_json, generate_topography_direct
from src.geostudio_xml import generate_geostudio_file
from typing import List
import math
from shapely.ops import linemerge, unary_union, polygonize
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Polygon, LineString
import xlwings as xw
from src.utils import find_project_root, Point


class Stratigraphy:
    top_level: List[float]
    material: List[str]
    def from_json(self, path):
        self.top_level = self.generate_elevation_from_json(path)
        self.material = self.generate_material_from_json(path)


    def generate_elevation_from_json(self, path):
        with open(path, 'r') as json_file:
            json_data = json.load(json_file)
            elevation_list = json_data['strat_elev']
        return elevation_list

    def generate_material_from_json(self, path):
        with open(path, 'r') as json_file:
            json_data = json.load(json_file)
            material_list = json_data['material']
        return material_list

    def from_direct(self):
        project_root = find_project_root()
        input_file = project_root / 'data' / 'input' / 'excel' / 'Input Template.xlsx'
        output_json = project_root / 'data' / 'input' / 'json' / 'strat_data.json'

        print(f"Reading input from: {input_file}")
        wb = xw.Book(input_file)
        ws = wb.sheets['Input']  # Assuming 'Input' is the sheet name

        # Read stratigraphy data
        strat_elev = []
        material = []
        row = 5  # Start from row 5

        while True:
            elev = ws.range(f'D{row}').value
            mat = ws.range(f'E{row}').value

            if elev is None or mat is None:  # Check if either cell is empty
                break

            strat_elev.append(elev)
            material.append(mat)
            row += 1

        wb.close()

        # Reverse the order of data (bottom to top)
        strat_elev.reverse()
        material.reverse()

        # Prepare JSON data
        strat_data = {
            'strat_elev': strat_elev,
            'material': material
        }

        # Save to JSON file
        with open(output_json, 'w') as f:
            json.dump(strat_data, f, indent=2)

        print(f"Stratigraphy data saved to: {output_json}")

        # Load the data into the object
        self.top_level = strat_elev
        self.material = material

        print(str(output_json))
        return str(output_json)

class Surface:
    points: List[Point]

    def from_json(self, start_point, end_point, path, num_sampling_points):
        self.points = generate_topography_from_json(start_point, end_point, path, num_sampling_points)

    def from_direct(self):
        self.points = generate_topography_direct()

class CrossSection2D:
    x_extent: List[float]
    soil_block_points: List[Point]
    cut_soil_polygon_points: List[Point]

    def define_x_extent(self, topography_points):
        x_values = [point[0] for point in topography_points]
        self.x_extent = [min(x_values), max(x_values)]

    def generate_soil_block_points(self, x_extent, strat_elev, topography_points, ref_point):
        _ , max_topo = max(topography_points, key=lambda item: item[1])
        strat_elev.append(max_topo)
        polygon_points = [(x, y) for x in x_extent for y in strat_elev]
        assigned_polygon_points = self.assign_block_points(polygon_points, strat_elev)
        sorted_polygon_points = self.sort_block_points(assigned_polygon_points, ref_point)
        self.soil_block_points = sorted_polygon_points

    def generate_cut_soil_polygon_points(self, polygons, topography_points, ref_point):
        self.cut_soil_polygon_points = self.cut_polygons(polygons, topography_points, ref_point)

    def assign_block_points(self, polygon_points, strat_elev):
        strat_elev.sort()
        result_polygons = []
        for i in range(len(strat_elev) - 1):
            polygon = []
            for point in polygon_points:
                if strat_elev[i] <= point[1] <= strat_elev[i + 1]:
                    polygon.append(point)
            result_polygons.append(polygon)
        return result_polygons

    def sort_block_points(self, polygons, reference_point):
        sorted_polygons = []
        for polygon in polygons:
            # Sort the points by distance from the reference point
            sorted_by_distance = sorted(polygon, key=lambda point: self.distance(point, reference_point))
            # Sort the points clockwise based on angles relative to the reference point in descending order
            sorted_polygon = sorted(sorted_by_distance, key=lambda point: self.angle(point, reference_point), reverse=True)
            sorted_polygons.append(sorted_polygon)
        return sorted_polygons

    def cut_polygons(self, polygons, topography_points, ref_point):
        poly_list = [Polygon(coords) for coords in polygons]
        topography_line = LineString(topography_points)
        line_list = [poly.boundary for poly in poly_list]
        merged_lines = line_list + [topography_line]
        borders = unary_union(merged_lines)
        cut_poly_objs = polygonize(borders)
        #Remove polygons above the topo line
        below_topo_poly_obj = []
        for cut_poly in cut_poly_objs:
            if not cut_poly.centroid.within(cut_poly):
                below_topo_poly_obj.append(cut_poly)
                continue
            line_check = LineString([(cut_poly.centroid.x, ref_point[1]), (cut_poly.centroid.x, cut_poly.centroid.y)])
            intersection = line_check.intersection(topography_line)
            if intersection.geom_type == "Point":
                continue
            below_topo_poly_obj.append(cut_poly)
        return below_topo_poly_obj

    def distance(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def angle(self, point, reference_point):
        x, y = point
        ref_x, ref_y = reference_point
        return math.atan2(ref_y - y, ref_x - x)

    def assign_material_to_polygons(self, block_polygons, cut_polygons, materials):
        cut_poly_material_list = []
        for cut_poly in cut_polygons:
            cut_poly_centroid = cut_poly.centroid
            for block_poly, material in zip(block_polygons, materials):
                block_poly_obj = Polygon(block_poly)
                if block_poly_obj.contains(cut_poly_centroid):
                   cut_poly_material_list.append(material)
        return list(zip(cut_polygons, cut_poly_material_list))

def plot_soil_block(polygons, topography_points):
    colors = plt.cm.get_cmap('tab10', 10)
    color_list = {'color': [colors(i) for i in range(len(polygons))]}
    poly_list = [Polygon(coords) for coords in polygons]
    geo_series = gpd.GeoSeries(poly_list)
    topography_line = LineString(topography_points)
    topography_series = gpd.GeoSeries(topography_line)
    # Create a GeoDataFrame from the GeoSeries
    gdf = gpd.GeoDataFrame(color_list, geometry=geo_series)
    # Plot all polygons
    ax = gdf.plot(color=gdf['color'], figsize=(10, 10), legend=False)
    # Plot the topography line on top of the polygons
    topography_series.plot(ax=ax, color='black', linewidth=2)
    plt.title('Stratigraphy')
    plt.show()

def plot_cut_soil_polygon(below_topo_poly_obj):
    geo_series = gpd.GeoSeries(below_topo_poly_obj)
    colors = plt.cm.get_cmap('tab10', 10)
    color_list = {'color': [colors(i) for i in range(len(below_topo_poly_obj))]}
    gdf = gpd.GeoDataFrame(color_list, geometry=geo_series)
    gdf.plot(color=gdf['color'], figsize=(10, 10), legend=False)
    plt.title('Stratigraphy')
    plt.show()

def create_dataframe(list):
    df = pd.DataFrame(list, columns=["Geometry Points", "Material Type"])
    return df

def df_to_json(df):
    result = []
    for idx, row in df.iterrows():
        if isinstance(row['Geometry Points'], Polygon):
            geometry_points = row['Geometry Points'].exterior.coords[:]
        else:
            geometry_points = row['Geometry Points']
        json_obj = {
            "Geometry ID": idx,
            "Geometry Points": geometry_points,
            "Material Type": row['Material Type']
        }
        result.append(json_obj)
    json_data = json.dumps(result, indent=4)  # Add indentation for better readability
    json_data = json.loads(json_data)
    return json_data

def export_json(json_data, file_path):
    with open(file_path, 'w') as f:
        json.dump(json_data, f)


def section_to_geostudio(scale, sectionjson_path, blank_gs_path, xml_points_path, xml_regions_path, strat_elev_path, xml_materials_point_path):
    generate_geostudio_file(scale, sectionjson_path, blank_gs_path, xml_points_path, xml_regions_path, strat_elev_path, xml_materials_point_path)

######################################################################