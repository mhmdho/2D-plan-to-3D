import os
import ezdxf
import numpy as np
import pyvista as pv
from dxf_to_pyvista import dxf_to_pyvista_line, dxf_to_pyvista_polyline, dxf_to_pyvista_hatch
from roof_utilities import extrude_as_gable, create_floor_surface

##########################################################################################################

folder_path = "decomposed"                     # Path to the decomposed folder
WallHeight = 155                               # Height of each floor

dxf_files = [file for file in os.listdir(folder_path) if file.endswith('.dxf') and file.startswith('plan')]  # List all plan files in the folder
dxf_files.sort(reverse=False)
N = len(dxf_files)                             # Number of files (floors + roof)

MSP = []
for file_name in dxf_files:
    doc = ezdxf.readfile(os.path.join(folder_path, file_name))
    msp = doc.modelspace()
    MSP.append(msp)

x_translate = np.zeros(N)
y_translate = np.zeros(N)
z_translate = [n * WallHeight for n in range(N)]

##########################################################################################################

# Wall_Texture = pv.Texture('Red_brick_wall_texture.jpg')
Wall_Texture = pv.Texture('Textures/wall.jpg')
Window_Texture = pv.Texture('Textures/window2.jpg')
Door_Texture = pv.Texture('Textures/door.png')
Roof_Texture = pv.Texture('Textures/roof.jpg')
Stair_Texture = pv.Texture('Textures/stair.jpg')
Balcony_Texture = pv.Texture('Textures/wall.jpg')
Floor_Texture = pv.Texture('Textures/stair.jpg')

Layers = ['Door', 'Wall', 'Roof', 'Stair', 'Window', 'Balcony', 'Floors']         # Order of Layers 

# lightred = (.7, .4, .4)
# Colors = [lightred, 'lightgrey'   , 'lightbrown', 'lightgreen', 'lightblue', '#FFFFFF', '#FFFFFF']
Colors = ['#694b29', '#FFFFFF'   , '#787878', '#FFFFFF', '#357EC7', '#FFFFFF', '#FFFFFF']
Textures = [None, None, None, None, None, None, None]

# Colors = ['#694b29', None, None, None, '#357EC7', '#FFFFFF', '#FFFFFF']
# Textures = [None, Wall_Texture, Roof_Texture, Wall_Texture, None, Balcony_Texture, None]

# Colors = [None, None, None, None, None, None, None]
# Textures = [Door_Texture, Wall_Texture, Roof_Texture, Wall_Texture, Window_Texture, Balcony_Texture, Floor_Texture]

Opacities = [1., 1., 1., 1., 1., 1., 1.]
Texture_Scales = [2, 2, 2, 2, 2, 2, 2]

Mesh_Doors = pv.MultiBlock()
Mesh_Walls = pv.MultiBlock()
Mesh_Stairs = pv.MultiBlock()
Mesh_Windows = pv.MultiBlock() 
Mesh_Outline_window = pv.MultiBlock()
Mesh_Balcony = pv.MultiBlock()
Mesh_Floors = pv.MultiBlock()

##########################################################################################################

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


def update_layers(msp, translation_vector):
    
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
            # Mesh_Walls.append(lower_wall)
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
            
            outline_window = window.outline()
            Mesh_Outline_window.append(outline_window)
            
        elif 'roof' in entity.dxf.layer.lower() or 'سقف' in entity.dxf.layer or 'gable' in entity.dxf.layer or 'شیروانی' in entity.dxf.layer:
            # mesh = entity_to_mesh(entity)
            # TODO: Add roof extrudion by seperation of each roof id and then extruding it by extrude_as_gable()
            pass
        
    plan_lines.translate(translation_vector, inplace=True)        
    floor_surface = create_floor_surface(plan_lines)
    Mesh_Floors.append(floor_surface)
    

def shell_delaunay_2d(mesh):
    copy = mesh.copy()
    copy.points[:,1] = 0.0 # Smash shell down to a plane
    # Exagerate x and z
    copy.points[:,0] *= 10
    copy.points[:,2] *= 10
    tri = copy.delaunay_2d()
    # Put connectivity on plane to the original mesh
    return pv.PolyData(mesh.points, tri.faces)


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
    
    """
    Centers a PyVista mesh to [0, 0, 0] and rescales it to fit within a maximum boundary.
    """
    
    # If mesh is a MultiBlock, Convert into pv.PolyData()
    if isinstance(mesh, pv.MultiBlock):
        mesh = mesh.combine().extract_surface()

    mesh0 = mesh.copy()
    
    # Translate the mesh center to [0, 0, 0]
    mesh_centered = mesh0.translate(-np.array(center))

    # Rescale the mesh
    transformed_mesh = mesh_centered.scale([scale_factor, scale_factor, scale_factor], inplace=False)
    
    # Swap Y and Z axes
    # transformed_mesh.points = np.column_stack((transformed_mesh.points[:, 0],  # X
                                            #    transformed_mesh.points[:, 2],  # Z
                                            #    transformed_mesh.points[:, 1])) # Y
    
    transformed_mesh.points[:, [1, 2]] = transformed_mesh.points[:, [2, 1]]   #Alternatively use this line to swap Y and Z
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

##########################################################################################################

for i, msp in enumerate(MSP):

    Translation_Vector = [x_translate[i], y_translate[i], z_translate[i]]
    
    if i < len(MSP)-1:
        update_layers(msp, Translation_Vector)
        print(f'Floor {i+1} completed')
    else:
        Mesh_Roof = extrude_as_gable(msp, max_height=WallHeight, Translation_Vector=Translation_Vector)
        print('Roof completed')

All_mesh = pv.MultiBlock()
meshes = [Mesh_Doors, Mesh_Walls, Mesh_Roof, Mesh_Stairs, Mesh_Windows, Mesh_Balcony, Mesh_Floors]
for mesh in meshes:
    All_mesh.append(mesh)


plotter = pv.Plotter(notebook=False)
plotter.set_background('#282828')  # Set the background color here

center, scale_factor = get_ScaleFactor_and_Translation(All_mesh, max_boundary=100)

for i,mesh in enumerate(meshes):
    if mesh is not None and len(mesh) > 0:
        mesh = prepare_for_3DViewers(mesh, center=center, scale_factor=scale_factor)
        # mesh = TextureScale(mesh, Texture_Scales[i])
        plotter.add_mesh(mesh, color=Colors[i], texture=Textures[i], opacity=Opacities[i], line_width=2, point_size=0)

if Mesh_Outline_window is not None and len(Mesh_Outline_window) > 0:
    Mesh_Outline_window = prepare_for_3DViewers(Mesh_Outline_window, center=center, scale_factor=scale_factor)
    # plotter.add_mesh(Mesh_Outline_window, color='blue', line_width=4, point_size=0)

plotter.enable_depth_peeling()
plotter.export_obj('outputOBJ/output.obj')
plotter.add_axes()
plotter.show()
plotter.close()

convert_tr_to_d('outputOBJ/output.mtl')
