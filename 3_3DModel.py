import ezdxf
import numpy as np
import pyvista as pv
from dxf_to_pyvista import dxf_to_pyvista_line, dxf_to_pyvista_hatch, dxf_to_pyvista_polyline

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
Colors = [lightred, 'lightgrey'   ,'lightgrey', None, None]
Textures = [Door_Texture, Wall_Texture, Roof_Texture, Wall_Texture, Window_Texture]



def entity_to_mesh(plotter, msp, layers, colors, textures, translation_vector):
    
    # Create a dictionary to map each layer to its color
    layer_to_color = dict(zip(layers, colors))
    layer_to_texture = dict(zip(layers, textures))

    for entity in msp:

        layer_color = layer_to_color.get(entity.dxf.layer)
        layer_texture = layer_to_texture.get(entity.dxf.layer)

        if layer_texture:
            # Set transparency for the "window" layer
            opacity = 1 if entity.dxf.layer == "FP-Window" else 1.0
            height = WallHeight/2 if entity.dxf.layer == "FP-Stair" else WallHeight

            if entity.dxftype() == 'LINE':
                line = dxf_to_pyvista_line(entity)
                line.translate(translation_vector, inplace=True)
                mesh = line.extrude([0, 0, height], capping=False)
                mesh.point_data_to_cell_data()
                mesh.texture_map_to_plane(inplace=True)
                plotter.add_mesh(mesh, color=layer_color, line_width=2, opacity=opacity, texture=layer_texture)
            elif entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']:
                lines = dxf_to_pyvista_polyline(entity)
                for line in lines:
                    line.translate(translation_vector, inplace=True)
                    mesh = line.extrude([0, 0, height], capping=False)
                    mesh.point_data_to_cell_data()
                    mesh.texture_map_to_plane(inplace=True)
                    plotter.add_mesh(mesh, color=layer_color, line_width=2, opacity=opacity, texture=layer_texture)
            elif entity.dxftype() == 'HATCH':
                all_hatch = dxf_to_pyvista_hatch(entity)
                for hatch in all_hatch:
                    hatch.translate(translation_vector, inplace=True)
                    mesh = hatch.extrude([0, 0, height], capping=False)
                    mesh.point_data_to_cell_data()
                    mesh.texture_map_to_plane(inplace=True)
                    plotter.add_mesh(mesh, color=layer_color, line_width=2, point_size=.0001, opacity=opacity, texture=layer_texture)

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


def extrude_as_gable(msp, base_height, Translation_Vector):
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

    # Now, create a surface from all these lines.
    Points = all_lines.points
    roof_surface0 = all_lines.delaunay_2d()
    roof_ceiling = roof_surface0.copy()


    # Now, deform this 2D surface to shape it as a gable.
    for point in Points:
        # Adjust the base 
        point[2] += base_height

        # Calculate the gable deformation
        height_offset = np.tan(np.radians(20)) * ( -abs(point[0] - roof_surface0.center[0]))

        # Apply the gable deformation
        point[2] += height_offset


    cloud = pv.PolyData(all_lines)
    roof_surface1 = cloud.delaunay_3d().extract_geometry()

    roof_surface = roof_surface0 + roof_surface1
    # roof_surface = roof_surface0 + roof_surface1 + roof_ceiling
    # roof_surface = roof_ceiling

    roof_surface.point_data_to_cell_data()
    roof_surface.texture_map_to_plane(inplace=True)

    TextureScale(roof_surface,16)

    return roof_surface



plotter = pv.Plotter(notebook=False)

for i, msp in enumerate(MSP):

    Translation_Vector = [x_translate[i], y_translate[i], z_translate[i]]
    
    if i < len(MSP)-1:
        plotter = entity_to_mesh(plotter, msp, Layers, Colors, Textures, Translation_Vector)
    else:
        roof_surface = extrude_as_gable(msp, 10+WallHeight, Translation_Vector)
        plotter.add_mesh(roof_surface, texture=Roof_Texture)



# plotter.enable_depth_peeling(number_of_peels=50, occlusion_ratio=0)
camera = plotter.camera
camera.position = (11368.489169071205, 4093.2579511056797, 2239.165230214689)
camera.focal_point = (11332.366527666658, 4006.397461809341, 627.5624088506037)
camera.view_up = (0, 1, 0)
camera.clipping_range = (1790.0142033648085, 2825.4544759496184)
camera.view_angle = 30
camera.distance = 2859.9125435621586
camera.azimuth = -30        
camera.elevation = 0         
camera.roll =  0           

plotter.enable_depth_peeling()
plotter.show()
plotter.close()
