import xml.etree.ElementTree as ET
import json
import random

def get_all_point_data(scale, path):
    with open(path, 'r') as json_file:
        json_data = json.load(json_file)
    all_points = []
    scaled_points = []
    for entry in json_data:
        all_points.extend(entry['Geometry Points'])
    scaled_points = scale_points(all_points, scale)
    return scaled_points

def get_cross_section_object_list(scale, path):
    with open(path, 'r') as json_file:
        json_data = json.load(json_file)
    cross_section_object_list = []
    output_list = []
    for geometry in json_data:
        geometry_id = geometry["Geometry ID"]
        geometry_points = geometry["Geometry Points"]
        material_type = geometry["Material Type"]
        cross_section_object_list.append([geometry_id, geometry_points, material_type])
    for id, pts, mat in cross_section_object_list:
        pts = scale_points(pts, scale)
        output_list.append([id, pts, mat])
    return output_list


def scale_points(point_list, scale):
    scaled_points = [[f"{x * scale:.3f}", f"{y * scale:.3f}"] for x, y in point_list]
    return scaled_points

def write_point_data(point_list, input_path, output_path):
    tree = ET.parse(input_path)
    root = tree.getroot()
    points_element = root.find('.//Points')
    print(points_element)
    if points_element is None:
        # If 'Points' element does not exist, create one
        points_element = ET.SubElement(root, 'Points')
    else:
        # Clear existing 'Point' sub-elements if 'Points' element exists
        points_element.clear()
    #points_element.set('Len', str(len(point_list)))
    # Add new 'Point' elements based on the provided point list
    drawn_points = []
    counter = 1
    for idx, (x, y) in enumerate(point_list, start=1):
        if (x, y) in drawn_points:
            continue
        drawn_points.append((x, y))
        point = ET.SubElement(points_element, 'Point')
        point.set('ID', str(counter))
        point.set('X', x)
        point.set('Y', y)
        point.set('Pinned', 'true')
        counter += 1
        print(point.attrib)
    points_element.set('Len', str(len(drawn_points)))
    tree.write(output_path)

def write_region_data(xml_points, cross_section_object_list, input_path, output_path):
    tree = ET.parse(input_path)
    root = tree.getroot()
    for geometry in root.findall('.//Geometry'):
        points = geometry.find('Points')
        if points is not None:
            # Create the new <Regions> element
            regions = ET.Element('Regions')
            # Add a sub-element or text to ensure closing tag
            regions.text = '\n'  # Adds a newline and spaces for formatting
            # Insert <Regions> after <Points>
            geometry.insert(list(geometry).index(points) + 1, regions)

    region_data = []
    for id, pts, mat in cross_section_object_list:
        id_indexed_list = [id+1]
        geom_pt_ID_list = []
        for pt in pts:
            geom_pt_ID_list.append(xml_points.index(pt)+1)
        geom_pt_ID_list.pop(0)
        no_duplicates = []
        for item in geom_pt_ID_list:
            if item not in no_duplicates:
                no_duplicates.append(item)
        id_indexed_list.append(no_duplicates)
        region_data.append(id_indexed_list)
    print(region_data)

    for geometry in root.findall('.//Geometry'):
        regions = geometry.find('Regions')
        regions.set('Len', str(len(region_data)))
        for id, points in region_data:
            region = ET.SubElement(regions, 'Region')
            # Add <ID>
            id_elem = ET.SubElement(region, 'ID')
            id_elem.text = str(id)
            # Add <PointIDs>
            point_ids = ET.SubElement(region, 'PointIDs')
            point_ids.text = ','.join(map(str, points))
            # Formatting
            region.tail = '\n        ' if id != region_data[-1][0] else '\n      '
    tree.write(output_path)

def extract_points_from_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    points = []
    for point in root.findall(".//Points/Point"):
        x = point.get('X')
        y = point.get('Y')
        points.append([x, y])
    return points

def generate_random_colors(n):
    colors = set()
    while len(colors) < n:
        color = "RGB=({},{},{})".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        colors.add(color)
    return list(colors)

def write_material_data(section_json_path, input_path, output_path):
    #pass
    tree = ET.parse(input_path)
    root = tree.getroot()
    geometries = root.find('.//Geometries')
    materials = ET.Element('Materials')
    materials.text = '\n'
    with open(section_json_path, 'r') as f:
        json_data = json.load(f)
    materials_len = len(json_data["material"])
    materials = ET.Element('Materials', Len=str(materials_len))
    colors = generate_random_colors(materials_len)

    # Iterate over materials from JSON data
    for idx, (material, color) in enumerate(zip(json_data["material"], colors), start=1):
        material_element = ET.SubElement(materials, "Material")
        ET.SubElement(material_element, "ID").text = str(idx)
        ET.SubElement(material_element, "Color").text = color
        ET.SubElement(material_element, "Name").text = material
        ET.SubElement(material_element, "SlopeModel").text = "None"
        stress_strain = ET.SubElement(material_element, "StressStrain")
        #Update in the future
        for param in ["JointEffectiveCohesion", "IntactRockParam", "GeologicalStrengthIndex",
                      "DisturbanceFactor", "Cohesion", "CohesionPrime", "PhiPrime",
                      "YoungsPrimeModulus", "EffectivePoissonsRatio", "EPrimeModulusXPrime",
                      "EffectivePoissonsRatioXPrime", "EPrimeModulusYPrime", "EffectivePoissonsRatioYPrime",
                      "ShearModulusXYPrime"]:
            ET.SubElement(stress_strain, param, Missing="true")
    root.insert(list(root).index(geometries) + 1, materials)
    tree.write(output_path)

def generate_geostudio_file(scale, sectionjson_path, blank_gs_path, xml_points_path, xml_regions_path, strat_elev_path, xml_materials_point_path):
    point_list = get_all_point_data(scale, sectionjson_path)
    write_point_data(point_list, blank_gs_path, xml_points_path)
    cross_section_object_list = get_cross_section_object_list(scale, sectionjson_path)
    print(cross_section_object_list)
    xml_points = extract_points_from_xml(xml_points_path)
    print(xml_points)
    write_region_data(xml_points, cross_section_object_list, xml_points_path, xml_regions_path)
    write_material_data(strat_elev_path, xml_regions_path, xml_materials_point_path)




