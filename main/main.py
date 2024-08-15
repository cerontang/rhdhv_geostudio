from src.utils import find_project_root
from src.stratigraphy import Stratigraphy, Surface, CrossSection2D, plot_soil_block, plot_cut_soil_polygon, \
    create_dataframe, df_to_json, export_json, section_to_geostudio


def example_geostudio():
    print("Initialising...")
    print("Loading Models")

    project_root = find_project_root()
    data_dir = project_root / 'data'

    # Update paths to use project structure
    cross_section_export_path = data_dir / 'output' / 'cross_section_data.json'
    blank_gs_path = data_dir / 'input' / 'xml' / 'Python Geostudio Template Blank.xml'
    xml_points_path = data_dir / 'output' / 'points_xml_file.xml'
    xml_regions_path = data_dir / 'output' / 'regions_xml_file.xml'
    xml_materials_point_path = data_dir / 'output_final' / 'materials_xml_file.xml'


    print("Loaded Models")

    # Stratigraphy
    stratigraphy = Stratigraphy()
    strat_data_path = stratigraphy.from_direct()

    # Topography Surface
    surface = Surface()
    surface.from_direct()

    # Cross Section
    ref_point = [0, min(stratigraphy.top_level)]
    cross_section = CrossSection2D()
    cross_section.define_x_extent(surface.points)
    cross_section.generate_soil_block_points(cross_section.x_extent, stratigraphy.top_level, surface.points, ref_point)
    cross_section.generate_cut_soil_polygon_points(cross_section.soil_block_points, surface.points, ref_point)

    print(cross_section.cut_soil_polygon_points)
    print(len(cross_section.cut_soil_polygon_points))

    # Cross 2D Section
    plot_soil_block(cross_section.soil_block_points, surface.points)
    plot_cut_soil_polygon(cross_section.cut_soil_polygon_points)

    # Assign material to polygons in 2D section
    polygon_with_material_list = cross_section.assign_material_to_polygons(
        cross_section.soil_block_points, cross_section.cut_soil_polygon_points, stratigraphy.material
    )
    df = create_dataframe(polygon_with_material_list)
    print(df)

    # Convert df into a json as output
    section2D_json = df_to_json(df)
    export_json(section2D_json, str(cross_section_export_path))

    # Generate Geostudio XML file
    scale = 1
    section_to_geostudio(scale, str(cross_section_export_path), str(blank_gs_path),
                         str(xml_points_path), str(xml_regions_path), strat_data_path,
                         str(xml_materials_point_path))

if __name__ == "__main__":
    example_geostudio()