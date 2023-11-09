import ezdxf
import numpy as np
import pyvista as pv
import vtkmodules.all as vtk
from dxf_to_pyvista import dxf_to_pyvista_line, dxf_to_pyvista_hatch, dxf_to_pyvista_polyline
from pyvista import wrap
from concave_hull import concave_hull, concave_hull_indexes
from roof_utilities import create_PolyData_Line, interpolate_AllLines, get_outline, sort_points_by_distance
from roof_utilities import produce_gable_height, find_corner_points, produce_2Dsurface

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

lightred = (.7, .4, .4)
Layers = ['FP-Door', 'FP-Proposed Wall', 'FP-Roof', 'FP-Stair', 'FP-Window']
# Colors = [lightred, 'lightgrey'   , 'lightbrown', 'lightgreen', 'lightblue']
Colors = ['#694b29', '#FFFFFF'   , '#454545', '#FFFFFF', '#357EC7']
# Textures = [Door_Texture, Wall_Texture, Roof_Texture, Wall_Texture, Window_Texture]
Textures = [None, None, None, None, None]


def dxf_to_pyvista_polyline2(polyline):
    """Convert DXF POLYLINE or LWPOLYLINE to pyvista PolyData."""
    vertices = [vertex+(0,) for vertex in polyline.vertices()]
    if polyline.is_closed:
        vertices = vertices + [vertices[0]]
    polyline_data = pv.PolyData(vertices)
    polyline_data.lines = [len(vertices)] + list(range(len(vertices)))
    return polyline_data


def entity_to_mesh(plotter, msp, layers, colors, textures, translation_vector):
    
    # Create a dictionary to map each layer to its color
    layer_to_color = dict(zip(layers, colors))
    # layer_to_texture = dict(zip(layers, textures))

    for entity in msp:

        layer_color = layer_to_color.get(entity.dxf.layer)
        # layer_texture = layer_to_texture.get(entity.dxf.layer)

        if layer_color:
            # Set transparency for the "window" layer
            opacity = 1 if entity.dxf.layer == "FP-Window" else 1.0
            height = WallHeight/2 if entity.dxf.layer == "FP-Stair" else WallHeight

            if entity.dxftype() == 'LINE':
                line = dxf_to_pyvista_line(entity)
                line.translate(translation_vector, inplace=True)
                mesh = line.extrude([0, 0, height], capping=False)
                mesh.point_data_to_cell_data()
                mesh.texture_map_to_plane(inplace=True)
                plotter.add_mesh(mesh, color=layer_color, line_width=2, opacity=opacity)
            elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
                polyline = dxf_to_pyvista_polyline2(entity)
                polyline.translate(translation_vector, inplace=True)
                mesh = polyline.extrude([0, 0, height], capping=False)
                mesh.point_data_to_cell_data()
                mesh.texture_map_to_plane(inplace=True)
                plotter.add_mesh(mesh, color=layer_color, line_width=2, point_size=.0001, opacity=opacity)
                
            elif entity.dxftype() == 'HATCH':
                all_hatch = dxf_to_pyvista_hatch(entity)
                for hatch in all_hatch:
                    hatch.translate(translation_vector, inplace=True)
                    mesh = hatch.extrude([0, 0, height], capping=False)
                    mesh.point_data_to_cell_data()
                    mesh.texture_map_to_plane(inplace=True)
                    plotter.add_mesh(mesh, color=layer_color, line_width=2, point_size=.0001, opacity=opacity)

    return plotter



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

    if 'Texture Coordinates' in surface.point_data:
        # Get the texture coordinates
        tcoords = surface.point_data['Texture Coordinates']

        # Scale the texture coordinates to zoom out
        tcoords *= scale_factor

        # Set the adjusted texture coordinates back to the mesh
        surface.point_data['Texture Coordinates'] = tcoords
    else:
        print("The mesh does not have texture coordinates!")


def extrude_as_gable(msp, Base_H, Translation_Vector):
    #Plotting the roof:  First, join all lines from the 'FP-Roof' layer into a single PolyData
    all_lines = None

    for entity in msp:
        if entity.dxftype() == 'LINE' and entity.dxf.layer == 'FP-Roof':
            line = dxf_to_pyvista_line(entity)
            line.translate(Translation_Vector, inplace=True)

            if all_lines is None:
                all_lines = line
            else:
                all_lines += line

        elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE'] and entity.dxf.layer == 'FP-Roof':
            lines = dxf_to_pyvista_polyline(entity)
            for line in lines:
                line.translate(Translation_Vector, inplace=True)
                if all_lines is None:
                    all_lines = line
                else:
                    all_lines += line


    ##################################################################

    densified_points = interpolate_AllLines(all_lines,21)
    outline_points = get_outline(densified_points)
    outline_points = np.array(outline_points)
    outline_points = np.unique(outline_points, axis=0)
    outline_points = sort_points_by_distance(outline_points)
    outline_points3D = produce_gable_height(outline_points, base_height=Base_H)

    ###################################################################
    # Find the indices of the two points with the maximum z-values and Sort
    max_z_indices = np.argsort(-outline_points3D[:, 2])[:2]
    max_z_indices = np.sort(max_z_indices)[::-1]

    outline_points3D = np.roll(outline_points3D, -max_z_indices[0], axis=0)
    outline_points = np.roll(outline_points, -max_z_indices[0], axis=0)

    max_z_indices = np.argsort(-outline_points3D[:, 2])[:2]
    max_z_indices = np.sort(max_z_indices)[::-1]

    # Split the list of points into two parts
    outline_points3D_1 = outline_points3D[:max_z_indices[0] + 1]
    outline_points3D_2 = outline_points3D[max_z_indices[0] + 1:]

    #####################################################################
    outline_lines = create_PolyData_Line(outline_points)
    outline_lines3D = create_PolyData_Line(outline_points3D)
    outline_lines3D_1 = create_PolyData_Line(outline_points3D_1)
    outline_lines3D_2 = create_PolyData_Line(outline_points3D_2)


    # Creating Outline Lines with corner_points instead of all outline_points
    corner_points = find_corner_points(outline_points, angle_threshold=10)  # Threshold angle in degrees
    corner_points3D = produce_gable_height(corner_points, base_height=Base_H)

    corner_lines = create_PolyData_Line(corner_points)
    corner_lines3D = create_PolyData_Line(corner_points3D)

    ##################################################################
    surface2D = produce_2Dsurface(outline_lines)

    surface3D_1 = produce_2Dsurface(outline_lines3D_1)
    surface3D_2 = produce_2Dsurface(outline_lines3D_2)

    points = np.array([outline_points3D[max_z_indices[0]], outline_points3D[max_z_indices[0]+1], 
                    outline_points3D[max_z_indices[1]-1], outline_points3D[max_z_indices[1]]])

    faces = np.hstack([[4], np.arange(4)])  # 4 points, followed by the indices 0, 1, 2, 3
    surface3D_3 = pv.PolyData(points, faces)

    surface3D = surface3D_1 + surface3D_2 + surface3D_3

    ##################################################################
    # plotting side surfaces of the gable

    side_surface = pv.MultiBlock()

    for i in range(len(outline_points) - 1):
        p1, p2, p3, p4 = outline_points[i], outline_points[i + 1], outline_points3D[i + 1], outline_points3D[i]
        points = np.array((p1, p2, p3, p4)).astype(np.float32)  # Explicitly cast to float32
        faces = np.hstack([[4], np.arange(4)])  # 4 points, followed by the indices 0, 1, 2, 3
        plane = pv.PolyData(points, faces)
        side_surface.append(plane)


    #plotting the last plane:
    p1, p2, p3, p4 = outline_points[-1], outline_points[0], outline_points3D[0], outline_points3D[-1]
    points = np.array((p1, p2, p3, p4)).astype(np.float32)  # Explicitly cast to float32
    faces = np.hstack([[4], np.arange(4)])  # 4 points, followed by the indices 0, 1, 2, 3
    plane = pv.PolyData(points, faces)
    side_surface.append(plane)

    Gable = surface2D + surface3D + side_surface

    return Gable



plotter = pv.Plotter(notebook=False)
plotter.set_background('#282828')  # Set the background color here

for i, msp in enumerate(MSP):

    Translation_Vector = [x_translate[i], y_translate[i], z_translate[i]]
    
    if i < len(MSP)-1:
        plotter = entity_to_mesh(plotter, msp, Layers, Colors, Textures, Translation_Vector)
    else:
        roof_surface = extrude_as_gable(msp, 280, Translation_Vector)
        plotter.add_mesh(roof_surface, color=Colors[2])

        

# plotter.enable_depth_peeling()

plotter.export_obj('outputOBJ/output.obj')  
plotter.show()
plotter.close()
