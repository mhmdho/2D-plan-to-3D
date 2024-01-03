import os
import ezdxf
import numpy as np
import pyvista as pv
from roof_utilities import extrude_as_gable
from mesh_utilities import update_layers, get_ScaleFactor_and_Translation, prepare_for_3DViewers, convert_tr_to_d
from mesh_utilities import Mesh_Doors, Mesh_Walls, Mesh_Roof, Mesh_Stairs, Mesh_Windows, Mesh_Outline_window, Mesh_Balcony, Mesh_Floors


folder_path = "decomposed"                     # Path to the decomposed folder
WallHeight = 155                               # Height of each floor

Wall_Texture = pv.Texture('Textures/wall.jpg')
Window_Texture = pv.Texture('Textures/window2.jpg')
Door_Texture = pv.Texture('Textures/door.png')
Roof_Texture = pv.Texture('Textures/roof.jpg')
Stair_Texture = pv.Texture('Textures/stair.jpg')
Balcony_Texture = pv.Texture('Textures/wall.jpg')
Floor_Texture = pv.Texture('Textures/stair.jpg')

Layers = ['Door',    'Wall',    'Roof',    'Stair',   'Window',  'Balcony', 'Floors']                  # Order of Layers 
Colors = ['#694b29', '#FFFFFF', '#787878', '#FFFFFF', '#357EC7', '#FFFFFF', '#FFFFFF']
Textures = [None, None, None, None, None, None, None]
Opacities = [1., 1., 1., 1., 1., 1., 1.]
Texture_Scales = [2, 2, 2, 2, 2, 2, 2]

# lightred = (.7, .4, .4)
# Colors = [lightred, 'lightgrey'   , 'lightbrown', 'lightgreen', 'lightblue', '#FFFFFF', '#FFFFFF']
# Colors = ['#694b29', None, None, None, '#357EC7', '#FFFFFF', '#FFFFFF']
# Textures = [None, Wall_Texture, Roof_Texture, Wall_Texture, None, Balcony_Texture, None]
# Colors = [None, None, None, None, None, None, None]
# Textures = [Door_Texture, Wall_Texture, Roof_Texture, Wall_Texture, Window_Texture, Balcony_Texture, Floor_Texture]

##########################################################################################################

plan_files = [file for file in os.listdir(folder_path) if file.endswith('.dxf') and file.startswith('plan')]  # List all plan files in the folder
plan_files.sort(reverse=False)
N = len(plan_files)                    # Number of total plan files (floors + roof)

x_translate = np.zeros(N)
y_translate = np.zeros(N)
z_translate = [n * WallHeight for n in range(N)]

for i, plan in enumerate(plan_files):
    
    doc = ezdxf.readfile(os.path.join(folder_path, plan))
    msp = doc.modelspace()
    Translation_Vector = [x_translate[i], y_translate[i], z_translate[i]]
    
    if i < N-1:
        update_layers(msp, Translation_Vector, WallHeight)        
        print(f'Floor {i+1} completed')
        
    else:
        top_Roof = extrude_as_gable(msp, max_height=WallHeight, Translation_Vector=Translation_Vector)
        Mesh_Roof.append(top_Roof)
        print('Roof completed')

All_mesh = pv.MultiBlock()
meshes = [Mesh_Doors, Mesh_Walls, Mesh_Roof, Mesh_Stairs, Mesh_Windows, Mesh_Balcony, Mesh_Floors]
for mesh in meshes:
    All_mesh.append(mesh)
    
##########################################################################################################

plotter = pv.Plotter(notebook=False)
plotter.set_background('#282828')  # Set the background color here

center, scale_factor = get_ScaleFactor_and_Translation(All_mesh, max_boundary=100)

for i,mesh in enumerate(meshes):
    if mesh is not None and len(mesh) > 0:
        mesh = prepare_for_3DViewers(mesh, center=center, scale_factor=scale_factor)
        # mesh = TextureScale(mesh, Texture_Scales[i])
        plotter.add_mesh(mesh, color=Colors[i], texture=Textures[i], opacity=Opacities[i], line_width=2, point_size=0)

# if Mesh_Outline_window is not None and len(Mesh_Outline_window) > 0:
#     Mesh_Outline_window = prepare_for_3DViewers(Mesh_Outline_window, center=center, scale_factor=scale_factor)
#     plotter.add_mesh(Mesh_Outline_window, color='blue', line_width=4, point_size=0)

plotter.enable_depth_peeling()
plotter.export_obj('outputOBJ/output.obj')
plotter.add_axes()
plotter.show()
plotter.close()

convert_tr_to_d('outputOBJ/output.mtl')
