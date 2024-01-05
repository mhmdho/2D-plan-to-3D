import numpy as np
import pyvista as pv
from dxf_to_pyvista import dxf_to_pyvista_line, dxf_to_pyvista_polyline, dxf_to_pyvista_hatch
from roof_utilities import create_floor_surface


Mesh_Doors = pv.MultiBlock()
Mesh_Walls = pv.MultiBlock()
Mesh_Roof = pv.MultiBlock()
Mesh_Stairs = pv.MultiBlock()
Mesh_Windows = pv.MultiBlock() 
Mesh_Outline_window = pv.MultiBlock()
Mesh_Balcony = pv.MultiBlock()
Mesh_Floors = pv.MultiBlock()


def extract_door_and_window(mesh,fraction_wall1,fraction_wall2):
    bounds = mesh.bounds
    z_min, z_max = bounds[4], bounds[5]
    total_height = z_max - z_min
    h_wall1 = fraction_wall1 * total_height
    h_wall2 = fraction_wall2 * total_height
    h_door_or_window = total_height - (h_wall1 + h_wall2)
    z1_door_or_window = z_min + h_wall1
    z2_door_or_window = z_max - h_wall2
    lower_wall = mesh.clip(normal=[0, 0, 1], origin=(0, 0, z1_door_or_window)) #Clip total mesh from z1_door_or_window upwards
    door_or_window = mesh.clip(normal=[0, 0, 1], origin=(0, 0, z2_door_or_window)) #Clip total mesh from z2_door_or_window upwards
    door_or_window = door_or_window.clip(normal=[0, 0, -1], origin=(0, 0, z1_door_or_window)) #Clip total mesh from z1_door_or_window downwards
    upper_wall = mesh.clip(normal=[0, 0, -1], origin=(0, 0, z2_door_or_window)) #Clip total mesh from z2_door_or_window downwards
    return lower_wall, door_or_window, upper_wall


def entity_to_mesh(entity):

    mesh = pv.MultiBlock()
        
    if entity.dxftype() == 'LINE':
        mesh = dxf_to_pyvista_line(entity)
        
    elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
        lines = dxf_to_pyvista_polyline(entity)
        for line in lines:
            mesh.append(line)
                    
    elif entity.dxftype() == 'HATCH':
        all_hatch = dxf_to_pyvista_hatch(entity)
        for hatch in all_hatch:
            mesh.append(hatch)
            
    if isinstance(mesh, pv.MultiBlock):
        mesh = mesh.combine().extract_surface()
    
    return mesh


def update_layers(msp, translation_vector, WallHeight):
    
    def extrude_mesh(mesh, height, Translation_Vector):
        mesh.translate(Translation_Vector, inplace=True)
        mesh3D = mesh.extrude([0, 0, height], capping=False)
        return mesh3D
        
    plan_lines = None
    
    for entity in msp:
            
        if 'wal' in entity.dxf.layer.lower() or 'دیوار' in entity.dxf.layer:
            mesh = entity_to_mesh(entity)
            plan_lines = mesh.copy() if plan_lines is None else plan_lines + mesh  # Add every raw line and polyline to plan_lines layer
            mesh3D = extrude_mesh(mesh, WallHeight, translation_vector)
            Mesh_Walls.append(mesh3D)
            
        elif 'stair' in entity.dxf.layer.lower() or 'پله' in entity.dxf.layer:
            mesh = entity_to_mesh(entity)
            plan_lines = mesh.copy() if plan_lines is None else plan_lines + mesh  # Add every raw line and polyline to plan_lines layer
            mesh3D = extrude_mesh(mesh, WallHeight/8, translation_vector)
            Mesh_Stairs.append(mesh3D)
            
        elif 'balcony' in entity.dxf.layer.lower() or 'بالکن' in entity.dxf.layer:
            mesh = entity_to_mesh(entity)
            plan_lines = mesh.copy() if plan_lines is None else plan_lines + mesh  # Add every raw line and polyline to plan_lines layer
            mesh = extrude_mesh(mesh, WallHeight/4, translation_vector)
            Mesh_Balcony.append(mesh)
            
        elif 'door' in entity.dxf.layer.lower() or 'در' in entity.dxf.layer:
            mesh = entity_to_mesh(entity)
            plan_lines = mesh.copy() if plan_lines is None else plan_lines + mesh  # Add every raw line and polyline to plan_lines layer
            mesh3D = extrude_mesh(mesh, WallHeight, translation_vector)
            lower_wall, door, upper_wall = extract_door_and_window(mesh3D, 1/12 , 1/4)        
            Mesh_Walls.append(lower_wall)
            Mesh_Doors.append(door)
            Mesh_Walls.append(upper_wall)
            
        elif 'win' in entity.dxf.layer.lower() or 'پنجره' in entity.dxf.layer:
            mesh = entity_to_mesh(entity)
            plan_lines = mesh.copy() if plan_lines is None else plan_lines + mesh  # Add every raw line and polyline to plan_lines layer
            mesh3D = extrude_mesh(mesh, WallHeight, translation_vector)
            lower_wall, window, upper_wall = extract_door_and_window(mesh3D, 1/12 , 1/4)        
            Mesh_Walls.append(lower_wall)
            Mesh_Windows.append(window)
            Mesh_Walls.append(upper_wall)
            # outline_window = window.outline()
            # Mesh_Outline_window.append(outline_window)
        
    plan_lines.translate(translation_vector, inplace=True)        
    floor_surface = create_floor_surface(plan_lines)
    Mesh_Floors.append(floor_surface)


def TextureScale(surface, scale_factor):
    
    surface0 = surface.copy()
    
    if 'Texture Coordinates' in surface0.point_data:
        # Get the texture coordinates
        tcoords = surface0.point_data['Texture Coordinates']

        # Scale the texture coordinates to zoom out
        tcoords *= scale_factor

        # Set the adjusted texture coordinates back to the mesh
        surface0.point_data['Texture Coordinates'] = tcoords
        return surface0
    
    else:
        return surface


def get_ScaleFactor_and_Translation(mesh, max_boundary=100):

    # If mesh is a MultiBlock, Convert into pv.PolyData()
    if isinstance(mesh, pv.MultiBlock):
        mesh = mesh.combine().extract_surface()
        
    mesh0 = mesh.copy()
    center = mesh0.center
    center[-1] = 0
    mesh_centered = mesh0.translate(-np.array(center))
    # Calculate the scaling factor
    bounds = mesh_centered.bounds
    max_extent = max([bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]])
    scale_factor = max_boundary / max_extent
    return center, scale_factor


def prepare_for_3DViewers(mesh, center, scale_factor):
    
    """ Centers a PyVista mesh to [0, 0, 0] and rescales it to fit within a maximum boundary."""
    
    # If mesh is a MultiBlock, Convert into pv.PolyData()
    if isinstance(mesh, pv.MultiBlock):
        mesh = mesh.combine().extract_surface()

    mesh0 = mesh.copy()
    
    # Translate the mesh center to [0, 0, 0]
    mesh_centered = mesh0.translate(-np.array(center))

    # Rescale the mesh
    transformed_mesh = mesh_centered.scale([scale_factor, scale_factor, scale_factor], inplace=False)
    
    # Swap Y and Z axes
    transformed_mesh.points = np.column_stack((transformed_mesh.points[:, 0],  # X
                                               transformed_mesh.points[:, 2],  # Z
                                               -transformed_mesh.points[:, 1])) # Y
    
    # transformed_mesh.points[:, [1, 2]] = transformed_mesh.points[:, [2, 1]]   #Alternatively use this line to swap Y and Z
    
    transformed_mesh = transformed_mesh.point_data_to_cell_data()
    transformed_mesh = transformed_mesh.compute_normals()
    transformed_mesh = transformed_mesh.texture_map_to_plane()
    transformed_mesh = transformed_mesh.triangulate()

    return transformed_mesh


def convert_tr_to_d(mtl_file_path):
    # Read the original .mtl file
    with open(mtl_file_path, 'r') as file:
        lines = file.readlines()

    # Modify the lines with the Tr parameter
    modified_lines = []
    for line in lines:
        if line.startswith('Tr'):
            tr_value = float(line.split()[1])
            # d_value = 1 - tr_value
            d_value = tr_value
            modified_line = f'd {d_value}\n'
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)

    # Write the modified content back to the .mtl file
    with open(mtl_file_path, 'w') as file:
        file.writelines(modified_lines)
