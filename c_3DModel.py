import ezdxf
import numpy as np
import pyvista as pv
from dxf_to_pyvista import dxf_to_pyvista_line, dxf_to_pyvista_hatch
from roof_utilities import extrude_as_gable

WallHeight = 200

x_translate = [0, 19, 0]
y_translate = [0, 1890, 5920]
z_translate = [0, WallHeight, 2*WallHeight]

doc1 = ezdxf.readfile("decomposed/plan_1.dxf")
doc2 = ezdxf.readfile("decomposed/plan_2.dxf")
doc3 = ezdxf.readfile("decomposed/plan_roof.dxf")

msp1 = doc1.modelspace()
msp2 = doc2.modelspace()
msp_roof = doc3.modelspace()
MSP = [msp1, msp2, msp_roof]


# Wall_Texture = pv.Texture('Red_brick_wall_texture.jpg')
Wall_Texture = pv.Texture('Textures/wall.jpg')
Window_Texture = pv.Texture('Textures/window2.jpg')
Door_Texture = pv.Texture('Textures/door.png')
Roof_Texture = pv.Texture('Textures/roof.jpg')
Stair_Texture = pv.Texture('Textures/stair.jpg')

Layers = ['FP-Door', 'FP-Proposed Wall', 'FP-Roof', 'FP-Stair', 'FP-Window']

# lightred = (.7, .4, .4)
# Colors = [lightred, 'lightgrey'   , 'lightbrown', 'lightgreen', 'lightblue']
Colors = ['#694b29', '#FFFFFF'   , '#787878', '#FFFFFF', '#357EC7']
Textures = [None, None, None, None, None]

# Colors = ['#694b29', None, None, None, '#357EC7']
# Textures = [None, Wall_Texture, Roof_Texture, Wall_Texture, None]

# Colors = [None, None, None, None, None]
# Textures = [Door_Texture, Wall_Texture, Roof_Texture, Wall_Texture, Window_Texture]

Opacities = [1., 1., 1., 1., 1.]
Texture_Scales = [2, 2, .3, 2, 4]

Mesh_Doors = pv.MultiBlock()
Mesh_Walls = pv.MultiBlock()
Mesh_Stairs = pv.MultiBlock()
Mesh_Windows = pv.MultiBlock() 
Mesh_Outline_window = pv.MultiBlock()

#######################################################################


def dxf_to_pyvista_polyline2(polyline):
    """Convert DXF POLYLINE or LWPOLYLINE to pyvista PolyData."""
    vertices = [vertex+(0,) for vertex in polyline.vertices()]
    if polyline.is_closed:
        vertices = vertices + [vertices[0]]
    polyline_data = pv.PolyData(vertices)
    polyline_data.lines = [len(vertices)] + list(range(len(vertices)))
    return polyline_data


def extract_window(mesh):
    bounds = mesh.bounds
    z_min, z_max = bounds[4], bounds[5]
    total_height = z_max - z_min
    h_window = total_height/2
    h_walls = (total_height - h_window)/2
    z1_window = z_min + h_walls
    z2_window = z_max - h_walls
    lower_wall = mesh.clip(normal=[0, 0, 1], origin=(0, 0, z1_window)) #Clip total mesh from z1_window upwards
    window = mesh.clip(normal=[0, 0, 1], origin=(0, 0, z2_window)) #Clip total mesh from z2_window upwards
    window = window.clip(normal=[0, 0, -1], origin=(0, 0, z1_window)) #Clip total mesh from z1_window downwards
    upper_wall = mesh.clip(normal=[0, 0, -1], origin=(0, 0, z2_window)) #Clip total mesh from z2_window downwards
    return lower_wall, window, upper_wall


def update_layers(mesh, Layer_name):
    if Layer_name == Layers[0]:
        Mesh_Doors.append(mesh)
    elif Layer_name == Layers[1]:
        Mesh_Walls.append(mesh)
    elif Layer_name == Layers[3]:
        Mesh_Stairs.append(mesh)
    elif Layer_name == Layers[4]:
        lower_wall, window, upper_wall = extract_window(mesh)        
        Mesh_Walls.append(lower_wall)
        Mesh_Windows.append(window)
        Mesh_Walls.append(upper_wall)
        
        outline_window = window.outline()
        Mesh_Outline_window.append(outline_window)

def entity_to_mesh(msp, translation_vector):
    
    for entity in msp:

        if entity.dxf.layer in Layers:
            # Set transparency for the "window" layer
            height = WallHeight/2 if entity.dxf.layer == "FP-Stair" else WallHeight

            if entity.dxftype() == 'LINE':
                line = dxf_to_pyvista_line(entity)
                line.translate(translation_vector, inplace=True)
                mesh = line.extrude([0, 0, height], capping=False)
                update_layers(mesh, entity.dxf.layer)
                
            elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
                polyline = dxf_to_pyvista_polyline2(entity)
                polyline.translate(translation_vector, inplace=True)
                mesh = polyline.extrude([0, 0, height], capping=False)
                update_layers(mesh, entity.dxf.layer)
                            
            elif entity.dxftype() == 'HATCH':
                all_hatch = dxf_to_pyvista_hatch(entity)
                for hatch in all_hatch:
                    hatch.translate(translation_vector, inplace=True)
                    mesh = hatch.extrude([0, 0, height], capping=False)
                    update_layers(mesh, entity.dxf.layer)



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

    if 'Texture Coordinates' in surface.point_data:
        # Get the texture coordinates
        tcoords = surface.point_data['Texture Coordinates']

        # Scale the texture coordinates to zoom out
        tcoords *= scale_factor

        # Set the adjusted texture coordinates back to the mesh
        surface.point_data['Texture Coordinates'] = tcoords
        return surface
    
    else:
        return surface0


def get_ScaleFactor_and_Translation(mesh, max_boundary=100):

    # If mesh is a MultiBlock, Convert into pv.PolyData()
    if isinstance(mesh, pv.MultiBlock):
        mesh = mesh.combine().extract_surface()
        
    center = mesh.center
    mesh_centered = mesh.translate(-np.array(center))
    # Calculate the scaling factor
    bounds = mesh_centered.bounds
    max_extent = max([bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]])
    scale_factor = max_boundary / max_extent
    return center, scale_factor


def prepare_for_3DViewers(mesh, center, scale_factor):
    """
    Centers a PyVista mesh to [0, 0, 0] and rescales it to fit within a maximum boundary.

    :param mesh: PyVista mesh to be transformed.
    :param max_boundary: Maximum size of the mesh's largest dimension after scaling.
    :return: Transformed PyVista mesh.
    """
    
    # If mesh is a MultiBlock, Convert into pv.PolyData()
    if isinstance(mesh, pv.MultiBlock):
        mesh = mesh.combine().extract_surface()
    
    # Translate the mesh center to [0, 0, 0]
    mesh_centered = mesh.translate(-np.array(center))

    # Rescale the mesh
    mesh_scaled = mesh_centered.scale([scale_factor, scale_factor, scale_factor], inplace=False)
    
    # Copy the mesh to avoid modifying the original
    transformed_mesh = mesh_scaled.copy()

    # Swap Y and Z axes
    # transformed_mesh.points = np.column_stack((transformed_mesh.points[:, 0],  # X
                                            #    transformed_mesh.points[:, 2],  # Z
                                            #    transformed_mesh.points[:, 1])) # Y
    
    transformed_mesh.points[:, [1, 2]] = transformed_mesh.points[:, [2, 1]]   #Alternatively use this line to swap Y and Z
    # transformed_mesh = transformed_mesh.triangulate()
    transformed_mesh.point_data_to_cell_data()
    transformed_mesh.texture_map_to_plane(inplace=True)
    transformed_mesh.compute_normals()

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

######################################################################################

for i, msp in enumerate(MSP):

    Translation_Vector = [x_translate[i], y_translate[i], z_translate[i]]
    
    if i < len(MSP)-1:
        entity_to_mesh(msp, Translation_Vector)
    else:
        Mesh_Roof = extrude_as_gable(msp, 280, Translation_Vector)


All_mesh = pv.MultiBlock()
meshes = [Mesh_Doors, Mesh_Walls, Mesh_Roof, Mesh_Stairs, Mesh_Windows]
for mesh in meshes:
    All_mesh.append(mesh)


plotter = pv.Plotter(notebook=False)
plotter.set_background('#282828')  # Set the background color here

center, scale_factor = get_ScaleFactor_and_Translation(All_mesh, max_boundary=100)

for i,mesh in enumerate(meshes):
    mesh = prepare_for_3DViewers(mesh, center=center, scale_factor=scale_factor)
    mesh = TextureScale(mesh, Texture_Scales[i])
    plotter.add_mesh(mesh, color=Colors[i], texture=Textures[i], opacity=Opacities[i], line_width=0, point_size=0)

Mesh_Outline_window = prepare_for_3DViewers(Mesh_Outline_window, center=center, scale_factor=scale_factor)
# plotter.add_mesh(Mesh_Outline_window, color='blue', line_width=4, point_size=0)

plotter.enable_depth_peeling()
plotter.export_obj('outputOBJ/output.obj')
plotter.add_axes()
plotter.show()
plotter.close()


convert_tr_to_d('outputOBJ/output.mtl')
